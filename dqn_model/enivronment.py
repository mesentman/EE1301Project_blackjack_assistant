import random
from collections import deque
import numpy as np
from config import COUNT_BINS, NUM_ACTIONS, NUM_DECKS, DEVICE, MAX_STEPS
import torch

# ---------------- SHOE & COUNT ----------------
def make_shoe(num_decks=NUM_DECKS):
    shoe = []
    for _ in range(num_decks):
        for r in range(1, 14):
            shoe.extend([min(r, 10)] * 4)
    random.shuffle(shoe)     
    return deque(shoe)

def shoe_draw(shoe):
    return shoe.popleft()

def update_count(card, running):
    if 2 <= card <= 6:
        return running + 1
    elif 7 <= card <= 9:
        return running
    else:
        return running - 1

def true_count_bin_from_running(running_count, cards_remaining):
    decks_left = max(cards_remaining / 52.0, 0.25)
    tc = running_count / decks_left
    tc_rounded = int(round(tc))
    tc_rounded = max(min(tc_rounded, COUNT_BINS[-1]), COUNT_BINS[0])
    return tc_rounded + abs(COUNT_BINS[0])

# ---------------- HAND HELPERS ----------------
def hand_total(cards):
    total = sum(cards)
    aces = cards.count(1)
    while total > 21 and aces:
        total -= 10
        aces -= 1
    usable_ace = 1 in cards and sum(cards) + 10 <= 21
    return total, usable_ace

def encode_state_vec(cards, dealer_up, tc_idx):
    total, usable = hand_total(cards)
    total_clamped = min(max(total, 4), 21)
    hand_size = min(len(cards), 5) / 5.0
    num_aces = cards.count(1) / 4.0
    return np.array([
        (total_clamped - 4) / (21 - 4),
        1.0 if usable else 0.0,
        (dealer_up - 1) / 9.0,
        tc_idx / (len(COUNT_BINS) - 1),
        hand_size,
        num_aces
    ], dtype=np.float32)

# ---------------- FIXED PLAYER STRATEGIES ----------------
def aggressive(player_hand, dealer_up, shoe, running_count):
    total, _ = hand_total(player_hand)
    while total < 17:
        c = shoe_draw(shoe)
        player_hand.append(c)
        running_count = update_count(c, running_count)
        total, _ = hand_total(player_hand)
    return player_hand, running_count

def passive(player_hand, dealer_up, shoe, running_count):
    total, _ = hand_total(player_hand)
    while total < 12:
        c = shoe_draw(shoe)
        player_hand.append(c)
        running_count = update_count(c, running_count)
        total, _ = hand_total(player_hand)
    return player_hand, running_count

def basic_strategy(player_hand, dealer_up, shoe, running_count):
    total, usable = hand_total(player_hand)
    while True:
        if usable and total >= 18: break
        if not usable and total >= 17: break
        c = shoe_draw(shoe)
        player_hand.append(c)
        running_count = update_count(c, running_count)
        total, usable = hand_total(player_hand)
    return player_hand, running_count

PLAYER_TYPES = [aggressive, passive, basic_strategy]

def play_fixed_player(player_hand, dealer_up, shoe, running_count, strategy_fn):
    final_hand, running_count = strategy_fn(player_hand, dealer_up, shoe, running_count)
    dealer_hand = [dealer_up, shoe_draw(shoe)]
    dealer_total, _ = hand_total(dealer_hand)
    while dealer_total < 17:
        c = shoe_draw(shoe)
        dealer_hand.append(c)
        running_count = update_count(c, running_count)
        dealer_total, _ = hand_total(dealer_hand)
    player_total, _ = hand_total(final_hand)
    if player_total > 21: return -1.0, running_count
    if dealer_total > 21 or player_total > dealer_total: return 1.0, running_count
    if player_total < dealer_total: return -1.0, running_count
    return 0.0, running_count

