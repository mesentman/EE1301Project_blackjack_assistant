# Compiler settings
CXX = g++
CXXFLAGS = -O3 -Wall -std=c++11

# Target executable names
SIM_TARGET = blackjack_sim
GEN_TARGET = gen_table

# Default target (runs when you type 'make')
all: $(SIM_TARGET) $(GEN_TARGET)

# Compile the Simulator
$(SIM_TARGET): Evsimulation.cpp blackjack_policy.h
	$(CXX) $(CXXFLAGS) Evsimulation.cpp -o $(SIM_TARGET)

# Compile the Table Generator
$(GEN_TARGET): generate_table.cpp blackjack_policy.h
	$(CXX) $(CXXFLAGS) generate_table.cpp -o $(GEN_TARGET)

# Clean up build files (runs when you type 'make clean')
clean:
	rm -f $(SIM_TARGET) $(GEN_TARGET) *.exe *.o