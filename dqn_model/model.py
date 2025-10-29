import torch.nn as nn

class DuelingMLP(nn.Module):
    def __init__(self, in_dim, out_dim):
        super().__init__()
        self.fc = nn.Sequential(
            nn.Linear(in_dim, 256),  nn.layerNorm(256), nn.LeakyReLU(0.01),
            nn.Linear(256, 256), nn.layerNorm(256), nn.LeakyReLU(0.01), 
        )
        self.value = nn.Linear(256, 1)
        self.adv = nn.Linear(256, out_dim)

        # optional weight init
        self.apply(self._init_weights)

    def _init_weights(self, m):
        if isinstance(m, nn.Linear):
            nn.init.kaiming_uniform_(m.weight, nonlinearity='LeakyReLU')
            nn.init.constant_(m.bias, 0)

    def forward(self, x):
        x = self.fc(x)
        v = self.value(x)
        a = self.adv(x)
        return v + (a - a.mean(dim=1, keepdim=True))