import math
import torch
import torch.nn as nn

# ---------- Optional NoisyLinear (for exploration) ----------
class NoisyLinear(nn.Module):
    """Noisy linear layer from (Fortunato et al., 2017). Useful for exploration."""
    def __init__(self, in_features, out_features, sigma_init=0.5):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features

        self.weight_mu = nn.Parameter(torch.empty(out_features, in_features))
        self.weight_sigma = nn.Parameter(torch.empty(out_features, in_features))
        self.register_buffer('weight_eps', torch.empty(out_features, in_features))

        self.bias_mu = nn.Parameter(torch.empty(out_features))
        self.bias_sigma = nn.Parameter(torch.empty(out_features))
        self.register_buffer('bias_eps', torch.empty(out_features))

        self.sigma_init = sigma_init
        self.reset_parameters()
        self.reset_noise()

    def reset_parameters(self):
        mu_range = 1.0 / math.sqrt(self.in_features)
        nn.init.uniform_(self.weight_mu, -mu_range, mu_range)
        nn.init.uniform_(self.bias_mu, -mu_range, mu_range)
        nn.init.constant_(self.weight_sigma, self.sigma_init / math.sqrt(self.in_features))
        # FIXED: Use in_features for both weight and bias sigma (was out_features for bias)
        nn.init.constant_(self.bias_sigma, self.sigma_init / math.sqrt(self.in_features))

    def reset_noise(self):
        self.weight_eps.normal_()
        self.bias_eps.normal_()

    def forward(self, x):
        if self.training:
            weight = self.weight_mu + self.weight_sigma * self.weight_eps
            bias = self.bias_mu + self.bias_sigma * self.bias_eps
        else:
            weight = self.weight_mu
            bias = self.bias_mu
        return nn.functional.linear(x, weight, bias)


# ---------- Standard Dueling MLP (your original improved) ----------
class DuelingMLP(nn.Module):
    def __init__(self, in_dim, out_dim, hidden=256):
        super().__init__()
        self.fc = nn.Sequential(
            nn.Linear(in_dim, hidden),
            nn.LayerNorm((hidden,)),   
            nn.LeakyReLU(0.01),
            nn.Linear(hidden, hidden),
            nn.LayerNorm((hidden,)),   
            nn.LeakyReLU(0.01)         
)

        self.value = nn.Linear(hidden, 1)
        self.adv = nn.Linear(hidden, out_dim)

        self.apply(self._init_weights)

    def _init_weights(self, m):
        if isinstance(m, nn.Linear):
            nn.init.kaiming_uniform_(m.weight, a=0.01, nonlinearity='leaky_relu')
            if m.bias is not None:
                nn.init.constant_(m.bias, 0.0)

    def forward(self, x):
        x = self.fc(x)
        v = self.value(x)
        a = self.adv(x)
        return v + (a - a.mean(dim=1, keepdim=True))


# ---------- Noisy Dueling variant (drop-in replacement) ----------
class NoisyDuelingMLP(nn.Module):
    def __init__(self, in_dim, out_dim, hidden=256, sigma_init=0.5):
        super().__init__()
        self.fc = nn.Sequential(
            nn.Linear(in_dim, hidden),
            nn.LayerNorm((hidden,)),
            nn.LeakyReLU(0.01),
            nn.Linear(hidden, hidden),
            nn.LayerNorm((hidden,)),
            nn.LeakyReLU(0.01),
        )
        
        self.value = NoisyLinear(hidden, 1, sigma_init=sigma_init)
        self.adv = NoisyLinear(hidden, out_dim, sigma_init=sigma_init)

        self.apply(self._init_weights)

    def _init_weights(self, m):
        if isinstance(m, nn.Linear):
            nn.init.kaiming_uniform_(m.weight, a=0.01, nonlinearity='leaky_relu')
            if m.bias is not None:
                nn.init.constant_(m.bias, 0.0)

    def reset_noise(self):
        self.value.reset_noise()
        self.adv.reset_noise()

    def forward(self, x):
        #print(f"[DEBUG] forward input shape: {x.shape}, dtype: {x.dtype}")
        x = self.fc(x)
        v = self.value(x)
        a = self.adv(x)
        return v + (a - a.mean(dim=1, keepdim=True))