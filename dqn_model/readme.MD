Blackjack DQN Agent with Noisy Dueling MLP

This project implements a Deep Q-Learning agent to play Blackjack using a Noisy Dueling Multi-Layer Perceptron (MLP). The goal is to learn an optimal strategy that maximizes expected rewards over many hands, incorporating advanced techniques such as Prioritized Experience Replay and optional behavior cloning from basic strategy.

Features

Noisy Dueling MLP: Combines dueling network architecture (separate state-value and advantage streams) with learnable noise in the layers to improve exploration.

Prioritized Experience Replay: Stores transitions with priority-based sampling to focus learning on more informative experiences.

Basic Strategy Pre-Fill: Initializes the replay buffer with hands played according to basic strategy to accelerate early learning.

Behavior Cloning (optional): Uses supervised learning on pre-filled transitions to guide the agent initially.

Policy Export: Exports a table-based policy mapping player hands, dealer upcards, and true counts to optimal actions.

Workflow

Initialize the environment: Create a shoe (deck) of cards and track running counts.

Pre-fill replay buffer: Simulate hands using basic strategy and store transitions in the buffer.

Train agent: Perform Q-learning updates using transitions from the buffer, updating the target network periodically.

Optional behavior cloning: Encourage the policy to mimic basic strategy during early episodes.

Export policy: Generate a table for quick action selection based on learned Q-values.

Dependencies

Python 3.12+

PyTorch

NumPy

tqdm

Usage
python main.py


Adjust the number of episodes or replay buffer parameters in config.py.

Use train_and_export_quick() for small-scale tests.