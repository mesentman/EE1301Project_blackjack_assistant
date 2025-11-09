import time
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
# Local imports
from model import NoisyDuelingMLP
from replay_buffer import PrioritizedReplayBuffer, ReplayBuffer
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
def train_and_export_quick():
    """
    Mini quick test: very small buffer, few episodes, fast pre-fill,
    no behavior cloning, prints shapes and rewards for debugging.
    """
    state_dim = 6
    NUM_ACTIONS_QUICK = 5  # same as normal

    # ---- Model ----
    policy_net = NoisyDuelingMLP(state_dim, NUM_ACTIONS_QUICK, hidden=64).to(DEVICE)
    target_net = NoisyDuelingMLP(state_dim, NUM_ACTIONS_QUICK, hidden=64).to(DEVICE)
    target_net.load_state_dict(policy_net.state_dict())
    target_net.eval()
    optimizer = torch.optim.Adam(policy_net.parameters(), lr=LR)

    # ---- Tiny Replay buffer ----
    replay = PrioritizedReplayBuffer(
        capacity=50,              # tiny buffer
        state_shape=(state_dim,), # must be iterable
        alpha=PER_ALPHA,
        device=DEVICE
    )

    step_count = 0
    total_reward_window = 0.0

    # ---- Pre-fill buffer quickly ----
    print("[🟢] Quick pre-fill of replay buffer...")
    while len(replay) < 10:  # only 10 transitions
        shoe = make_shoe()
        running_count = 0
        dealer_hand = [shoe_draw(shoe), shoe_draw(shoe)]
        player_hand = [shoe_draw(shoe), shoe_draw(shoe)]
        tc_idx = true_count_bin_from_running(running_count, len(shoe))

        reward, running_count, _ = play_single_hand_dqn(
            policy_net, shoe, running_count, dealer_hand,
            player_hand, tc_idx, device=DEVICE, replay=replay,
            reward_scale=REWARD_SCALE, shaping_coeff=0.0,
            step_counter=0, max_steps=1  # only 1 step per hand
        )
        print(f"Pre-fill {len(replay)} | Reward: {reward:.3f}")
    print("[🟢] Quick pre-fill done!")

    # ---- Run 5 mini training episodes ----
    for ep in range(5):
        shoe = make_shoe()
        running_count = 0
        dealer_hand = [shoe_draw(shoe), shoe_draw(shoe)]
        player_hand = [shoe_draw(shoe), shoe_draw(shoe)]
        tc_idx = true_count_bin_from_running(running_count, len(shoe))

        reward, running_count, _ = play_single_hand_dqn(
            policy_net, shoe, running_count, dealer_hand,
            player_hand, tc_idx, device=DEVICE, replay=replay,
            reward_scale=REWARD_SCALE, shaping_coeff=0.0,
            step_counter=0, max_steps=1
        )
        print(f"[Episode {ep+1}] Reward: {reward:.3f} | Replay size: {len(replay)}")

        # ---- Tiny training step ----
        if len(replay) >= 2:
            (batch, idxs, weights) = replay.sample(2, beta=0.4)

            s = batch.state
            a = batch.action.long().unsqueeze(1)
            r = batch.reward.float().unsqueeze(1)
            ns = batch.next_state
            done = batch.done.float().unsqueeze(1)

            with torch.no_grad():
                next_actions = policy_net(ns).argmax(1, keepdim=True)
                next_q = target_net(ns).gather(1, next_actions)
                target_val = r + GAMMA * (1 - done) * next_q

            current_val = policy_net(s).gather(1, a)
            td_loss = nn.SmoothL1Loss()(current_val, target_val)

            optimizer.zero_grad()
            td_loss.backward()
            optimizer.step()

            step_count += 1
            policy_net.reset_noise()
            target_net.reset_noise()
            print(f"Step {step_count} | TD loss: {td_loss.item():.4f}")
    
    print("[✅] Quick test done!")

