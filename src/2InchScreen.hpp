#ifndef SCREEN_HPP
#define SCREEN_HPP

#include <vector>
#include "blackjack.hpp"

// Initializes the LCD screen, draws borders, labels, etc.
void screen_init();

// Draws the cards, counts, and action on the 2-inch display.
// Called from main.cpp when new cards are received.
void display_cards(
    Action action,
    std::vector<int> player_cards,
    std::vector<int> dealer_cards,
    int true_count,
    int winrate
);

#endif