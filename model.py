import torch.nn as nn

class DuelingMLP(nn.Module):
    def __init__(self, in_dim, out_dim):
        super().__init__()
        self.fc = nn.Sequential(
            nn.Linear(in_dim, 128), nn.ReLU(),
            nn.Linear(128, 128), nn.ReLU()
        )
        self.value = nn.Linear(128, 1)
        self.adv = nn.Linear(128, out_dim)

    def forward(self, x):
        x = self.fc(x)
        v = self.value(x)
        a = self.adv(x)
        return v + (a - a.mean(dim=1, keepdim=True))