def _train_and_export_core(num_episodes, print_progress=False, reward_window=10_000,
                           use_bc=True, bc_episodes=500, bc_weight_start=1.0):
    state_dim = 6

    # ---- Model ----
    policy_net = NoisyDuelingMLP(state_dim, NUM_ACTIONS, hidden=HIDDEN).to(DEVICE)
    target_net = NoisyDuelingMLP(state_dim, NUM_ACTIONS, hidden=HIDDEN).to(DEVICE)
    target_net.load_state_dict(policy_net.state_dict())
    target_net.eval()
    optimizer = torch.optim.Adam(policy_net.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)

    # ---- Replay buffer ----
    # NOTE: new ReplayBuffer / PrioritizedReplayBuffer expect state_shape and device
    if USE_PER:
        replay = PrioritizedReplayBuffer(REPLAY_CAPACITY, state_shape=(state_dim,), alpha=PER_ALPHA, device=DEVICE)
    else:
        raise ValueError("PER must be True for this agent")

    step_count = 0
    total_reward_window = 0.0
    smoothed_loss = 0.0
    start_time = time.time()

    # ==== Pre-fill buffer with basic strategy ====
    print("[🟢] Pre-filling replay buffer with basic strategy...")
    shoe = make_shoe(NUM_DECKS)
    running_count = 0
    while len(replay) < PRE_FILL_TRANSITIONS:
        if len(shoe) < 52:
            shoe = make_shoe()
            running_count = 0
        
        dealer_hand = [shoe_draw(shoe), shoe_draw(shoe)]
        player_hand = [shoe_draw(shoe), shoe_draw(shoe)]
        tc_idx = true_count_bin_from_running(running_count, len(shoe))

        reward, running_count, _ = play_single_hand_dqn(
        None, shoe, running_count, dealer_hand,
        player_hand, tc_idx, device=DEVICE, replay=replay,
        reward_scale=REWARD_SCALE, shaping_coeff=0.0,
        step_counter=0, max_steps=5,
        use_basic_strategy=True   # add a flag to use basic strategy only
)
    
    print(f"[🟢] Replay buffer pre-filled ({len(replay)} transitions)")
    # ==== Main DQN training loop ====
    for ep in range(num_episodes):
        shoe = make_shoe()
        running_count = 0
        dealer_hand = [shoe_draw(shoe), shoe_draw(shoe)]
        for strat_fn in PLAYER_TYPES:
            play_fixed_player([shoe_draw(shoe), shoe_draw(shoe)], dealer_hand[0], shoe, running_count, strat_fn)

        player_hand = [shoe_draw(shoe), shoe_draw(shoe)]
        tc_idx = true_count_bin_from_running(running_count, len(shoe))

        reward, running_count, _ = play_single_hand_dqn(
            policy_net, shoe, running_count, dealer_hand,
            player_hand, tc_idx, device=DEVICE, replay=replay,
            reward_scale=REWARD_SCALE, shaping_coeff=SHAPING_COEFF,
            step_counter=0, max_steps=MAX_STEPS
        )
        total_reward_window += reward

        # ---- Training update ----
        if len(replay) >= REPLAY_WARMUP:
            beta = min(1.0, PER_BETA_START + step_count / PER_BETA_FRAMES)

            # New API: prioritized.sample -> (states, actions, rewards, next_states, dones, idxs, weights)
            s, a, r, ns, done, idxs, weights = replay.sample(BATCH_SIZE, beta=beta)

            # Ensure shapes: actions as (batch,1) for gather, rewards as (batch,1), done as (batch,1)
            a_idx = a.detach().long().unsqueeze(1)            # (B,1)
            r = r.detach().float().unsqueeze(1)               # (B,1)
            done = done.detach().float().unsqueeze(1)         # (B,1)

            with torch.no_grad():
                next_actions = policy_net(ns).argmax(1, keepdim=True)     # (B,1)
                next_q = target_net(ns).gather(1, next_actions)          # (B,1)
                target_val = r + GAMMA * (1 - done) * next_q            # (B,1)

            current_val = policy_net(s).gather(1, a_idx)                 # (B,1)
            td_loss_unreduced = nn.SmoothL1Loss(reduction='none')(current_val, target_val)  # (B,1)
            td_loss = (td_loss_unreduced * weights).mean()

            # ---- Behavior Cloning weight schedule ----
            bc_weight = bc_weight_start * max(0, (bc_episodes - ep) / bc_episodes) if use_bc else 0.0

            if bc_weight > 0:
                # CrossEntropyLoss expects logits of shape (B, C) and targets of shape (B,)
                # a.squeeze() would be (B,) dtype long
                bc_targets = a.detach().long().squeeze()
                bc_loss = nn.CrossEntropyLoss()(policy_net(s), bc_targets)
            else:
                bc_loss = 0.0

            loss = td_loss + bc_weight * bc_loss

            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(policy_net.parameters(), GRAD_CLIP)
            optimizer.step()

            # Update priorities using TD magnitude (abs)
            td_errors = (current_val - target_val).detach().cpu().squeeze().abs().numpy()
            # replay.update_priorities expects (idxs, new_priorities)
            replay.update_priorities(idxs, td_errors + 1e-5)

            step_count += 1
            policy_net.reset_noise()
            if step_count % TARGET_UPDATE_STEPS == 0:
                target_net.load_state_dict(policy_net.state_dict())
                target_net.reset_noise()

        # ---- Logging ----
        if print_progress and (ep + 1) % reward_window == 0:
            avg_reward = total_reward_window / reward_window
            policy_net.eval()
            eval_avg = 0.0
            for _ in range(500):
                shoe = make_shoe()
                running_count = 0
                dealer_hand = [shoe_draw(shoe), shoe_draw(shoe)]
                for strat_fn in PLAYER_TYPES:
                    play_fixed_player([shoe_draw(shoe), shoe_draw(shoe)], dealer_hand[0], shoe, running_count, strat_fn)
                player_hand = [shoe_draw(shoe), shoe_draw(shoe)]
                tc_idx = true_count_bin_from_running(running_count, len(shoe))
                r, _, _ = play_single_hand_dqn(policy_net, shoe, running_count, dealer_hand,
                                               player_hand, tc_idx, device=DEVICE, replay=None,
                                               reward_scale=REWARD_SCALE, shaping_coeff=0.0,
                                               step_counter=0, max_steps=MAX_STEPS)
                eval_avg += r
            eval_avg /= 500
            policy_net.train()
            elapsed = time.time() - start_time
            print(f"[Ep {ep+1:,}] AvgR={avg_reward:.3f} | EvalR={eval_avg:.3f} | "
                  f"Steps={step_count:,} | Replay={len(replay):,} | "
                  f"Loss={smoothed_loss:.4f} | Time={elapsed:.1f}s")
            total_reward_window = 0

    # ---- Export final policy ----
    policy_net.eval()
    policy_table = np.zeros((22, 2, len(COUNT_BINS)), dtype=np.uint8)
    with torch.no_grad():
        for pt in range(4, 22):
            for ua in [0, 1]:
                for tc in range(len(COUNT_BINS)):
                    dealer = 6
                    hand = [pt - 10 if ua else pt - 2, 2]
                    state_vec = encode_state_vec(hand, dealer, tc)
                    s = torch.tensor(state_vec, dtype=torch.float32, device=DEVICE).unsqueeze(0)
                    q = policy_net(s).cpu().numpy()[0]
                    policy_table[pt, ua, tc] = np.argmax(q)

    export_policy(policy_table)
    print("[✅] Training complete — final policy exported!")
