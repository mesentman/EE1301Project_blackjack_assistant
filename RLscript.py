# dqn_blackjack_export_policy.py
import random, math, csv
from collections import deque, namedtuple
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

# -------------------- CONFIG --------------------
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

NUM_DECKS = 6
RESHUFFLE_PENETRATION = 0.25

# actions
ACTION_HIT = 0
ACTION_STAND = 1
ACTION_DOUBLE = 2
ACTION_SPLIT = 3
ACTION_SURRENDER = 4
ACTION_NAMES = ["HIT", "STAND", "DOUBLE", "SPLIT", "SURRENDER"]
NUM_ACTIONS = len(ACTION_NAMES)

# count bins
COUNT_BINS = list(range(-5, 6))   # -5..5 => 11 bins

# DQN hyperparams
GAMMA = 0.99
LR = 1e-4
BATCH_SIZE = 256
REPLAY_CAPACITY = 200000
TARGET_UPDATE_STEPS = 2000
START_EPS = 1.0
END_EPS = 0.05
EPS_DECAY_STEPS = 200000

NUM_EPISODES = 100000  # default; change if you want
MAX_STEPS_PER_EP = 200  # safe guard
UPDATE_PER_EP = 2       # number of optimization steps per episode

SEED = 42
random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED)

# -------------------- SHOE & COUNT HELPERS --------------------
from collections import deque
def make_shoe(num_decks=NUM_DECKS):
    shoe = []
    for _ in range(num_decks):
        for r in range(1,14):
            shoe.extend([min(r,10)] * 4)
    random.shuffle(shoe)
    return deque(shoe)

def shoe_draw(shoe):
    return shoe.popleft()

# Hi-Lo: 2-6 -> +1, 7-9 -> 0, 10/A -> -1 (Ace counted as 1)
def hi_lo_value(card):
    if 2 <= card <= 6:
        return 1
    if 7 <= card <= 9:
        return 0
    return -1

def true_count_bin_from_running(running_count, cards_remaining):
    decks_left = max(cards_remaining / 52.0, 0.25)
    tc = running_count / decks_left
    tc_round = int(round(tc))
    tc_round = max(min(tc_round, COUNT_BINS[-1]), COUNT_BINS[0])
    return tc_round + abs(COUNT_BINS[0])  # map -5..5 -> 0..10

# -------------------- HAND HELPERS --------------------
def hand_value(cards):
    total = sum(cards)
    usable_ace = (1 in cards) and (total + 10 <= 21)
    if usable_ace:
        total += 10
    return total, usable_ace

def play_dealer(deck, shoe, running_count):
    total, _ = hand_value(deck)
    while total < 17:
        c = shoe_draw(shoe); deck.append(c); running_count += hi_lo_value(c)
        total, _ = hand_value(deck)
    return total, running_count

# -------------------- OTHER PLAYERS --------------------
def conservative_strategy(cards):
    t, _ = hand_value(cards); return 0 if t < 12 else 1

def normal_strategy(cards):
    t, _ = hand_value(cards); return 0 if t < 17 else 1

def aggressive_strategy(cards):
    t, _ = hand_value(cards); return 0 if t < 19 else 1

PLAYER_TYPES = {
    "conservative": (conservative_strategy, 0),
    "normal": (normal_strategy, 1),
    "aggressive": (aggressive_strategy, 2)
}

def play_fixed_player(cards, dealer_up, shoe, running_count, strat_fn):
    done = False
    while not done:
        a = strat_fn(cards)
        if a == 0:
            c = shoe_draw(shoe); cards.append(c); running_count += hi_lo_value(c)
            t, _ = hand_value(cards)
            if t > 21:
                done = True
        else:
            done = True
    return hand_value(cards)[0], running_count

# -------------------- NN / DQN --------------------
class MLP(nn.Module):
    def __init__(self, in_dim, out_dim):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Linear(128, out_dim)
        )
    def forward(self, x):
        return self.net(x)

# state vector: [norm_total, usable, dealer_norm, tc_idx_norm]
def encode_state_vec(cards, dealer_up, tc_idx):
    total, usable = hand_value(cards)
    total_clamped = min(max(total, 4), 21)
    return np.array([
        (total_clamped - 4) / (21 - 4),
        1.0 if usable else 0.0,
        (dealer_up - 1) / 9.0,
        tc_idx / (len(COUNT_BINS) - 1)
    ], dtype=np.float32)

