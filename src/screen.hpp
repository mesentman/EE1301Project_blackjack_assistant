#ifndef SCREEN_HPP
#define SCREEN_HPP
#include "blackjack.hpp"

void lcd_init();
void display_scanning();
void display_action(Action action, int player_total);

#endif // SCREEN_HPP