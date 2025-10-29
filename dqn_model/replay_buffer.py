import random
from collections import deque, namedtuple
import numpy as np
import torch

Transition = namedtuple("Transition", ("state", "action", "reward", "next_state", "done"))

class ReplayBuffer:
    def __init__(self, capacity, device=None):
        """
        Experience replay buffer for off-policy learning (e.g., DQN).
        Stores (s, a, r, s', done) tuples.
        """
        self.buffer = deque(maxlen=capacity)
        self.device = device or torch.device("cpu")

    def push(self, *args):
        """Store a single transition (state, action, reward, next_state, done)."""
        self.buffer.append(Transition(*args))

    def sample(self, batch_size):
        """Sample a batch and return it as a namedtuple of tensors."""
        batch = random.sample(self.buffer, batch_size)
        batch = Transition(*zip(*batch))

        states = torch.tensor(np.array(batch.state), dtype=torch.float32, device=self.device)
        actions = torch.tensor(batch.action, dtype=torch.int64, device=self.device)
        rewards = torch.tensor(batch.reward, dtype=torch.float32, device=self.device)
        next_states = torch.tensor(np.array(batch.next_state), dtype=torch.float32, device=self.device)
        dones = torch.tensor(batch.done, dtype=torch.float32, device=self.device)

        return Transition(states, actions, rewards, next_states, dones)

    def sample_numpy(self, batch_size):
        """Sample a batch and return it as NumPy arrays"""
        batch = random.sample(self.buffer, batch_size)
        batch = Transition(*zip(*batch))
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

    def clear(self):
        """Completely reset the buffer."""
        self.buffer.clear()

    def __len__(self):
        return len(self.buffer)