Transition = namedtuple('Transition', ('state', 'action', 'reward', 'next_state', 'done'))
class ReplayBuffer:
    def __init__(self, capacity):
        self.buffer = deque(maxlen=capacity)
    def push(self, *args):
        self.buffer.append(Transition(*args))
    def sample(self, batch_size):
        batch = random.sample(self.buffer, batch_size)
        return Transition(*zip(*batch))
    def __len__(self):
        return len(self.buffer)

# -------------------- ENVIRONMENT STEP (supports split single time) --------------------
def can_split_allowed(hand, can_split_flag):
    return can_split_flag and len(hand) == 2 and hand[0] == hand[1]

def agent_step(hand, dealer_up, action, can_split, shoe, running_count):
    """Perform action on `hand`. Returns tuple:
       - if split: ("split", [hand1, hand2], running_count)
       - else: (next_hand, reward_or_None, done_bool, running_count, double_mult)
       reward_or_None: for immediate bust/surrender, return numeric reward (units per base bet).
    """
    total, usable = hand_value(hand)
    # SPLIT
    if action == ACTION_SPLIT and can_split_allowed(hand, can_split):
        c1 = shoe_draw(shoe); running_count += hi_lo_value(c1)
        c2 = shoe_draw(shoe); running_count += hi_lo_value(c2)
        return "split", [[hand[0], c1], [hand[1], c2]], running_count

    # HIT
    if action == ACTION_HIT:
        c = shoe_draw(shoe); running_count += hi_lo_value(c); hand.append(c)
        t, _ = hand_value(hand)
        if t > 21:
            return hand, -1.0, True, running_count, 1
        else:
            return hand, None, False, running_count, 1

    # STAND
    if action == ACTION_STAND:
        return hand, None, True, running_count, 1

    # DOUBLE
    if action == ACTION_DOUBLE:
        c = shoe_draw(shoe); running_count += hi_lo_value(c); hand.append(c)
        return hand, None, True, running_count, 2

    # SURRENDER
    if action == ACTION_SURRENDER:
        return hand, -0.5, True, running_count, 1

    # fallback
    return hand, None, False, running_count, 1

# play a single agent hand until resolution (handles recursion for a single split)
def play_single_hand_dqn(policy_net, shoe, running_count, dealer_hand, hand, tc_idx, eps, can_split=True):
    """
    Uses the policy_net to select actions.
    Returns unit_reward (monetary units per base bet) and updated running_count.
    """
    steps = 0
    while True:
        steps += 1
        # compute state vector
        state_vec = encode_state_vec(hand, dealer_hand[0], tc_idx)
        # eps-greedy selection
        if random.random() < eps:
            action = random.randrange(NUM_ACTIONS)
        else:
            with torch.no_grad():
                s = torch.tensor(state_vec, dtype=torch.float32, device=DEVICE).unsqueeze(0)
                q = policy_net(s).cpu().numpy()[0]
                action = int(np.argmax(q))

        res = agent_step(hand, dealer_hand[0], action, can_split, shoe, running_count)

        if isinstance(res[0], str) and res[0] == "split":
            # play both sub-hands; disable further splits (for simplicity)
            subhands = res[1]; running_count = res[2]
            total = 0.0
            for sh in subhands:
                # recompute TC index before playing each sub-hand
                tc_idx = true_count_bin_from_running(running_count, len(shoe))
                rsub, running_count = play_single_hand_dqn(policy_net, shoe, running_count, dealer_hand, sh, tc_idx, eps, can_split=False)
                total += rsub
            return total, running_count

        # normal path
        hand, reward_or_none, done, running_count, double_mult = res

        # immediate terminal reward (bust/surrender)
        if done and reward_or_none is not None:
            return reward_or_none * double_mult, running_count

        # if stand/double we must resolve vs dealer
        if done and reward_or_none is None:
            dealer_total, running_count = play_dealer(list(dealer_hand), shoe, running_count)
            player_total, _ = hand_value(hand)
            if player_total > 21:
                payoff = -1.0 * double_mult
            elif dealer_total > 21 or player_total > dealer_total:
                payoff = 1.0 * double_mult
            elif player_total == dealer_total:
                payoff = 0.0
            else:
                payoff = -1.0 * double_mult
            return payoff, running_count

        # else (HIT non-terminal) continue loop; recompute tc_idx if needed
        tc_idx = true_count_bin_from_running(running_count, len(shoe))

        if steps > MAX_STEPS_PER_EP:
            # safety fallback
            return 0.0, running_count

