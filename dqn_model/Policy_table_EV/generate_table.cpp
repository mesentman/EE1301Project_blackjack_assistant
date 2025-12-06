#include <iostream>
#include <fstream>  // Required for file output
#include <vector>
#include <numeric>
#include <algorithm>
#include <random>
#include <iomanip>
#include <cmath>

// INCLUDE YOUR POLICY FILE
#include "blackjack_policy.h"

// --- CONFIG ---
const int SIM_ITERATIONS = 2000; // Hands per cell
const int NUM_DECKS = 6;
const char* OUTPUT_FILENAME = "win_rate_table.h";

// --- STRUCTURES ---
enum Action { HIT = 0, STAND = 1, DOUBLE = 2, SPLIT = 3 };

struct Hand {
    std::vector<int> cards;
    int bet;
    int total;
    bool isSoft;
    bool isPair;
    
    Hand() : bet(1), total(0), isSoft(false), isPair(false) {}
    
    void addCard(int c) {
        cards.push_back(c);
        update();
    }
    
    void update() {
        total = 0; 
        int aces = 0;
        for(int c : cards) {
            total += c;
            if(c == 11) aces++;
        }
        while(total > 21 && aces > 0) {
            total -= 10;
            aces--;
        }
        isSoft = (aces > 0);
        isPair = (cards.size() == 2 && cards[0] == cards[1]);
    }
};

std::mt19937 rng(42);

// --- HELPERS ---
int getCard(int& runningCount) {
    int r = std::uniform_int_distribution<>(1, 13)(rng);
    int val = (r > 10) ? 10 : (r == 1) ? 11 : r;
    
    // Update hypothetical count
    if (val >= 2 && val <= 6) runningCount++;
    else if (val == 10 || val == 11) runningCount--;
    
    return val;
}

int getAction(int pTotal, int pAce, int dCard, int tcIdx, bool isPair) {
    int code = blackjack_policy[pTotal][pAce][dCard][tcIdx];
    
    if (code >= 30) {
        if (isPair) return SPLIT;
        if (code == 30) return HIT;
        if (code == 31) return STAND;
        if (code == 32) return DOUBLE;
    }
    return code; 
}

// --- SIMULATION ENGINE ---
// Returns 100 if win, 50 if push, 0 if loss
int playHand(int pTotal, int pAce, int dCard, int tcIdx) {
    int runningCount = 0;
    std::vector<Hand> hands;
    hands.emplace_back();
    
    // Force Player Cards
    if (pAce) {
        hands[0].addCard(11);
        hands[0].addCard(pTotal - 11);
    } else {
        // Rough approx for Hard totals
        if (pTotal % 2 == 0 && pTotal <= 18 && pTotal >= 4) {
             // Randomize pair vs non-pair composition roughly 
             // (Simple version: just make non-pair mostly)
             int c1 = 10; 
             int c2 = pTotal - 10;
             if (c2 < 2) { c1 = pTotal/2; c2 = pTotal - c1; } // Fallback
             hands[0].addCard(c1);
             hands[0].addCard(c2);
        } else {
            hands[0].addCard(10);
            hands[0].addCard(pTotal - 10);
        }
    }
    
    // Force Dealer Card
    int dHidden = getCard(runningCount);
    Hand dealer;
    int dVal = (dCard == 8) ? 10 : (dCard == 9) ? 11 : dCard + 2;
    dealer.addCard(dVal);
    dealer.addCard(dHidden);

    // Play
    float profit = 0;
    
    for (size_t i = 0; i < hands.size(); ++i) {
        bool turnEnd = false;
        if (hands[i].total == 21 && hands[i].cards.size() == 2) turnEnd = true; 

        while (!turnEnd) {
            if (hands[i].total > 21) break;

            int act = getAction(hands[i].total > 21 ? 21 : hands[i].total, 
                                hands[i].isSoft ? 1 : 0, 
                                dCard, 
                                tcIdx, 
                                hands[i].isPair);
            
            if (act == DOUBLE && hands[i].cards.size() > 2) act = HIT;
            if (act == SPLIT && hands.size() >= 2) act = HIT; 

            if (act == HIT) {
                hands[i].addCard(getCard(runningCount));
            } else if (act == STAND) {
                turnEnd = true;
            } else if (act == DOUBLE) {
                hands[i].bet *= 2;
                hands[i].addCard(getCard(runningCount));
                turnEnd = true;
            } else if (act == SPLIT) {
                Hand newH;
                int splitC = hands[i].cards[0];
                hands[i].cards.clear();
                hands[i].addCard(splitC);
                hands[i].addCard(getCard(runningCount));
                
                newH.addCard(splitC);
                newH.addCard(getCard(runningCount));
                hands.push_back(newH);
            }
        }
    }

    // Dealer Play (H17)
    while (dealer.total < 17 || (dealer.total == 17 && dealer.isSoft)) {
        dealer.addCard(getCard(runningCount));
    }

    // Scoring
    for (auto& h : hands) {
        if (h.total > 21) profit -= h.bet;
        else if (dealer.total > 21) profit += h.bet;
        else if (h.total > dealer.total) profit += h.bet;
        else if (h.total < dealer.total) profit -= h.bet;
    }
    
    if (profit > 0) return 100; // Win
    if (profit == 0) return 50; // Push
    return 0; // Loss
}

int main() {
    std::cout << "Starting generation of " << OUTPUT_FILENAME << "..." << std::endl;
    std::cout << "This may take a few seconds." << std::endl;

    std::ofstream outFile(OUTPUT_FILENAME);

    if (!outFile.is_open()) {
        std::cerr << "Error: Could not create output file!" << std::endl;
        return 1;
    }

    outFile << "#ifndef BLACKJACK_WINRATES_H\n";
    outFile << "#define BLACKJACK_WINRATES_H\n\n";
    outFile << "#include <stdint.h>\n\n";
    outFile << "// Win Rate Table (0 to 100)\n";
    outFile << "// 0 = Loss, 50 = Push, 100 = Win\n";
    outFile << "const uint8_t blackjack_winrates[22][2][10][12] = {\n";

    // Loop Player Total
    for (int pt = 0; pt < 22; ++pt) {
        if (pt % 5 == 0) std::cout << "Processing Total " << pt << "..." << std::endl; // Progress bar
        
        outFile << "    // Total " << pt << "\n";
        outFile << "    {\n";
        
        // Loop Usable Ace
        for (int ace = 0; ace < 2; ++ace) {
            outFile << "        {";
            
            // Loop Dealer Card
            for (int dc = 0; dc < 10; ++dc) {
                outFile << "{";
                
                // Loop True Count
                for (int tc = 0; tc < 12; ++tc) {
                    
                    if (pt < 4) {
                        outFile << "0"; // Unused
                    } else {
                        // SIMULATE THIS CELL
                        long totalScore = 0;
                        for(int k=0; k<SIM_ITERATIONS; ++k) {
                            totalScore += playHand(pt, ace, dc, tc);
                        }
                        int avgRate = totalScore / SIM_ITERATIONS;
                        outFile << avgRate;
                    }

                    if (tc < 11) outFile << ",";
                }
                outFile << "}";
                if (dc < 9) outFile << ",";
            }
            outFile << "}";
            if (ace < 1) outFile << ",";
            outFile << "\n";
        }
        outFile << "    }";
        if (pt < 21) outFile << ",";
        outFile << "\n";
    }

    outFile << "};\n\n";
    outFile << "#endif\n";
    
    outFile.close();
    std::cout << "Done! Generated " << OUTPUT_FILENAME << std::endl;
    return 0;
}