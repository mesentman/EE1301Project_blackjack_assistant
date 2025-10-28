import random
from collections import deque, namedtuple
import numpy as np

Transition = namedtuple("Transition", ("state", "action", "reward", "next_state", "done"))

class ReplayBuffer:
    def __init__(self, capacity):
        self.buffer = deque(maxlen=capacity)

    def push(self, *args):
        """Store a single transition (s, a, r, s', done)."""
        self.buffer.append(Transition(*args))

    def sample(self, batch_size):
        """Randomly sample a batch of transitions."""
        batch = random.sample(self.buffer, batch_size)
        return Transition(*zip(*batch))

    def sample_numpy(self, batch_size):
        """Sample a batch and return as NumPy arrays (optional helper)."""
        batch = self.sample(batch_size)
        return (
            np.array(batch.state, dtype=np.float32),
            np.array(batch.action, dtype=np.int64),
            np.array(batch.reward, dtype=np.float32),
            np.array(batch.next_state, dtype=np.float32),
            np.array(batch.done, dtype=np.float32),
        )

    def is_ready(self, batch_size, warmup=5000):
        """Check if buffer has enough data to start training."""
        return len(self.buffer) >= max(batch_size, warmup)

    def __len__(self):
        return len(self.buffer)
