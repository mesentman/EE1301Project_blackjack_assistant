#include <iostream>
#include <vector>
#include <numeric>
#include <algorithm>
#include <random>
#include <iomanip>
#include <cmath>

// Include policy table header
#include "blackjack_policy.h"

// --- CONFIGURATION ---
const int NUM_DECKS = 6;
const int SIMULATION_HANDS = 10000000; // 10 Million hands for accuracy
const bool HIT_SOFT_17 = true;         // Dealer hits Soft 17
const float BLACKJACK_PAYOUT = 1.5f;

// --- TYPES ---
enum Action { HIT = 0, STAND = 1, DOUBLE = 2, SPLIT = 3 };

struct Card {
    int value; // 2-10, 11 for Ace
    int countValue; // +1, 0, -1
};

struct Hand {
    std::vector<int> cards;
    int bet;
    bool isSoft;
    int total;
    bool isPair;
    bool surrendered;

    Hand(int initialBet) : bet(initialBet), isSoft(false), total(0), isPair(false), surrendered(false) {}

    void addCard(int cardVal) {
        cards.push_back(cardVal);
        update();
    }

    void update() {
        total = 0;
        int aces = 0;
        for (int c : cards) {
            total += c;
            if (c == 11) aces++;
        }
        while (total > 21 && aces > 0) {
            total -= 10;
            aces--;
        }
        isSoft = (aces > 0);
        isPair = (cards.size() == 2 && cards[0] == cards[1]);
    }
};

// --- GLOBAL STATE ---
std::vector<int> shoe;
int shoeIndex = 0;
int runningCount = 0;
std::mt19937 rng(42);

void initShoe() {
    shoe.clear();
    for (int d = 0; d < NUM_DECKS; ++d) {
        for (int s = 0; s < 4; ++s) {
            for (int r = 2; r <= 9; ++r) shoe.push_back(r);
            for (int r = 0; r < 4; ++r) shoe.push_back(10); // 10, J, Q, K
            shoe.push_back(11); // Ace
        }
    }
    std::shuffle(shoe.begin(), shoe.end(), rng);
    shoeIndex = 0;
    runningCount = 0;
}

int drawCard() {
    if (shoeIndex >= shoe.size() * 0.75) { // Reshuffle at 75% penetration
        initShoe();
    }
    int card = shoe[shoeIndex++];
    
    // Hi-Lo Counting
    if (card >= 2 && card <= 6) runningCount++;
    else if (card == 10 || card == 11) runningCount--;
    
    return card;
}

// --- POLICY LOOKUP ---
int getPolicyAction(const Hand& hand, int dealerUpCard) {
    // 1. Map Player Total
    int pIdx = hand.total;
    if (pIdx > 21) pIdx = 21; 

    // 2. Map Usable Ace
    int aceIdx = hand.isSoft ? 1 : 0;

    // 3. Map Dealer Card (2=0, ... 10=8, A=9)
    int dIdx = (dealerUpCard == 11) ? 9 : dealerUpCard - 2;

    // 4. Map True Count
    float decksRemaining = (shoe.size() - shoeIndex) / 52.0f;
    if (decksRemaining < 0.5f) decksRemaining = 0.5f;
    int trueCount = std::round(runningCount / decksRemaining);
    int cIdx = trueCount + 5; 
    if (cIdx < 0) cIdx = 0;
    if (cIdx > 11) cIdx = 11;

    // FETCH FROM YOUR HEADER
    int code = blackjack_policy[pIdx][aceIdx][dIdx][cIdx];

    // DECODE
    // 0=Hit, 1=Stand, 2=Double, 3=Stand
    // 30=Split/Hit, 31=Split/Stand, 32=Split/Double
    
    if (code >= 30) {
        if (hand.isPair) return SPLIT;
        // Fallback if not a pair
        if (code == 30) return HIT;
        if (code == 31) return STAND;
        if (code == 32) return DOUBLE;
    }

    if (code == 2) return DOUBLE;
    if (code == 1 || code == 3) return STAND;
    return HIT;
}

