import random
from collections import deque
import numpy as np
import torch
from config import COUNT_BINS, NUM_ACTIONS, NUM_DECKS, DEVICE

# ============================================================
# 🃏 SHOE & COUNT LOGIC
# ============================================================
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

# ============================================================
# ♠️ HAND HELPERS
# ============================================================
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

# ---------------- Fixed Player Strategies ----------------
def aggressive(player_hand, dealer_up, shoe, running_count):
    total, _ = hand_total(player_hand)
    while total < 17:
        card = shoe_draw(shoe)
        player_hand.append(card)
        running_count = update_count(card, running_count)
        total, _ = hand_total(player_hand)
    return player_hand, running_count

def passive(player_hand, dealer_up, shoe, running_count):
    total, _ = hand_total(player_hand)
    while total < 12:
        card = shoe_draw(shoe)
        player_hand.append(card)
        running_count = update_count(card, running_count)
        total, _ = hand_total(player_hand)
    return player_hand, running_count

def basic_strategy(player_hand, dealer_up, shoe, running_count):
    total, usable = hand_total(player_hand)
    while True:
        if usable and total >= 18:
            break
        if not usable and total >= 17:
            break
        card = shoe_draw(shoe)
        player_hand.append(card)
        running_count = update_count(card, running_count)
        total, usable = hand_total(player_hand)
    return player_hand, running_count

PLAYER_TYPES = [aggressive, passive, basic_strategy]

# ---------------- Fixed Player Simulation ----------------
def play_fixed_player(player_hand, dealer_up, shoe, running_count, strategy_fn):
    final_hand, updated_count = strategy_fn(player_hand, dealer_up, shoe, running_count)

    # Dealer plays normally
    dealer_hand = [dealer_up, shoe_draw(shoe)]
    dealer_total, _ = hand_total(dealer_hand)
    while dealer_total < 17:
        card = shoe_draw(shoe)
        dealer_hand.append(card)
        updated_count = update_count(card, updated_count)
        dealer_total, _ = hand_total(dealer_hand)

    # Determine reward
    player_total, _ = hand_total(final_hand)
    if player_total > 21:
        reward = -1.0
    elif dealer_total > 21 or player_total > dealer_total:
        reward = 1.0
    elif player_total < dealer_total:
        reward = -1.0
    else:
        reward = 0.0

    return reward, updated_count

# ============================================================
# ⚙️ ENVIRONMENT STEP
# ============================================================
def step_blackjack_env(shoe, player_hand, dealer_hand, action, running_count):
    player_hand = player_hand.copy()
    dealer_hand = dealer_hand.copy()
    reward = 0.0
    done = False
    double_mult = 1

    # Natural blackjack
    player_bj = len(player_hand) == 2 and sorted(player_hand) == [1, 10]
    dealer_bj = len(dealer_hand) == 2 and sorted(dealer_hand) == [1, 10]
    if player_bj or dealer_bj:
        if player_bj and not dealer_bj:
            reward = 1.5
        elif dealer_bj and not player_bj:
            reward = -1.0
        else:
            reward = 0.0
        return player_hand, dealer_hand, reward, True, running_count

    # SPLIT
    if action == 3 and len(player_hand) == 2 and player_hand[0] == player_hand[1]:
        reward, running_count = _simulate_split_hand(player_hand, dealer_hand, shoe, running_count)
        done = True
        return player_hand, dealer_hand, reward, done, running_count

    # DOUBLE
    if action == 2:
        double_mult = 2
        c = shoe_draw(shoe)
        player_hand.append(c)
        running_count = update_count(c, running_count)

    # HIT
    if action == 0:
        c = shoe_draw(shoe)
        player_hand.append(c)
        running_count = update_count(c, running_count)
        total, _ = hand_total(player_hand)
        if total > 21:
            reward = -1.0
            done = True
        return player_hand, dealer_hand, reward, done, running_count

    # STAND / DOUBLE resolution
    if action in [1, 2]:
        player_total, _ = hand_total(player_hand)
        dealer_total, _ = hand_total(dealer_hand)
        while dealer_total < 17:
            c = shoe_draw(shoe)
            dealer_hand.append(c)
            running_count = update_count(c, running_count)
            dealer_total, _ = hand_total(dealer_hand)

        if player_total > 21:
            reward = -1.0 * double_mult
        elif dealer_total > 21 or player_total > dealer_total:
            reward = 1.0 * double_mult
        elif player_total < dealer_total:
            reward = -1.0 * double_mult
        else:
            reward = 0.0
        done = True
        return player_hand, dealer_hand, reward, done, running_count

    # SURRENDER
    if action == 4:
        reward = -0.5
        done = True
        return player_hand, dealer_hand, reward, done, running_count

    return player_hand, dealer_hand, reward, done, running_count

