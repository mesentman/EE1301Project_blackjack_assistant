import random
from collections import deque, namedtuple
import numpy as np
import torch

Transition = namedtuple("Transition", ("state", "action", "reward", "next_state", "done"))


# ============================================================
# 🔁 Standard Replay Buffer
# ============================================================
class ReplayBuffer:
    def __init__(self, capacity, device=None):
        """
        Standard experience replay buffer for DQN-style agents.
        Stores (s, a, r, s', done) tuples and supports PyTorch or NumPy sampling.
        """
        self.buffer = deque(maxlen=capacity)
        self.device = device or torch.device("cpu")

    def push(self, *args):
        """Store a single transition (state, action, reward, next_state, done)."""
        self.buffer.append(Transition(*args))

    def sample(self, batch_size):
        """Vectorized sampling — returns a namedtuple of PyTorch tensors."""
        if len(self.buffer) < batch_size:
            raise ValueError("Not enough samples in buffer to draw a batch.")

        # Use NumPy indexing instead of Python's random.sample for speed
        idxs = np.random.choice(len(self.buffer), batch_size, replace=False)
        batch = [self.buffer[i] for i in idxs]
        batch = Transition(*zip(*batch))

        # Use as_tensor to avoid unnecessary memory copies
        states = torch.as_tensor(np.array(batch.state), dtype=torch.float32, device=self.device)
        actions = torch.as_tensor(batch.action, dtype=torch.int64, device=self.device)
        rewards = torch.as_tensor(batch.reward, dtype=torch.float32, device=self.device)
        next_states = torch.as_tensor(np.array(batch.next_state), dtype=torch.float32, device=self.device)
        dones = torch.as_tensor(batch.done, dtype=torch.float32, device=self.device)

        return Transition(states, actions, rewards, next_states, dones)

    def sample_numpy(self, batch_size):
        """Sample a batch and return it as NumPy arrays."""
        if len(self.buffer) < batch_size:
            raise ValueError("Not enough samples in buffer to draw a batch.")
        idxs = np.random.choice(len(self.buffer), batch_size, replace=False)
        batch = [self.buffer[i] for i in idxs]
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


# ============================================================
# ⚖️ Prioritized Replay Buffer
# ============================================================
class PrioritizedReplayBuffer(ReplayBuffer):
    def __init__(self, capacity, alpha=0.6, device=None):
        """
        Prioritized replay buffer for improved sample efficiency.
        α controls how strongly priorities affect sampling (0 = uniform).
        """
        super().__init__(capacity, device)
        self.alpha = alpha
        self.priorities = np.zeros((capacity,), dtype=np.float32)
        self.position = 0

    def push(self, *args):
        """Add transition with max priority (ensures new samples are likely to be used soon)."""
        max_prio = self.priorities.max() if len(self.buffer) > 0 else 1.0

        if len(self.buffer) < self.buffer.maxlen:
            self.buffer.append(Transition(*args))
        else:
            self.buffer[self.position] = Transition(*args)

        self.priorities[self.position] = max_prio
        self.position = (self.position + 1) % self.buffer.maxlen

    def sample(self, batch_size, beta=0.4):
        """Sample transitions with probability proportional to priority^α."""
        if len(self.buffer) == 0:
            raise ValueError("Cannot sample from an empty buffer.")

        prios = self.priorities[:len(self.buffer)]
        probs = prios ** self.alpha
        probs /= probs.sum()

        idxs = np.random.choice(len(self.buffer), batch_size, p=probs, replace=False)
        batch = [self.buffer[i] for i in idxs]
        batch = Transition(*zip(*batch))

        # Importance-sampling weights
        total = len(self.buffer)
        weights = (total * probs[idxs]) ** (-beta)
        weights /= weights.max()
        weights = torch.as_tensor(weights, dtype=torch.float32, device=self.device).unsqueeze(1)

        states = torch.as_tensor(np.array(batch.state), dtype=torch.float32, device=self.device)
        actions = torch.as_tensor(batch.action, dtype=torch.int64, device=self.device)
        rewards = torch.as_tensor(batch.reward, dtype=torch.float32, device=self.device)
        next_states = torch.as_tensor(np.array(batch.next_state), dtype=torch.float32, device=self.device)
        dones = torch.as_tensor(batch.done, dtype=torch.float32, device=self.device)

        return Transition(states, actions, rewards, next_states, dones), idxs, weights

    def update_priorities(self, idxs, priorities):
        """Update sampling priorities (usually with TD-error magnitude)."""
        for i, p in zip(idxs, priorities):
            self.priorities[i] = float(np.abs(p) + 1e-5)
