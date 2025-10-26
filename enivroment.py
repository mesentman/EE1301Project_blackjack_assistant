import random
from collections import deque
import numpy as np
import torch
from config import COUNT_BINS, NUM_ACTIONS, NUM_DECKS, MAX_STEPS_PER_EP, DEVICE

# ============================================================
# 🃏 SHOE & COUNT LOGIC
# ============================================================
def make_shoe(num_decks=NUM_DECKS):
    """Create a shuffled blackjack shoe with given deck count."""
    shoe = []
    for _ in range(num_decks):
        for r in range(1, 14):  # ranks 1-13
            shoe.extend([min(r, 10)] * 4)  # face cards = 10
    random.shuffle(shoe)
    return deque(shoe)

def shoe_draw(shoe):
    """Draw a card from the shoe."""
    return shoe.popleft()

def hi_lo_value(card):
    """Return Hi-Lo count adjustment for given card."""
    if 2 <= card <= 6:
        return 1
    if 7 <= card <= 9:
        return 0
    return -1

def true_count_bin_from_running(running_count, cards_remaining):
    """Convert running count into a binned true count index."""
    decks_left = max(cards_remaining / 52.0, 0.25)
    tc = running_count / decks_left
    tc_rounded = int(round(tc))
    tc_rounded = max(min(tc_rounded, COUNT_BINS[-1]), COUNT_BINS[0])
    return tc_rounded + abs(COUNT_BINS[0])

# ============================================================
# ♠️ HAND HELPERS
# ============================================================
def hand_value(cards):
    """Return (total, usable_ace_flag)."""
    total = sum(cards)
    usable_ace = (1 in cards and total + 10 <= 21)
    if usable_ace:
        total += 10
    return total, usable_ace

def is_blackjack(cards):
    """Return True if hand is a natural blackjack."""
    return len(cards) == 2 and sorted(cards) == [1, 10]

def encode_state_vec(cards, dealer_up, tc_idx):
    """
    Encode the player's state as a normalized 6D vector.
    [total_norm, usable_ace, dealer_norm, tc_norm, hand_size, ace_count_norm]
    """
    total, usable = hand_value(cards)
    total_clamped = min(max(total, 4), 21)
    hand_size = min(len(cards), 5) / 5.0
    num_aces = cards.count(1) / 4.0

    return np.array([
        (total_clamped - 4) / (21 - 4),   # normalized total
        1.0 if usable else 0.0,           # usable ace flag
        (dealer_up - 1) / 9.0,            # dealer upcard normalization
        tc_idx / (len(COUNT_BINS) - 1),   # true count normalization
        hand_size,                        # normalized hand size
        num_aces                          # normalized ace count
    ], dtype=np.float32)

# ============================================================
# 🧠 DEALER & FIXED STRATEGIES
# ============================================================
def play_dealer(deck, shoe, running_count):
    """Dealer draws until reaching 17 or more."""
    total, _ = hand_value(deck)
    while total < 17:
        c = shoe_draw(shoe)
        deck.append(c)
        running_count += hi_lo_value(c)
        total, _ = hand_value(deck)
    return total, running_count

def conservative_strategy(cards):
    t, _ = hand_value(cards)
    return 0 if t < 12 else 1

def normal_strategy(cards):
    t, _ = hand_value(cards)
    return 0 if t < 17 else 1

def aggressive_strategy(cards):
    t, _ = hand_value(cards)
    return 0 if t < 19 else 1

PLAYER_TYPES = [conservative_strategy, normal_strategy, aggressive_strategy]

def play_fixed_player(cards, dealer_up, shoe, running_count, strat_fn):
    """Simulate a non-learning player using a fixed strategy."""
    done = False
    while not done:
        a = strat_fn(cards)
        if a == 0:  # HIT
            c = shoe_draw(shoe)
            cards.append(c)
            running_count += hi_lo_value(c)
            t, _ = hand_value(cards)
            if t > 21:
                done = True
        else:
            done = True
    return hand_value(cards)[0], running_count

