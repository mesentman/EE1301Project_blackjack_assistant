import torch, numpy as np, random
import torch.nn as nn, torch.optim as optim
from model import DuelingMLP
from replay_buffer import ReplayBuffer
from environment import *
from utils import export_policy
from config import *

def train_and_export(num_episodes=NUM_EPISODES):
    state_dim = 4
    policy_net = DuelingMLP(state_dim, NUM_ACTIONS).to(DEVICE)
    target_net = DuelingMLP(state_dim, NUM_ACTIONS).to(DEVICE)
    target_net.load_state_dict(policy_net.state_dict())
    target_net.eval()
    optimizer = optim.Adam(policy_net.parameters(), lr=LR)
    replay = ReplayBuffer(REPLAY_CAPACITY)
    eps = EPS_START
    step_count = 0

    for ep in range(num_episodes):
        if ep % 2000 == 0:
            print(f"Episode {ep}")
        shoe = make_shoe()
        running_count = 0
        dealer_hand = [shoe_draw(shoe), shoe_draw(shoe)]

        # Play other players first
        for strat_fn in PLAYER_TYPES:
            play_fixed_player([shoe_draw(shoe), shoe_draw(shoe)], dealer_hand[0], shoe, running_count, strat_fn)

        player_hand = [shoe_draw(shoe), shoe_draw(shoe)]
        tc_idx = true_count_bin_from_running(running_count, len(shoe))
        reward, running_count = play_single_hand_dqn(policy_net, shoe, running_count, dealer_hand, player_hand, tc_idx, eps, DEVICE)

        state_vec = encode_state_vec(player_hand, dealer_hand[0], tc_idx)
        replay.push(state_vec, 0, reward, state_vec.copy(), True)

        if len(replay) >= BATCH_SIZE:
            batch = replay.sample(BATCH_SIZE)
            s = torch.tensor(batch.state, dtype=torch.float32, device=DEVICE)
            a = torch.tensor(batch.action, dtype=torch.long, device=DEVICE).unsqueeze(1)
            r = torch.tensor(batch.reward, dtype=torch.float32, device=DEVICE).unsqueeze(1)
            ns = torch.tensor(batch.next_state, dtype=torch.float32, device=DEVICE)
            done = torch.tensor(batch.done, dtype=torch.float32, device=DEVICE).unsqueeze(1)

            with torch.no_grad():
                target_val = r + GAMMA * (1 - done) * target_net(ns).max(1, keepdim=True)[0]
            current_val = policy_net(s).gather(1, a)
            loss = nn.MSELoss()(current_val, target_val)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

        eps = max(EPS_END, EPS_START - (EPS_START - EPS_END) * (ep / EPS_DECAY))
        step_count += 1
        if step_count % TARGET_UPDATE_STEPS == 0:
            target_net.load_state_dict(policy_net.state_dict())

    # Export policy
    policy_table = np.zeros((22, 2, 11), dtype=np.uint8)
    for pt in range(4, 22):
        for ua in [0, 1]:
            for tc in range(len(COUNT_BINS)):
                dealer = 6
                hand = [pt - 10 if ua else pt - 2, 2]
                state_vec = encode_state_vec(hand, dealer, tc)
                with torch.no_grad():
                    s = torch.tensor(state_vec, dtype=torch.float32, device=DEVICE).unsqueeze(0)
                    q = policy_net(s).cpu().numpy()[0]
                    policy_table[pt, ua, tc] = np.argmax(q)

    export_policy(policy_table)
