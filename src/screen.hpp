#ifndef SCREEN_HPP
#define SCREEN_HPP
#include "blackjack.hpp"

void lcd_init();
void screen_init();
void display_scanning();
void display_action(Action action, int player_total);
void display_cards(Action action, std::vector<int> player_cards,
                   std::vector<int> dealer_cards, int true_count, int winrate);

#endif // SCREEN_HPP