# ============================================================
# ⚙️ AGENT LOGIC
# ============================================================
def can_split_allowed(hand, can_split_flag):
    """Check if a split is allowed."""
    return can_split_flag and len(hand) == 2 and hand[0] == hand[1]

def agent_step(hand, dealer_up, action, can_split, shoe, running_count):
    """
    Execute one action and return (new_hand, reward, done, running_count, multiplier).
    """
    double_mult = 1
    reward = None
    done = False

    # SPLIT
    if action == 3 and can_split_allowed(hand, can_split):
        c1, c2 = shoe_draw(shoe), shoe_draw(shoe)
        running_count += hi_lo_value(c1) + hi_lo_value(c2)
        return "split", [[hand[0], c1], [hand[1], c2]], True, running_count, 1

    # HIT
    if action == 0:
        c = shoe_draw(shoe)
        hand.append(c)
        running_count += hi_lo_value(c)
        total, _ = hand_value(hand)
        if total > 21:
            reward = -1.0  # bust
            done = True
        return hand, reward, done, running_count, 1

    # STAND
    if action == 1:
        done = True
        return hand, reward, done, running_count, 1

    # DOUBLE
    if action == 2:
        c = shoe_draw(shoe)
        hand.append(c)
        running_count += hi_lo_value(c)
        double_mult = 2
        done = True
        return hand, reward, done, running_count, double_mult

    # SURRENDER
    if action == 4:
        reward = -0.5
        done = True
        return hand, reward, done, running_count, 1

    return hand, reward, done, running_count, 1  # fallback
def step_blackjack_env(shoe, player_hand, dealer_hand, action, running_count):
    """
    Executes one action in the blackjack environment.
    Supports: HIT, STAND, DOUBLE, SPLIT, SURRENDER.
    Returns:
        next_hand, dealer_hand, reward, done, new_running_count
    """
    done = False
    reward = 0.0
    double_mult = 1
    split_hands = []

    def hand_value(hand):
        total = sum(hand)
        aces = hand.count(1)
        while total > 21 and aces:
            total -= 10
            aces -= 1
        return total

    def update_count(card, running):
        if 2 <= card <= 6:
            running += 1
        elif card == 1 or card == 10:
            running -= 1
        return running

    # Update count for visible cards
    for c in player_hand + dealer_hand:
        running_count = update_count(c, running_count)

    # ---- SPLIT ----
    if action == 3 and len(player_hand) == 2 and player_hand[0] == player_hand[1]:
        # Draw one card for each split hand
        card1 = [player_hand[0], shoe_draw(shoe)]
        card2 = [player_hand[1], shoe_draw(shoe)]
        running_count = update_count(card1[-1], running_count)
        running_count = update_count(card2[-1], running_count)
        # Play each hand recursively (simplified: stand or hit once)
        r1 = _simulate_split_hand(card1, dealer_hand, shoe, running_count)
        r2 = _simulate_split_hand(card2, dealer_hand, shoe, running_count)
        reward = (r1 + r2) / 2.0
        done = True
        return [card1, card2], dealer_hand, reward, done, running_count

    # ---- DOUBLE ----
    if action == 2:
        double_mult = 2
        player_hand.append(shoe_draw(shoe))
        running_count = update_count(player_hand[-1], running_count)
        done = True

    # ---- HIT ----
    if action == 0:
        player_hand.append(shoe_draw(shoe))
        running_count = update_count(player_hand[-1], running_count)
        if hand_value(player_hand) > 21:
            reward = -1.0
            done = True
        return player_hand, dealer_hand, reward, done, running_count

    # ---- STAND or DOUBLE ----
    if action in [1, 2]:
        player_total = hand_value(player_hand)
        # Dealer plays
        dealer_total = hand_value(dealer_hand)
        while dealer_total < 17:
            dealer_hand.append(shoe_draw(shoe))
            running_count = update_count(dealer_hand[-1], running_count)
            dealer_total = hand_value(dealer_hand)

        # Compute final reward
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

    # ---- SURRENDER ----
    if action == 4:
        reward = -0.5
        done = True
        return player_hand, dealer_hand, reward, done, running_count

    return player_hand, dealer_hand, reward, done, running_count