// --- GAMEPLAY ---
float playRound() {
    // Deal
    int p1 = drawCard();
    int d1 = drawCard(); // Dealer Up
    int p2 = drawCard();
    int d2 = drawCard(); // Dealer Hole

    // Check Dealer BJ
    bool dealerBJ = (d1 + d2 == 21 || (d1+d2==22 && d1==11)); // A+A=22->12, but if A=11 A=10 logic handled
    // Correct BJ check: 
    if (d1==11 && d2==10) dealerBJ = true;
    if (d1==10 && d2==11) dealerBJ = true;

    // Check Player BJ
    bool playerBJ = (p1==11 && p2==10) || (p1==10 && p2==11);

    if (dealerBJ && playerBJ) return 0.0f; // Push
    if (playerBJ) return BLACKJACK_PAYOUT;
    if (dealerBJ) return -1.0f;

    // Play Hands
    std::vector<Hand> hands;
    hands.emplace_back(1); // 1 unit bet
    hands[0].addCard(p1);
    hands[0].addCard(p2);

    float totalProfit = 0;

    for (size_t i = 0; i < hands.size(); ++i) {
        bool turnEnded = false;
        // Double check eligibility (only on 2 cards)
        bool canDouble = (hands[i].cards.size() == 2);
        
        while (!turnEnded) {
            if (hands[i].total >= 21) break;

            int action = getPolicyAction(hands[i], d1);
            
            // Validate Action vs Rules
            if (action == DOUBLE && !canDouble) action = HIT; 
            if (action == SPLIT && hands.size() >= 4) action = HIT; // Max 4 hands

            switch (action) {
                case HIT:
                    hands[i].addCard(drawCard());
                    canDouble = false;
                    break;
                case STAND:
                    turnEnded = true;
                    break;
                case DOUBLE:
                    hands[i].bet *= 2;
                    hands[i].addCard(drawCard());
                    turnEnded = true; // One card only
                    break;
                case SPLIT:
                    // Create new hand
                    Hand newHand(hands[i].bet);
                    int splitCard = hands[i].cards[1];
                    hands[i].cards.pop_back();
                    hands[i].addCard(drawCard()); // Hit split 1
                    
                    newHand.addCard(splitCard);
                    newHand.addCard(drawCard());  // Hit split 2
                    hands.push_back(newHand);
                    
                    // Re-eval current hand (it might be a pair again, or allow double)
                    canDouble = true; 
                    // Note: In strict rules, splitting Aces usually allows only 1 card.
                    // Simplified here to standard resplit/hit logic unless you want Ace restrictions.
                    if (splitCard == 11) {
                         turnEnded = true; 
                         hands.back().total = hands.back().total; // Force update?
                         // Flag next hand as done too if Ace
                         // Complex logic omitted for brevity, assuming Standard logic
                    }
                    break;
            }
        }
    }

    // Dealer Play
    Hand dealerHand(0);
    dealerHand.addCard(d1);
    dealerHand.addCard(d2);
    
    while (dealerHand.total < 17 || (HIT_SOFT_17 && dealerHand.total == 17 && dealerHand.isSoft)) {
        dealerHand.addCard(drawCard());
    }

    // Resolve
    for (auto& h : hands) {
        if (h.total > 21) {
            totalProfit -= h.bet;
        } else if (dealerHand.total > 21) {
            totalProfit += h.bet;
        } else if (h.total > dealerHand.total) {
            totalProfit += h.bet;
        } else if (h.total < dealerHand.total) {
            totalProfit -= h.bet;
        }
    }

    return totalProfit;
}

int main() {
    initShoe();
    
    double totalOutcome = 0;
    int wins = 0;
    int losses = 0;
    int pushes = 0;

    std::cout << "Simulating " << SIMULATION_HANDS << " hands..." << std::endl;

    for (int i = 0; i < SIMULATION_HANDS; ++i) {
        float result = playRound();
        totalOutcome += result;
        if (result > 0) wins++;
        else if (result < 0) losses++;
        else pushes++;

        if (i % 1000000 == 0 && i > 0) {
            std::cout << "Processed " << i << " hands. Current EV: " 
                      << (totalOutcome / (double)i) * 100.0 << "%" << std::endl;
        }
    }

    std::cout << "\n--- FINAL RESULTS ---" << std::endl;
    std::cout << "Total Hands: " << SIMULATION_HANDS << std::endl;
    std::cout << "Win Rate: " << (double)wins / SIMULATION_HANDS * 100.0 << "%" << std::endl;
    std::cout << "Loss Rate: " << (double)losses / SIMULATION_HANDS * 100.0 << "%" << std::endl;
    std::cout << "Push Rate: " << (double)pushes / SIMULATION_HANDS * 100.0 << "%" << std::endl;
    std::cout << "---------------------" << std::endl;
    std::cout << "EXPECTED VALUE (EV): " << (totalOutcome / SIMULATION_HANDS) * 100.0 << "%" << std::endl;

    if (totalOutcome < -0.005 * SIMULATION_HANDS) {
        std::cout << "Verdict: The house has the edge. (Normal for Blackjack)" << std::endl;
    } else if (totalOutcome > 0) {
        std::cout << "Verdict: YOU have the edge! (Your counting/policy is working)" << std::endl;
    }

    return 0;
}