import numpy as np
import torch


# ============================================================
# 🧱 Base Replay Buffer (fast vectorized version)
# ============================================================
class ReplayBuffer:
    def __init__(self, capacity, state_shape, device=None):
        """
        Fast, vectorized experience replay buffer for DQN-style agents.
        Stores transitions as preallocated NumPy arrays for maximum speed.
        """
        self.capacity = capacity
        self.device = device or torch.device("cpu")

        # Preallocate contiguous arrays
        self.states = np.zeros((capacity, *state_shape), dtype=np.float32)
        self.actions = np.zeros((capacity,), dtype=np.int64)
        self.rewards = np.zeros((capacity,), dtype=np.float32)
        self.next_states = np.zeros((capacity, *state_shape), dtype=np.float32)
        self.dones = np.zeros((capacity,), dtype=np.float32)

        # Ring buffer pointers
        self.position = 0
        self.size = 0

    def push(self, state, action, reward, next_state, done):
        """Add a new transition to the buffer."""
        self.states[self.position] = state
        self.actions[self.position] = action
        self.rewards[self.position] = reward
        self.next_states[self.position] = next_state
        self.dones[self.position] = done

        self.position = (self.position + 1) % self.capacity
        self.size = min(self.size + 1, self.capacity)

    def sample(self, batch_size):
        """Sample a random batch of transitions."""
        if self.size < batch_size:
            raise ValueError("Not enough samples in buffer to draw a batch.")

        idxs = np.random.randint(0, self.size, size=batch_size)
        return (
            torch.as_tensor(self.states[idxs], dtype=torch.float32, device=self.device),
            torch.as_tensor(self.actions[idxs], dtype=torch.int64, device=self.device),
            torch.as_tensor(self.rewards[idxs], dtype=torch.float32, device=self.device),
            torch.as_tensor(self.next_states[idxs], dtype=torch.float32, device=self.device),
            torch.as_tensor(self.dones[idxs], dtype=torch.float32, device=self.device),
        )

    def is_ready(self, batch_size, warmup=5000):
        """Check if buffer has enough data to start training."""
        return self.size >= max(batch_size, warmup)

    def clear(self):
        """Completely reset the buffer."""
        self.position = 0
        self.size = 0

    def __len__(self):
        return self.size


# ============================================================
# ⚖️ Prioritized Replay Buffer (fast version)
# ============================================================
class PrioritizedReplayBuffer:
    def __init__(self, capacity, state_shape, alpha=0.6, device=None):
        """
        Prioritized replay buffer with vectorized storage.
        α controls how strongly priorities affect sampling (0 = uniform).
        """
        self.capacity = capacity
        self.device = device or torch.device("cpu")
        self.alpha = alpha

        # Main storage (vectorized)
        self.states = np.zeros((capacity, *state_shape), dtype=np.float32)
        self.actions = np.zeros((capacity,), dtype=np.int64)
        self.rewards = np.zeros((capacity,), dtype=np.float32)
        self.next_states = np.zeros((capacity, *state_shape), dtype=np.float32)
        self.dones = np.zeros((capacity,), dtype=np.float32)

        # Priority data
        self.priorities = np.ones((capacity,), dtype=np.float32)
        self.position = 0
        self.size = 0

    def push(self, state, action, reward, next_state, done):
        """Add a transition with the current max priority."""
        max_prio = self.priorities[:self.size].max() if self.size > 0 else 1.0

        self.states[self.position] = state
        self.actions[self.position] = action
        self.rewards[self.position] = reward
        self.next_states[self.position] = next_state
        self.dones[self.position] = done
        self.priorities[self.position] = max_prio

        self.position = (self.position + 1) % self.capacity
        self.size = min(self.size + 1, self.capacity)

    def sample(self, batch_size, beta=0.4):
        """Sample transitions with probability proportional to priority^α."""
        if self.size == 0:
            raise ValueError("Cannot sample from an empty buffer.")

        scaled_prios = self.priorities[:self.size] ** self.alpha
        probs = scaled_prios / scaled_prios.sum()

        # Faster random sampling with replacement (no need for unique indices)
        idxs = np.random.choice(self.size, batch_size, p=probs, replace=True)

        # Importance-sampling weights
        weights = (self.size * probs[idxs]) ** (-beta)
        weights /= weights.max()  # normalize to [0,1]

        states = torch.as_tensor(self.states[idxs], dtype=torch.float32, device=self.device)
        actions = torch.as_tensor(self.actions[idxs], dtype=torch.int64, device=self.device)
        rewards = torch.as_tensor(self.rewards[idxs], dtype=torch.float32, device=self.device)
        next_states = torch.as_tensor(self.next_states[idxs], dtype=torch.float32, device=self.device)
        dones = torch.as_tensor(self.dones[idxs], dtype=torch.float32, device=self.device)
        weights = torch.as_tensor(weights[:, None], dtype=torch.float32, device=self.device)

        return (states, actions, rewards, next_states, dones, idxs, weights)

    def update_priorities(self, idxs, new_priorities):
        """Update sampling priorities (usually TD-error magnitudes)."""
        for i, p in zip(idxs, new_priorities):
            self.priorities[i] = float(abs(p) + 1e-5)

    def is_ready(self, batch_size, warmup=5000):
        """Check if buffer has enough data to start training."""
        return self.size >= max(batch_size, warmup)

    def __len__(self):
        return self.size