# ---------------- DQN SPLIT HAND ----------------
def _simulate_split_hand_dqn(hand, dealer_hand, shoe, running_count,
                             policy_net, tc_idx, device, replay,
                             step_counter=0, max_splits=1, reward_scale=1.0,
                             shaping_coeff=0.0, max_steps=MAX_STEPS):
    if step_counter >= max_steps:
        return -1.0, running_count, step_counter

    # Cannot split further
    if max_splits == 0 or len(hand) != 2 or hand[0] != hand[1]:
        reward, running_count, step_counter = play_single_hand_dqn(
            policy_net, shoe, running_count, dealer_hand, hand, tc_idx,
            device, replay, reward_scale, shaping_coeff, step_counter, max_steps
        )
        return reward, running_count, step_counter

    # Draw cards for split hands
    c1, c2 = shoe_draw(shoe), shoe_draw(shoe)
    running_count = update_count(c1, running_count)
    running_count = update_count(c2, running_count)

    # Left hand
    r1, running_count, step_counter = _simulate_split_hand_dqn(
        [hand[0], c1], dealer_hand.copy(), shoe, running_count,
        policy_net, tc_idx, device, replay,
        step_counter, max_splits-1, reward_scale, shaping_coeff, max_steps
    )

    # Right hand
    r2, running_count, step_counter = _simulate_split_hand_dqn(
        [hand[1], c2], dealer_hand.copy(), shoe, running_count,
        policy_net, tc_idx, device, replay,
        step_counter, max_splits-1, reward_scale, shaping_coeff, max_steps
    )

    return (r1 + r2) / 2.0, running_count, step_counter

# ---------------- ENVIRONMENT STEP ----------------
def step_blackjack_env(shoe, player_hand, dealer_hand, action, running_count,
                       policy_net=None, tc_idx=None, device=None, replay=None,
                       step_counter=0, max_steps=MAX_STEPS):
    player_hand = player_hand.copy()
    dealer_hand = dealer_hand.copy()
    reward, done, double_mult = 0.0, False, 1

    # Natural blackjack
    player_bj = len(player_hand) == 2 and sorted(player_hand) == [1, 10]
    dealer_bj = len(dealer_hand) == 2 and sorted(dealer_hand) == [1, 10]
    if player_bj or dealer_bj:
        if player_bj and not dealer_bj: reward = 1.5
        elif dealer_bj and not player_bj: reward = -1.0
        else: reward = 0.0
        done = True
        return player_hand, dealer_hand, reward, done, running_count, step_counter

    # SPLIT
    if action == 3 and len(player_hand) == 2 and player_hand[0] == player_hand[1]:
        reward, running_count, step_counter = _simulate_split_hand_dqn(
            player_hand, dealer_hand, shoe, running_count,
            policy_net, tc_idx, device, replay,
            step_counter=step_counter, max_splits=1
        )
        done = True
        return player_hand, dealer_hand, reward, done, running_count, step_counter

    # SURRENDER
    if action == 4:
        reward = -0.5
        done = True
        return player_hand, dealer_hand, reward, done, running_count, step_counter

    # DOUBLE
    if action == 2:
        double_mult = 2
        step_counter += 1
        if step_counter > max_steps: return player_hand, dealer_hand, -1.0, True, running_count, step_counter
        c = shoe_draw(shoe)
        player_hand.append(c)
        running_count = update_count(c, running_count)

        # Dealer plays
        dealer_total, _ = hand_total(dealer_hand)
        while dealer_total < 17:
            step_counter += 1
            if step_counter > max_steps: return player_hand, dealer_hand, -1.0 * double_mult, True, running_count, step_counter
            c = shoe_draw(shoe)
            dealer_hand.append(c)
            running_count = update_count(c, running_count)
            dealer_total, _ = hand_total(dealer_hand)

        player_total, _ = hand_total(player_hand)
        if player_total > 21: reward = -1.0 * double_mult
        elif dealer_total > 21 or player_total > dealer_total: reward = 1.0 * double_mult
        elif player_total < dealer_total: reward = -1.0 * double_mult
        else: reward = 0.0
        done = True
        return player_hand, dealer_hand, reward, done, running_count, step_counter

    # HIT
    if action == 0:
        step_counter += 1
        if step_counter > max_steps: return player_hand, dealer_hand, -1.0, True, running_count, step_counter
        c = shoe_draw(shoe)
        player_hand.append(c)
        running_count = update_count(c, running_count)

        total, _ = hand_total(player_hand)
        if total > 21:
            reward = -1.0
            done = True
            return player_hand, dealer_hand, reward, done, running_count, step_counter
        done = False
        reward = 0.0
        return player_hand, dealer_hand, reward, done, running_count, step_counter

    # STAND
    if action == 1:
        dealer_total, _ = hand_total(dealer_hand)
        while dealer_total < 17:
            step_counter += 1
            if step_counter > max_steps: return player_hand, dealer_hand, -1.0, True, running_count, step_counter
            c = shoe_draw(shoe)
            dealer_hand.append(c)
            running_count = update_count(c, running_count)
            dealer_total, _ = hand_total(dealer_hand)

        player_total, _ = hand_total(player_hand)
        if player_total > 21: reward = -1.0
        elif dealer_total > 21 or player_total > dealer_total: reward = 1.0
        elif player_total < dealer_total: reward = -1.0
        else: reward = 0.0
        done = True
        return player_hand, dealer_hand, reward, done, running_count, step_counter

    return player_hand, dealer_hand, reward, done, running_count, step_counter

