import random, numpy as np, torch

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Environment / problem
NUM_DECKS = 6
NUM_ACTIONS = 5
ACTION_NAMES = ["HIT", "STAND", "DOUBLE", "SPLIT", "SURRENDER"]
COUNT_BINS = list(range(-5, 6))

# Training schedule
NUM_EPISODES = 500_000
BATCH_SIZE = 512            # larger batch for stability
REPLAY_CAPACITY = 500_000
REPLAY_WARMUP = 20_000      # more warmup to stabilize PER
TARGET_UPDATE_STEPS = 2_000 # slightly slower target updates

# Core learning parameters
GAMMA = 0.995               # long-term discounting helps blackjack
LR = 5e-4
HIDDEN = 512                # larger hidden layers for better function approximation

# Exploration / optimization
# epsilon-greedy is disabled when using NoisyLinear
EPS_START = 0.0
EPS_END = 0.0
EPS_DECAY = 1_000_000       # irrelevant with NoisyLinear

# Training niceties
GRAD_CLIP = 5.0
WEIGHT_DECAY = 1e-6

# PER toggle
USE_PER = True
PER_ALPHA = 0.7
PER_BETA_START = 0.5
PER_BETA_FRAMES = NUM_EPISODES * 0.5

# Reward shaping defaults (small)
REWARD_SCALE = 1.0
SHAPING_COEFF = 0.01        # tiny shaping reward helps early learning

# reproducibility
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)
