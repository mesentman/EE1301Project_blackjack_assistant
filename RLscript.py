import numpy as np
import random

# -------------------- Blackjack Environment --------------------
ACTIONS = [0, 1, 2, 3]  # HIT, STAND, DOUBLE, SURRENDER

# ----- Hi-Lo Counting -----
def hilo_value(card):
    if card in [2, 3, 4, 5, 6]:
        return +1
    elif card in [7, 8, 9]:
        return 0
    else:
        return -1

# -------------------- Deck & Shoe --------------------
def create_shoe(num_decks=6):
    shoe = []
    for _ in range(num_decks):
        for card in range(1, 14):
            shoe += [card] * 4
    random.shuffle(shoe)
    return shoe

num_decks = 6
shoe = create_shoe(num_decks)
running_count = 0

def draw_card_from_shoe():
    global running_count, shoe
    if len(shoe) == 0:
        shoe = create_shoe(num_decks)
        running_count = 0
    card = shoe.pop()
    running_count += hilo_value(min(card, 10))
    return min(card, 10)

def true_count():
    decks_remaining = max(len(shoe) / 52, 1e-6)
    return running_count / decks_remaining

def tc_bin(tc):
    """Discretize true count into 4 bins."""
    if tc <= -2:
        return 0
    elif tc <= 0:
        return 1
    elif tc <= 2:
        return 2
    else:
        return 3

# -------------------- Game Mechanics --------------------
def hand_value(cards):
    total = sum(cards)
    usable_ace = 1 in cards and total + 10 <= 21
    if usable_ace:
        total += 10
    return total, usable_ace

def play_dealer(deck):
    total, usable = hand_value(deck)
    while total < 17:
        deck.append(draw_card_from_shoe())
        total, usable = hand_value(deck)
    return total

def step(player_cards, dealer_card, action):
    player_total, usable_ace = hand_value(player_cards)
    done = False

    if action == 0:  # HIT
        player_cards.append(draw_card_from_shoe())
        player_total, usable_ace = hand_value(player_cards)
        if player_total > 21:
            done = True
            reward = -1
        else:
            reward = 0

    elif action == 1:  # STAND
        dealer_hand = [dealer_card, draw_card_from_shoe()]
        dealer_total = play_dealer(dealer_hand)
        done = True
        if player_total > dealer_total or dealer_total > 21:
            reward = 1
        elif player_total == dealer_total:
            reward = 0
        else:
            reward = -1

    elif action == 2:  # DOUBLE
        player_cards.append(draw_card_from_shoe())
        player_total, usable_ace = hand_value(player_cards)
        dealer_hand = [dealer_card, draw_card_from_shoe()]
        dealer_total = play_dealer(dealer_hand)
        done = True
        if player_total > 21:
            reward = -2
        elif player_total > dealer_total or dealer_total > 21:
            reward = 2
        elif player_total == dealer_total:
            reward = 0
        else:
            reward = -2

    elif action == 3:  # SURRENDER
        done = True
        reward = -0.5

    new_state = (min(max(player_total, 4), 21), usable_ace, dealer_card)
    return new_state, reward, done

# -------------------- Q-Learning --------------------
# State = (player_total 4–21, usable_ace 0/1, dealer_card 1–10, true_count_bin 0–3)
Q = np.zeros((22, 2, 11, 4, 4))  # 4 bins for TC

alpha = 0.1
gamma = 0.99
epsilon = 0.1
num_episodes = 50000

for episode in range(num_episodes):
    player = [draw_card_from_shoe(), draw_card_from_shoe()]
    dealer_up = draw_card_from_shoe()
    total, usable_ace = hand_value(player)
    tc = true_count()
    tc_category = tc_bin(tc)
    state = (min(max(total, 4), 21), usable_ace, dealer_up, tc_category)
    done = False

    while not done:
        if random.random() < epsilon:
            action = random.choice(ACTIONS)
        else:
            action = np.argmax(Q[state[0], int(state[1]), state[2], state[3]])

        next_state, reward, done = step(player.copy(), dealer_up, action)
        next_tc = true_count()
        next_tc_bin = tc_bin(next_tc)

        old_val = Q[state[0], int(state[1]), state[2], state[3], action]
        if done:
            future_val = 0
        else:
            future_val = np.max(Q[next_state[0], int(next_state[1]), next_state[2], next_tc_bin])

        Q[state[0], int(state[1]), state[2], state[3], action] = (
            old_val + alpha * (reward + gamma * future_val - old_val)
        )

        state = (next_state[0], next_state[1], next_state[2], next_tc_bin)

    # Progress display
    if (episode + 1) % 10000 == 0:
        print(f"Episode {episode+1}, Running Count: {running_count}, True Count: {true_count():.2f}")

# -------------------- Export policy --------------------
policy_table = np.argmax(Q, axis=4)
np.save("blackjack_policy_tc.npy", policy_table)

print("Training complete! Sample policy:")
for pt in range(17, 22):
    for ua in [0, 1]:
        for dealer in range(1, 11):
            for tc_bin_id in range(4):
                action = policy_table[pt, ua, dealer, tc_bin_id]
                print(f"Player {pt} {'Ace' if ua else 'NoAce'} vs Dealer {dealer} | TC Bin {tc_bin_id} -> Action {action}")
