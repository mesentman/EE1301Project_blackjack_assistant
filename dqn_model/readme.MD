# Blackjack Assistant: Deep Q-Learning Agent & EV Simulator

**Course:** EE1301  
**Project:** Blackjack Assistant

This project implements a **Deep Q-Learning (DQN)** agent that learns optimal Blackjack strategy through self-play. It is paired with a high-performance **C++ Simulation Engine** to validate the agent's strategy using **flat betting** (constant bet size) to determine the baseline Expected Value (EV) and generate win-rate probability tables that will used to judge what is the best move based the player's cards and dealer's cards

## 🌟 Key Features

* **Advanced DQN Architecture:** Uses **Noisy Dueling DQN** with **Prioritized Experience Replay (PER)** for stable and efficient learning.
* **Card Counting Awareness:** The AI observes the "True Count" (Hi-Lo system) to make informed deviations from standard Basic Strategy.
* **Hybrid Workflow:**
    * **Python (PyTorch):** Trains the neural network and exports the policy.
    * **C++:** Simulates millions of hands to calculate the exact Expected Value (EV) and generates lookup tables.
* **Auto-Export:** Automatically generates C-header files (`blackjack_policy.h`) for easy deployment.

## 📂 Project Hierarchy

```text
├── config.py             # Hyperparameters (Learning rate, Batch size, PER settings)
├── dql_agent.py          # Core DQN Agent logic (Training loop, Action selection)
├── enivroment.py         # Blackjack Game Engine (Rules, Shoe management, Rewards)
├── main.py               # Entry point used to launch training or testing
├── model.py              # PyTorch Neural Network (NoisyDuelingMLP)
├── replay_buffer.py      # Prioritized Experience Replay (SumTree implementation)
├── utils.py              # Utilities to export .npy policies to .h headers
│
├── Policy_table_EV/      # C++ Validation & Generation Tools
│   ├── blackjack_policy.h   # (Generated) The strategy table exported by Python
│   ├── Evsimulation.cpp     # Monte Carlo Simulator (Calculates EV/Profitability)
│   ├── generate_table.cpp   # Win-Rate Table Generator (Calculates 0-100% odds)
│   └── win_rate_table.h     # (Output) The final lookup table for the Assistant UI
│
└── exports/              # Output folder for saved policies
```
## How to run the Code 
```text
1. Training the agent 
to train the model from scratch using the settings in config.py
# Standard training (default 500k episodes)
python main.py

# Quick debug run (smaller batch, fewer episodes)
python main.py quick

# Test mode (evaluate existing model)
python main.py test

What happens:

The agent plays thousands of hands against itself.

It learns Q-values for every state (Player Total, Dealer Card, True Count).

Upon completion, it exports blackjack_policy.h into the exports/ folder. or just exports into the folder Policy_table_EV

2. Validate the Strategy (C++)
After training, verify the strategy's performance using the C++ engine. This simulation uses Flat Betting (1 unit per hand) to test the efficiency of the learned playing strategy against the house edge without bet spreading.

Copy the generated blackjack_policy.h from exports/ into the Policy_table_EV/ folder.

Compile and run the simulator:

cd Policy_table_EV

# Compile the EV Simulator
g++ Evsimulation.cpp -o blackjack_sim -O3

# Run Simulation (10 Million Hands)
./blackjack_sim

3. Generate Win Rate Tables
To generate the percentage tables (0-100%) for the UI/Assistant:
# Compile the Table Generator
g++ generate_table.cpp -o gen_table -O3

# Run
./gen_table
This generates win_rate_table.h in the same directory.
```

## ⚙️ Configuration
```text
You can tweak the training performance in config.py:

NUM_DECKS: Number of decks in the shoe (Default: 6).

USE_NOISY_NETS: Set True for Noisy Layers (better exploration), False for Epsilon-Greedy.

USE_PER: Set True to use Prioritized Experience Replay.

NUM_EPISODES: Total training games (Default: 500,000).
```
## 🧠 Model Details The neural network 
```text
(model.py) is a Noisy Dueling MLP:
Input: State Vector (Player Sum, Dealer Card, Usable Ace, True Count).
Hidden Layers: 512 units with LeakyReLU.Heads: Splits into Value (V(s)) and Advantage (A(s,a)) streams.
Basically it has two parts a determinstic part of the value head then to account for the randomness we introduce a advantage stream that is stochastic meaning that if we hold our inputs constant for V(s) it always output the same thing but for A(s,a) it can output different values
Output: Q-Values for [HIT, STAND, DOUBLE, SPLIT, SURRENDER]. In this we didn't acutally use Surrender
```

## 📋 Requirements
Python 3.8+

PyTorch-Used for creating a model 

NumPy-For outputting the table in specfic array

G++ (for C++ simulation)
