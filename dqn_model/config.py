import torch, random, numpy as np

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Environment / problem
NUM_DECKS = 6
NUM_ACTIONS = 5
ACTION_NAMES = ["HIT", "STAND", "DOUBLE", "SPLIT", "SURRENDER"]
COUNT_BINS = list(range(-5, 6))

# Training schedule
NUM_EPISODES = 500_000
BATCH_SIZE = 256             # smaller batches often give more stable updates
REPLAY_CAPACITY = 200_000
REPLAY_WARMUP = 10_000        # <-- don't train until replay has this many transitions
TARGET_UPDATE_STEPS = 1000   # sync target net every 1k steps (faster than 2k)

# Exploration / optimization
EPS_START = 1.0
EPS_END = 0.05
EPS_DECAY = 200_000          # faster decay so agent starts exploiting earlier
GAMMA = 0.99
LR = 5e-4                    # learning rate tuned for stability (1e-3 is okay, 5e-4 safer)
MAX_STEPS_PER_EP = 200
SEED = 42

random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