def _simulate_split_hand(hand, dealer_hand, shoe, running_count, max_splits=1):
    """
    Play a split hand recursively for DQN training.
    Returns:
        reward: float
        running_count: updated count
    """
    def hand_value(cards):
        total = sum(cards)
        aces = cards.count(1)
        while total > 21 and aces:
            total -= 10
            aces -= 1
        return total

    def update_count(card, running):
        if 2 <= card <= 6:
            running += 1
        elif card == 1 or card >= 10:
            running -= 1
        return running

    # Check for further split
    if max_splits > 0 and len(hand) == 2 and hand[0] == hand[1]:
        # Split hand into two
        c1, c2 = shoe_draw(shoe), shoe_draw(shoe)
        running_count = update_count(c1, running_count)
        running_count = update_count(c2, running_count)

        reward1, running_count = _simulate_split_hand([hand[0], c1], dealer_hand, shoe, running_count, max_splits - 1)
        reward2, running_count = _simulate_split_hand([hand[1], c2], dealer_hand, shoe, running_count, max_splits - 1)
        return (reward1 + reward2) / 2.0, running_count

    # Play hand normally: HIT until 17+ or bust (simplified for DQN)
    done = False
    while not done:
        total = hand_value(hand)
        if total >= 17:
            done = True
            break
        # Hit once
        c = shoe_draw(shoe)
        hand.append(c)
        running_count = update_count(c, running_count)
        if hand_value(hand) > 21:
            done = True
            break

    # Dealer plays
    dealer_total = hand_value(dealer_hand)
    while dealer_total < 17:
        c = shoe_draw(shoe)
        dealer_hand.append(c)
        running_count = update_count(c, running_count)
        dealer_total = hand_value(dealer_hand)

    # Resolve outcome
    player_total = hand_value(hand)
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
# 🎯 PLAY SINGLE HAND (DQN EPISODE)
# ============================================================
def play_single_hand_dqn(policy_net, shoe, running_count, dealer_hand,
                         player_hand, tc_idx, eps, device, replay):
    """
    Plays a single blackjack hand using epsilon-greedy DQN policy.
    Logs transitions into replay buffer.
    """

    done = False
    total_reward = 0.0

    # Encode initial state
    state = encode_state_vec(player_hand, dealer_hand[0], tc_idx)

    while not done:
        # ----------------- ε-greedy action -----------------
        if random.random() < eps:
            action = random.randrange(NUM_ACTIONS)
        else:
            with torch.no_grad():
                s = torch.tensor(state, dtype=torch.float32, device=device).unsqueeze(0)
                q_values = policy_net(s)
                action = int(q_values.argmax().item())

        # ----------------- Take Action -----------------
        next_hand, dealer_hand_new, reward, done, running_count = step_blackjack_env(
            shoe, player_hand, dealer_hand, action, running_count
        )

        # Next state (if not terminal)
        if not done:
            next_tc_idx = true_count_bin_from_running(running_count, len(shoe))
            next_state = encode_state_vec(next_hand, dealer_hand_new[0], next_tc_idx)
        else:
            next_state = np.zeros_like(state, dtype=np.float32)

        # Reward clipping for stability
        reward = np.clip(reward, -1.0, 1.0)
        total_reward += reward

        # ----------------- Store Transition -----------------
        replay.push(state, action, reward, next_state, done)

        # Move to next
        state = next_state
        player_hand = next_hand
        dealer_hand = dealer_hand_new

    return total_reward, running_count