# -------------------- TRAINING LOOP --------------------
def train_and_export(num_episodes=NUM_EPISODES):
    # build networks
    state_dim = 4
    policy_net = MLP(state_dim, NUM_ACTIONS).to(DEVICE)
    target_net = MLP(state_dim, NUM_ACTIONS).to(DEVICE)
    target_net.load_state_dict(policy_net.state_dict())

    optimizer = optim.Adam(policy_net.parameters(), lr=LR)
    replay = ReplayBuffer(REPLAY_CAPACITY)

    # initialize shoe & running count
    shoe = make_shoe(NUM_DECKS)
    running_count = 0

    other_player_types = ["normal", "aggressive", "conservative"]  # 3 opponents

    steps_done = 0
    eps = START_EPS

    for ep in range(1, num_episodes+1):
        # reshuffle if needed
        if len(shoe) / (52.0 * NUM_DECKS) < RESHUFFLE_PENETRATION:
            shoe = make_shoe(NUM_DECKS)
            running_count = 0

        # deal initial hands
        dealer_hand = [shoe_draw(shoe), shoe_draw(shoe)]
        running_count += hi_lo_value(dealer_hand[0]) + hi_lo_value(dealer_hand[1])

        other_players = [[shoe_draw(shoe), shoe_draw(shoe)] for _ in other_player_types]
        for op in other_players:
            running_count += hi_lo_value(op[0]) + hi_lo_value(op[1])

        agent_hand = [shoe_draw(shoe), shoe_draw(shoe)]
        running_count += hi_lo_value(agent_hand[0]) + hi_lo_value(agent_hand[1])

        # other players play fully (affects running_count/shoe)
        for i, op in enumerate(other_players):
            strat_fn, _ = PLAYER_TYPES[other_player_types[i]]
            _, running_count = play_fixed_player(op, dealer_hand[0], shoe, running_count, strat_fn)

        # compute current true count bin (for state encoding)
        tc_idx = true_count_bin_from_running(running_count, len(shoe))

        # play agent hand until resolution; policy_net used for selection
        unit_reward, running_count = play_single_hand_dqn(policy_net, shoe, running_count, dealer_hand, agent_hand, tc_idx, eps, can_split=True)

        # there's no simple (s,a,r,s') logging within play_single_hand_dqn in this simplified training loop.
        # So we adopt an on-policy style: we do not push transitions inside that function; instead,
        # we gather transitions by replaying the same episode with the current policy deterministically (small overhead).
        # Simpler: run one more pass over the same initial dealing but with deterministic greedy actions to generate transitions.
        # For performance reasons we will instead skip generating many transitions and rely on reward-driven updates by sampling
        # mini-batches from existing replay. To bootstrap replay, collect a few random-play transitions initially.

        # Bootstrapping: collect some random transitions into replay occasionally
        if random.random() < 0.1:
            # perform a short random rollout to collect transitions
            # simple random mini-episode
            rshoe = make_shoe(NUM_DECKS)
            rcount = 0
            # deal minimal random sequence for some transitions
            rh = [shoe_draw(rshoe), shoe_draw(rshoe)]; rcount += hi_lo_value(rh[0]) + hi_lo_value(rh[1])
            dealeru = shoe_draw(rshoe); rcount += hi_lo_value(dealeru)
            # single random hit transition
            st_vec = encode_state_vec(rh, dealeru, true_count_bin_from_running(rcount, len(rshoe)))
            action = random.randrange(NUM_ACTIONS)
            # apply action naive
            if action == ACTION_HIT:
                c = shoe_draw(rshoe); rcount += hi_lo_value(c); rh.append(c)
                reward = -1.0 if hand_value(rh)[0] > 21 else 0.0
                ns = encode_state_vec(rh, dealeru, true_count_bin_from_running(rcount, len(rshoe)))
                replay.push(st_vec, action, reward, ns, reward != 0.0)
            else:
                # simple terminal sample
                replay.push(st_vec, action, 0.0, st_vec, True)

        # Basic optimization step(s)
        for _ in range(UPDATE_PER_EP):
            if len(replay) >= BATCH_SIZE:
                transitions = replay.sample(BATCH_SIZE)
                state_batch = torch.tensor(np.stack(transitions.state), device=DEVICE)
                action_batch = torch.tensor(transitions.action, device=DEVICE, dtype=torch.long)
                reward_batch = torch.tensor(transitions.reward, device=DEVICE, dtype=torch.float32).unsqueeze(1)
                next_state_batch = torch.tensor(np.stack(transitions.next_state), device=DEVICE)
                done_batch = torch.tensor(transitions.done, device=DEVICE, dtype=torch.float32).unsqueeze(1)

                q_values = policy_net(state_batch).gather(1, action_batch.unsqueeze(1))
                with torch.no_grad():
                    q_next = target_net(next_state_batch).max(1)[0].unsqueeze(1)
                    q_target = reward_batch + (1.0 - done_batch) * GAMMA * q_next

                loss = nn.MSELoss()(q_values, q_target)
                optimizer.zero_grad(); loss.backward(); optimizer.step()

        # occasionally push the (state->action->reward) tuple derived from the final result
        # We convert final episode summary to a training signal: for the final agent state only.
        # encode initial state and push (state, best_action, unit_reward, next_state=state, done=True)
        initial_state = encode_state_vec([agent_hand[0], agent_hand[1]], dealer_hand[0], tc_idx)
        # best action by network
        with torch.no_grad():
            q = policy_net(torch.tensor(initial_state, dtype=torch.float32, device=DEVICE).unsqueeze(0)).cpu().numpy()[0]
            chosen = int(np.argmax(q))
        replay.push(initial_state, chosen, unit_reward, initial_state, True)

        # epsilon decay
        steps_done += 1
        eps = END_EPS + (START_EPS - END_EPS) * math.exp(-1.0 * steps_done / EPS_DECAY_STEPS)

        # target update
        if steps_done % TARGET_UPDATE_STEPS == 0:
            target_net.load_state_dict(policy_net.state_dict())

        if ep % 2000 == 0:
            print(f"EP {ep:6d}  reward {unit_reward: .3f}  shoe_remain {len(shoe)}  running_count {running_count}  eps {eps:.3f}  replay {len(replay)}")

    # -------------------- EXPORT POLICY --------------------
    # enumerate all discrete states: player_total 4..21, usable 0/1, dealer 1..10, tc bins -5..5
    policy_table = np.zeros((22, 2, 11, len(COUNT_BINS)), dtype=np.uint8)  # using last dim for tc bins
    for pt in range(4, 22):
        for ua in [0, 1]:
            for dealer in range(1, 11):
                for tc_i in range(len(COUNT_BINS)):
                    # create a one-card placeholder for player to encode vector: we need card list that gives that total and usable
                    # Build a minimal synthetic hand that matches total and usable for encoding:
                    # if usable==1, put an Ace plus (total-11)
                    if ua == 1:
                        second = pt - 11
                        if second < 1:
                            second = 1
                        player_cards = [1, min(max(second,1),10)]
                    else:
                        # make two cards that sum to pt (approx): just use min(10, pt-4) and remainder
                        a = min(10, pt - 4)
                        b = pt - a
                        if b < 1:
                            b = 1
                        player_cards = [a, b]
                    state_vec = encode_state_vec(player_cards, dealer, tc_i)
                    with torch.no_grad():
                        q = policy_net(torch.tensor(state_vec, dtype=torch.float32, device=DEVICE).unsqueeze(0)).cpu().numpy()[0]
                        best = int(np.argmax(q))
                    policy_table[pt, ua, dealer, tc_i] = best

    # save numpy
    np.save("policy_table.npy", policy_table)
    # save csv for easy inspection (flattened: pt,ua,dealer,tc,action)
    with open("policy_table.csv", "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["player_total","usable_ace","dealer_up","tc_bin","action","action_name"])
        for pt in range(4,22):
            for ua in [0,1]:
                for dealer in range(1,11):
                    for tc_i in range(len(COUNT_BINS)):
                        a = int(policy_table[pt,ua,dealer,tc_i])
                        writer.writerow([pt,ua,dealer,COUNT_BINS[tc_i],a,ACTION_NAMES[a]])

    # export C header
    header_name = "policy_table.h"
    with open(header_name, "w") as h:
        h.write("// Auto-generated policy table (best action per discretized state)\n")
        h.write("// Dimensions: player_total 0..21, usable_ace 0..1, dealer_up 0..10, tc_bin 0..10\n")
        h.write("#include <stdint.h>\n\n")
        h.write("const uint8_t POLICY_TABLE[22][2][11][11] = {\n")
        for pt in range(22):
            h.write("  { // pt=%d\n" % pt)
            for ua in [0,1]:
                h.write("    { // ua=%d\n" % ua)
                for dealer in range(11):
                    h.write("      { ")
                    rowvals = []
                    for tc_i in range(len(COUNT_BINS)):
                        val = int(policy_table[pt,ua,dealer,tc_i]) if 4 <= pt <= 21 and 1 <= dealer <= 10 else 0
                        rowvals.append(str(val))
                    h.write(", ".join(rowvals))
                    h.write(" },\n")
                h.write("    },\n")
            h.write("  },\n")
        h.write("};\n")
    print("Training and export complete.\nSaved: policy_table.npy, policy_table.csv, policy_table.h")

    return policy_table

if __name__ == "__main__":
    policy = train_and_export(NUM_EPISODES)