# ============================================================
# 🔄 SPLIT HAND SIMULATION
# ============================================================
def _simulate_split_hand(hand, dealer_hand, shoe, running_count, max_splits=1):
    if max_splits > 0 and len(hand) == 2 and hand[0] == hand[1]:
        c1, c2 = shoe_draw(shoe), shoe_draw(shoe)
        running_count = update_count(c1, running_count)
        running_count = update_count(c2, running_count)
        r1, running_count = _simulate_split_hand([hand[0], c1], dealer_hand, shoe, running_count, max_splits-1)
        r2, running_count = _simulate_split_hand([hand[1], c2], dealer_hand, shoe, running_count, max_splits-1)
        return (r1 + r2) / 2.0, running_count

    done = False
    while not done:
        total, _ = hand_total(hand)
        if total >= 17: break
        c = shoe_draw(shoe)
        hand.append(c)
        running_count = update_count(c, running_count)
        if hand_total(hand)[0] > 21: break

    dealer_total, _ = hand_total(dealer_hand)
    while dealer_total < 17:
        c = shoe_draw(shoe)
        dealer_hand.append(c)
        running_count = update_count(c, running_count)
        dealer_total, _ = hand_total(dealer_hand)

    player_total, _ = hand_total(hand)
    if player_total > 21:
        reward = -1.0
    elif dealer_total > 21 or player_total > dealer_total:
        reward = 1.0
    elif player_total < dealer_total:
        reward = -1.0
    else:
        reward = 0.0

    return reward, running_count

# ============================================================
# 🎯 PLAY SINGLE HAND (DQN EPISODE) — NO EPSILON
# ============================================================
def play_single_hand_dqn(policy_net, shoe, running_count, dealer_hand,
                         player_hand, tc_idx, device, replay,
                         reward_scale=1.0, shaping_coeff=0.0):
    done = False
    total_reward = 0.0
    state = encode_state_vec(player_hand, dealer_hand[0], tc_idx)

    while not done:
        # Always greedy for NoisyDuelingMLP
        with torch.no_grad():
            s = torch.tensor(state, dtype=torch.float32, device=device).unsqueeze(0)
            action = int(policy_net(s).argmax().item())

        next_hand, dealer_hand_new, reward, done, running_count = step_blackjack_env(
            shoe, player_hand, dealer_hand, action, running_count
        )

        # Optional shaping
        if (not done) and shaping_coeff != 0.0:
            player_total, _ = hand_total(next_hand if not isinstance(next_hand[0], list) else next_hand[0])
            shaping = shaping_coeff * (player_total / 21.0)
            reward += shaping

        # Next-state encoding
        if not done:
            next_tc_idx = true_count_bin_from_running(running_count, len(shoe))
            if isinstance(next_hand, list) and len(next_hand) and isinstance(next_hand[0], list):
                next_state = encode_state_vec(next_hand[0], dealer_hand_new[0], next_tc_idx)
            else:
                next_state = encode_state_vec(next_hand, dealer_hand_new[0], next_tc_idx)
        else:
            next_state = np.zeros_like(state, dtype=np.float32)

        scaled_reward = float(reward) * float(reward_scale)
        if replay is not None:
            replay.push(state, action, scaled_reward, next_state, done)

        total_reward += scaled_reward
        state = next_state
        player_hand = next_hand
        dealer_hand = dealer_hand_new

    return total_reward, running_count
