Blackjack Assistant: Distributed IoT & AI Strategy Engine
This project bridges Artificial Intelligence and Embedded Systems to create a real-time Blackjack strategy assistant. We developed a distributed IoT system that uses Computer Vision to identify cards, processes game states using a Deep Reinforcement Learning (DQN) model, and provides optimal strategy advice via a microcontroller dashboard.

How It Works:

The "Brain" (Deep Learning): We trained a Neural Network (Noisy Dueling DQN) in Python to master Blackjack strategy, incorporating advanced card counting (Hi-Lo) techniques to overcome the house edge.

The "Bridge" (Optimization): To enable real-time performance on low-power hardware, the AI model was distilled into a highly optimized C++ lookup table, compressing millions of training episodes into an 11KB firmware payload.

The "Body" (IoT Deployment): The system operates as an Edge Computing device. An iPhone camera captures the table state using Computer Vision and transmits card data over the network to a Particle Photon 2 microcontroller. The Photon instantly calculates the mathematical Expected Value (EV) and displays the optimal move (Hit, Stand, Double) and win probability on an attached screen.

Key Technologies: Python (PyTorch), C++, Embedded Systems (Particle Photon 2), Computer Vision, Monte Carlo Simulation.