# ---------------- PLAY SINGLE HAND (DQN) ----------------
def play_single_hand_dqn(policy_net, shoe, running_count, dealer_hand,
                         player_hand, tc_idx, device, replay,
                         reward_scale=1.0, shaping_coeff=0.0,
                         step_counter=0, max_steps=MAX_STEPS, use_basic_strategy=False):
    
    if use_basic_strategy:
        # Encode current state
        state_vec = encode_state_vec(player_hand, dealer_hand[0], tc_idx)

        # Play using basic strategy
        reward, running_count = play_fixed_player(
            player_hand, dealer_hand[0], shoe, running_count,
            basic_strategy
        )

        # Push a dummy transition to the replay buffer
        if replay:
            next_state = np.zeros_like(state_vec, dtype=np.float32)
            replay.push(
                state_vec,      # current state
                -1,             # dummy action
                reward * reward_scale,
                next_state,
                True            # done
            )

        return reward * reward_scale, running_count, step_counter

    # ---- Regular DQN gameplay ----
    done = False
    total_reward = 0.0
    state = encode_state_vec(player_hand, dealer_hand[0], tc_idx)

    while not done:
        if step_counter >= max_steps:
            done = True
            next_state = np.zeros_like(state, dtype=np.float32)
            if replay:
                replay.push(state, -1, -1.0 * reward_scale, next_state, True)
            break

        # Select action
        with torch.no_grad():
            s = torch.tensor(state, dtype=torch.float32, device=device).unsqueeze(0)
            if not torch.isfinite(s).all(): 
                s = torch.zeros_like(s)
            if s.ndim == 1:
                s = s.unsqueeze(0)
            s = s.to(next(policy_net.parameters()).device)
            qvals = policy_net(s)
            if qvals is None or qvals.numel() == 0 or not torch.isfinite(qvals).all():
                action = np.random.randint(NUM_ACTIONS)
            else:
                action = int(qvals.argmax().item())
                action = min(action, NUM_ACTIONS - 1)

        # Step environment
        next_hand, dealer_hand_new, reward, done, running_count, step_counter = step_blackjack_env(
            shoe, player_hand, dealer_hand, action, running_count,
            policy_net, tc_idx, device, replay,
            step_counter=step_counter, max_steps=max_steps
        )

        if not done and shaping_coeff != 0.0:
            total, _ = hand_total(next_hand)
            reward += shaping_coeff * (total / 21.0)

        next_tc_idx = true_count_bin_from_running(running_count, len(shoe)) if not done else 0
        next_state = encode_state_vec(next_hand, dealer_hand_new[0], next_tc_idx) if not done else np.zeros_like(state, dtype=np.float32)

        if replay:
            replay.push(state, action, float(reward) * reward_scale, next_state, done)

        total_reward += float(reward) * reward_scale
        state, player_hand, dealer_hand = next_state, next_hand, dealer_hand_new

    return total_reward, running_count, step_counter
