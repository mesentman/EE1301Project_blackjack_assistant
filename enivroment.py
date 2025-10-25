import random
from collections import deque
import numpy as np
from config import COUNT_BINS, NUM_DECKS, MAX_STEPS_PER_EP

# -------------------- SHOE & COUNT --------------------
def make_shoe(num_decks=NUM_DECKS):
    shoe = []
    for _ in range(num_decks):
        for r in range(1, 14):
            shoe.extend([min(r, 10)] * 4)
    random.shuffle(shoe)
    return deque(shoe)

def shoe_draw(shoe): return shoe.popleft()

def hi_lo_value(card):
    if 2 <= card <= 6: return 1
    if 7 <= card <= 9: return 0
    return -1

def true_count_bin_from_running(running_count, cards_remaining):
    decks_left = max(cards_remaining / 52.0, 0.25)
    tc = running_count / decks_left
    tc_round = int(round(tc))
    tc_round = max(min(tc_round, COUNT_BINS[-1]), COUNT_BINS[0])
    return tc_round + abs(COUNT_BINS[0])

# -------------------- HAND HELPERS --------------------
def hand_value(cards):
    total = sum(cards)
    usable_ace = (1 in cards and total + 10 <= 21)
    if usable_ace: total += 10
    return total, usable_ace

def is_blackjack(cards): return len(cards) == 2 and sum(cards) == 11 + 1

def encode_state_vec(cards, dealer_up, tc_idx):
    total, usable = hand_value(cards)
    total_clamped = min(max(total, 4), 21)
    return np.array([
        (total_clamped - 4) / (21 - 4),
        1.0 if usable else 0.0,
        (dealer_up - 1) / 9.0,
        tc_idx / (len(COUNT_BINS) - 1)
    ], dtype=np.float32)

# -------------------- DEALER + OTHERS --------------------
def play_dealer(deck, shoe, running_count):
    total, _ = hand_value(deck)
    while total < 17:
        c = shoe_draw(shoe)
        deck.append(c)
        running_count += hi_lo_value(c)
        total, _ = hand_value(deck)
    return total, running_count

def conservative_strategy(cards): t, _ = hand_value(cards); return 0 if t < 12 else 1
def normal_strategy(cards): t, _ = hand_value(cards); return 0 if t < 17 else 1
def aggressive_strategy(cards): t, _ = hand_value(cards); return 0 if t < 19 else 1
PLAYER_TYPES = [conservative_strategy, normal_strategy, aggressive_strategy]

def play_fixed_player(cards, dealer_up, shoe, running_count, strat_fn):
    done = False
    while not done:
        a = strat_fn(cards)
        if a == 0:
            c = shoe_draw(shoe)
            cards.append(c)
            running_count += hi_lo_value(c)
            t, _ = hand_value(cards)
            if t > 21: done = True
        else: done = True
    return hand_value(cards)[0], running_count

# -------------------- AGENT LOGIC --------------------
def can_split_allowed(hand, can_split_flag):
    return can_split_flag and len(hand) == 2 and hand[0] == hand[1]

def agent_step(hand, dealer_up, action, can_split, shoe, running_count):
    total, _ = hand_value(hand)
    if action == 3 and can_split_allowed(hand, can_split):
        c1, c2 = shoe_draw(shoe), shoe_draw(shoe)
        running_count += hi_lo_value(c1) + hi_lo_value(c2)
        return "split", [[hand[0], c1], [hand[1], c2]], running_count
    if action == 0:  # HIT
        c = shoe_draw(shoe)
        hand.append(c)
        running_count += hi_lo_value(c)
        t, _ = hand_value(hand)
        return hand, -1.0 if t > 21 else None, t > 21, running_count, 1
    if action == 1: return hand, None, True, running_count, 1  # STAND
    if action == 2:  # DOUBLE
        c = shoe_draw(shoe)
        hand.append(c)
        running_count += hi_lo_value(c)
        return hand, None, True, running_count, 2
    if action == 4: return hand, -0.5, True, running_count, 1  # SURRENDER
    return hand, None, False, running_count, 1

# -------------------- PLAY SINGLE HAND --------------------
def play_single_hand_dqn(policy_net, shoe, running_count, dealer_hand, hand, tc_idx, eps, device, can_split=True, depth=0):
    steps = 0
    from torch import no_grad, tensor
    import numpy as np

    while True:
        steps += 1
        state_vec = encode_state_vec(hand, dealer_hand[0], tc_idx)
        if random.random() < eps:
            action = random.randrange(5)
        else:
            with no_grad():
                s = tensor(state_vec, dtype=float, device=device).unsqueeze(0)
                q = policy_net(s).cpu().numpy()[0]
                action = int(np.argmax(q))

        res = agent_step(hand, dealer_hand[0], action, can_split, shoe, running_count)

        if isinstance(res[0], str) and res[0] == "split":
            subhands, running_count = res[1], res[2]
            total = 0.0
            for sh in subhands:
                tc_idx = true_count_bin_from_running(running_count, len(shoe))
                rsub, running_count = play_single_hand_dqn(policy_net, shoe, running_count, dealer_hand, sh, tc_idx, eps, device, can_split=False, depth=depth + 1)
                total += rsub
            return total, running_count

        hand, reward_or_none, done, running_count, double_mult = res
        if done and reward_or_none is not None:
            return reward_or_none * double_mult, running_count
        if done:
            dealer_total, running_count = play_dealer(list(dealer_hand), shoe, running_count)
            player_total, _ = hand_value(hand)
            if is_blackjack(hand) and len(hand) == 2: payoff = 1.5 * double_mult
            elif player_total > 21: payoff = -1.0 * double_mult
            elif dealer_total > 21 or player_total > dealer_total: payoff = 1.0 * double_mult
            elif player_total == dealer_total: payoff = 0.0
            else: payoff = -1.0 * double_mult
            return payoff, running_count

        tc_idx = true_count_bin_from_running(running_count, len(shoe))
        if steps > MAX_STEPS_PER_EP: return 0.0, running_count
