import torch, random, numpy as np

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

NUM_DECKS = 6
NUM_ACTIONS = 5
ACTION_NAMES = ["HIT", "STAND", "DOUBLE", "SPLIT", "SURRENDER"]
COUNT_BINS = list(range(-5, 6))

NUM_EPISODES = 500_000
BATCH_SIZE = 256
REPLAY_CAPACITY = 200_000
TARGET_UPDATE_STEPS = 2000

EPS_START = 1.0
EPS_END = 0.05
EPS_DECAY = 400_000
GAMMA = 0.99
LR = 1e-4
MAX_STEPS_PER_EP = 200
SEED = 42

random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
