import random
import numpy as np
import torch

# ------------------------
# DEVICE SETUP
# ------------------------
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ------------------------
# BLACKJACK ENVIRONMENT SETTINGS
# ------------------------
NUM_DECKS = 6
NUM_ACTIONS = 5
ACTION_NAMES = ["HIT", "STAND", "DOUBLE", "SPLIT", "SURRENDER"]
COUNT_BINS = list(range(-5, 6))  # e.g., card counting feature range
MAX_STEPS = 200
# ------------------------
# TRAINING PARAMETERS
# ------------------------
NUM_EPISODES = 500_000
BATCH_SIZE = 512
REPLAY_CAPACITY = 500_000
REPLAY_WARMUP = 20_000
TARGET_UPDATE_STEPS = 2_000

# ------------------------
# DQN / RL HYPERPARAMETERS
# ------------------------
GAMMA = 0.995
LR = 5e-4
HIDDEN = 512
GRAD_CLIP = 5.0
WEIGHT_DECAY = 1e-6

# ------------------------
# EXPLORATION SETTINGS
# ------------------------
USE_NOISY_NETS = True  # set False if using epsilon-greedy
EPS_START = 0.0
EPS_END = 0.0
EPS_DECAY = 1_000_000  # ignored if USE_NOISY_NETS=True

# ------------------------
# PRIORITIZED EXPERIENCE REPLAY (PER)
# ------------------------
USE_PER = True
PER_ALPHA = 0.7
PER_BETA_START = 0.5
PER_BETA_FRAMES = int(NUM_EPISODES * 0.5)

# ------------------------
# REWARD SHAPING
# ------------------------
REWARD_SCALE = 1.0
SHAPING_COEFF = 0.01

# ------------------------
# REPRODUCIBILITY
# ------------------------
#SEED = 42
#random.seed(SEED)
#np.random.seed(SEED)
#torch.manual_seed(SEED)
#if torch.cuda.is_available():
 #   torch.cuda.manual_seed_all(SEED)

