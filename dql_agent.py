# Existing imports
import torch, numpy as np, random
import torch.nn as nn, torch.optim as optim
from model import DuelingMLP
from replay_buffer import ReplayBuffer
from environment import *
from utils import export_policy
from config import *
from tqdm import trange


# ---------------- Full Training Function ----------------
def train_and_export(num_episodes=NUM_EPISODES):
    _train_and_export_core(num_episodes, print_progress=True)


# ---------------- Test / Short Training Function ----------------
def train_and_export_test(num_episodes=1000):
    _train_and_export_core(num_episodes, print_progress=True, reward_window=50)


# ---------------- Core Training Function ----------------


def _train_and_export_core(num_episodes, print_progress=False, reward_window=200):
    state_dim = 6
    policy_net = DuelingMLP(state_dim, NUM_ACTIONS).to(DEVICE)
    target_net = DuelingMLP(state_dim, NUM_ACTIONS).to(DEVICE)
    target_net.load_state_dict(policy_net.state_dict())
    target_net.eval()

    optimizer = optim.Adam(policy_net.parameters(), lr=LR)
    replay = ReplayBuffer(REPLAY_CAPACITY)

    eps = EPS_START
    step_count = 0
    total_reward_window = 0.0
    smoothed_loss = 0.0
    REPLAY_WARMUP = 20_000

    with trange(num_episodes, desc="Training", unit="ep") as progress_bar:
        for ep in progress_bar:
            shoe = make_shoe()
            running_count = 0
            dealer_hand = [shoe_draw(shoe), shoe_draw(shoe)]

            # Simulate fixed-strategy players to warm up environment
            for strat_fn in PLAYER_TYPES:
                play_fixed_player([shoe_draw(shoe), shoe_draw(shoe)],
                                  dealer_hand[0], shoe, running_count, strat_fn)

            player_hand = [shoe_draw(shoe), shoe_draw(shoe)]
            tc_idx = true_count_bin_from_running(running_count, len(shoe))

            reward, running_count = play_single_hand_dqn(
                policy_net, shoe, running_count, dealer_hand,
                player_hand, tc_idx, eps, DEVICE, replay
            )

            total_reward_window += reward

            if len(replay) < REPLAY_WARMUP:
                continue

            # --- Sample minibatch ---
            batch = replay.sample(BATCH_SIZE)
            s = torch.tensor(np.array(batch.state), dtype=torch.float32, device=DEVICE)
            a = torch.tensor(batch.action, dtype=torch.long, device=DEVICE).unsqueeze(1)
            r = torch.tensor(batch.reward, dtype=torch.float32, device=DEVICE).unsqueeze(1)
            ns = torch.tensor(np.array(batch.next_state), dtype=torch.float32, device=DEVICE)
            done = torch.tensor(batch.done, dtype=torch.float32, device=DEVICE).unsqueeze(1)

            with torch.no_grad():
                next_actions = policy_net(ns).argmax(1, keepdim=True)
                next_q = target_net(ns).gather(1, next_actions)
                target_val = r + GAMMA * (1 - done) * next_q

            current_val = policy_net(s).gather(1, a)
            loss = nn.SmoothL1Loss()(current_val, target_val)
            smoothed_loss = 0.9 * smoothed_loss + 0.1 * loss.item() if smoothed_loss else loss.item()

            optimizer.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(policy_net.parameters(), 5.0)
            optimizer.step()

            step_count += 1
            eps = max(EPS_END, EPS_START * (0.999995 ** step_count))

            if step_count % TARGET_UPDATE_STEPS == 0:
                target_net.load_state_dict(policy_net.state_dict())

            if print_progress and (ep + 1) % reward_window == 0:
                avg_reward = total_reward_window / reward_window
                total_reward_window = 0
                progress_bar.write(
                    f"[Ep {ep+1:,}] Eps={eps:.3f} | AvgR={avg_reward:.3f} | "
                    f"Loss={smoothed_loss:.4f} | Steps={step_count:,} | Replay={len(replay):,}"
                )

    # --- Export final policy ---
    policy_table = np.zeros((22, 2, len(COUNT_BINS)), dtype=np.uint8)
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
    print("[✅] Training complete — final policy exported!")
