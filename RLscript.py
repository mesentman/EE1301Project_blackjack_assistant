import numpy as np
import random

# -------------------- Blackjack Environment --------------------
# Player total: 4-21
# Usable ace: 0/1
# Dealer upcard: 1-10
# Actions: 0=HIT, 1=STAND, 2=DOUBLE, 3=SURRENDER

ACTIONS = [0, 1, 2, 3]

def draw_card():
    # 1=Ace, 2-10 face cards as 10
    card = random.randint(1,13)
    return min(card,10)

def hand_value(cards):
    total = sum(cards)
    usable_ace = 1 in cards and total + 10 <= 21
    if usable_ace: total += 10
    return total, usable_ace

def play_dealer(deck):
    total, usable = hand_value(deck)
    while total < 17:
        deck.append(draw_card())
        total, usable = hand_value(deck)
    return total

def step(player_cards, dealer_card, action):
    """
    Returns: (new_state, reward, done)
    """
    player_total, usable_ace = hand_value(player_cards)
    done = False

    # Implement action
    if action == 0: # HIT
        player_cards.append(draw_card())
        player_total, usable_ace = hand_value(player_cards)
        if player_total > 21:
            done = True
            reward = -1
        else:
            reward = 0
    elif action == 1: # STAND
        dealer_hand = [dealer_card, draw_card()]
        dealer_total = play_dealer(dealer_hand)
        done = True
        if player_total > dealer_total or dealer_total > 21:
            reward = 1
        elif player_total == dealer_total:
            reward = 0
        else:
            reward = -1
    elif action == 2: # DOUBLE
        player_cards.append(draw_card())
        player_total, usable_ace = hand_value(player_cards)
        dealer_hand = [dealer_card, draw_card()]
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
    elif action == 3: # SURRENDER
        done = True
        reward = -0.5

    new_state = (min(max(player_total,4),21), usable_ace, dealer_card)
    return new_state, reward, done

# -------------------- Q-Learning --------------------
# Initialize Q table
Q = np.zeros((22, 2, 11, 4)) # player_total 0-21, usable_ace 0/1, dealer 1-10, action 0-3

alpha = 0.1   # learning rate
gamma = 0.99  # discount factor
epsilon = 0.1 # exploration

num_episodes = 50000

for episode in range(num_episodes):
    # Start a random hand
    player = [draw_card(), draw_card()]
    dealer_up = draw_card()
    total, usable_ace = hand_value(player)
    state = (min(max(total,4),21), usable_ace, dealer_up)
    done = False

    while not done:
        # Epsilon-greedy action
        if random.random() < epsilon:
            action = random.choice(ACTIONS)
        else:
            action = np.argmax(Q[state[0], int(state[1]), state[2]])

        next_state, reward, done = step(player.copy(), dealer_up, action)

        # Q-learning update
        old_val = Q[state[0], int(state[1]), state[2], action]
        future_val = 0 if done else np.max(Q[next_state[0], int(next_state[1]), next_state[2]])
        Q[state[0], int(state[1]), state[2], action] = old_val + alpha * (reward + gamma * future_val - old_val)

        state = next_state

# -------------------- Export policy --------------------
policy_table = np.argmax(Q, axis=3)
np.save("blackjack_policy.npy", policy_table) # save policy to file

print("Training complete! Sample policy:")
for pt in range(17,22):
    for ua in [0,1]:
        for dealer in range(1,11):
            action = policy_table[pt, ua, dealer]
            print(f"Player {pt} {'Ace' if ua else 'NoAce'} vs Dealer {dealer} -> Action {action}")
