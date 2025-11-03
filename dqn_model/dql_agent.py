import time
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

from model import NoisyDuelingMLP
from replay_buffer import PrioritizedReplayBuffer
from enivroment import make_shoe, shoe_draw, play_fixed_player, play_single_hand_dqn, PLAYER_TYPES
from enivroment import encode_state_vec, true_count_bin_from_running
from utils import export_policy
from config import *

DEVICE = DEVICE  # from config

# ---------------- Full Training Function ----------------
def train_and_export(num_episodes=NUM_EPISODES):
    _train_and_export_core(num_episodes, print_progress=True)
def train_and_export_test(num_episodes=1000):
    _train_and_export_core(num_episodes, print_progress=True, reward_window=100)


# ---------------- Core Training Function ----------------
def _train_and_export_core(num_episodes, print_progress=False, reward_window=10_000):
    state_dim = 6

    # ---- Model ----
    policy_net = NoisyDuelingMLP(state_dim, NUM_ACTIONS, hidden=HIDDEN).to(DEVICE)
    target_net = NoisyDuelingMLP(state_dim, NUM_ACTIONS, hidden=HIDDEN).to(DEVICE)
    target_net.load_state_dict(policy_net.state_dict())
    target_net.eval()

    optimizer = optim.Adam(policy_net.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)

    # ---- Replay buffer ----
    if USE_PER:
        replay = PrioritizedReplayBuffer(REPLAY_CAPACITY, alpha=PER_ALPHA, device=DEVICE)
    else:
        raise ValueError("This agent expects PER to be True.")

    step_count = 0
    total_reward_window = 0.0
    smoothed_loss = 0.0
    start_time = time.time()

    # ---- Evaluation function ----
    def evaluate_policy(n_eval=500):
        total = 0.0
        for _ in range(n_eval):
            shoe = make_shoe()
            running_count = 0
            dealer_hand = [shoe_draw(shoe), shoe_draw(shoe)]
            for strat_fn in PLAYER_TYPES:
                play_fixed_player([shoe_draw(shoe), shoe_draw(shoe)],
                                  dealer_hand[0], shoe, running_count, strat_fn)
            player_hand = [shoe_draw(shoe), shoe_draw(shoe)]
            tc_idx = true_count_bin_from_running(running_count, len(shoe))
            r, _ = play_single_hand_dqn(policy_net, shoe, running_count,
                                        dealer_hand, player_hand, tc_idx,
                                         device=DEVICE, replay=None,
                                        reward_scale=REWARD_SCALE, shaping_coeff=0.0)
            total += r
        return total / n_eval

    for ep in range(num_episodes):
        shoe = make_shoe()
        running_count = 0
        dealer_hand = [shoe_draw(shoe), shoe_draw(shoe)]

        # warm-up fixed strategy players
        for strat_fn in PLAYER_TYPES:
            play_fixed_player([shoe_draw(shoe), shoe_draw(shoe)],
                              dealer_hand[0], shoe, running_count, strat_fn)

        player_hand = [shoe_draw(shoe), shoe_draw(shoe)]
        tc_idx = true_count_bin_from_running(running_count, len(shoe))

        # ---- Play DQN hand ----
        reward, running_count = play_single_hand_dqn(
            policy_net, shoe, running_count, dealer_hand,
            player_hand, tc_idx, device=DEVICE, replay=replay,
             reward_scale=REWARD_SCALE, shaping_coeff=SHAPING_COEFF
        )

        total_reward_window += reward

        # ---- Training updates ----
        if len(replay) >= REPLAY_WARMUP:
            # PER sampling
            beta = min(1.0, PER_BETA_START + step_count / PER_BETA_FRAMES)
            (batch, idxs, weights) = replay.sample(BATCH_SIZE, beta=beta)

            s = batch.state
            a = batch.action.detach().clone().long().unsqueeze(1)
            r = batch.reward.detach().clone().float().unsqueeze(1)
            ns = batch.next_state
            done = batch.done.detach().clone().float().unsqueeze(1)

            # Double DQN target
            with torch.no_grad():
                next_actions = policy_net(ns).argmax(1, keepdim=True)
                next_q = target_net(ns).gather(1, next_actions)
                target_val = r + GAMMA * (1 - done) * next_q

            current_val = policy_net(s).gather(1, a)

            # Loss (with PER weights)
            loss_unreduced = nn.SmoothL1Loss(reduction='none')(current_val, target_val)
            loss = (loss_unreduced * weights).mean()
            smoothed_loss = 0.9 * smoothed_loss + 0.1 * loss.item() if smoothed_loss else loss.item()

            optimizer.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(policy_net.parameters(), GRAD_CLIP)
            optimizer.step()

            # Update PER priorities
            td_errors = (current_val - target_val).detach().cpu().squeeze().abs().numpy()
            replay.update_priorities(idxs, td_errors)

            # Increment step count
            step_count += 1

            # Reset noisy weights
            policy_net.reset_noise()
            target_net.reset_noise()

            if step_count % TARGET_UPDATE_STEPS == 0:
                target_net.load_state_dict(policy_net.state_dict())

        # ---- Logging ----
        if print_progress and (ep + 1) % reward_window == 0:
            avg_reward = total_reward_window / reward_window
            eval_avg = evaluate_policy(n_eval=500)
            elapsed = time.time() - start_time
            eps_per_sec = (ep + 1) / elapsed
            print(f"[Ep {ep+1:,}] AvgR={avg_reward:.3f} | EvalR={eval_avg:.3f} | Steps={step_count:,} "
                  f"| Replay={len(replay):,} | Elapsed={elapsed:.1f}s | Ep/s={eps_per_sec:.2f} | Loss={smoothed_loss:.4f}")
            total_reward_window = 0

    # ---- Export final policy table ----
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
