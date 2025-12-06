#ifndef __2InchScreen_H
#define __2InchScreen_H

#include "DEV_Config.h"
#include "blackjack.hpp"
#include "win_rate_table.h"
#include "LCD_Driver.h"
#include "Paint_DrawCard.h"
#include "GUI_Paint.h"
#include "fonts.h"
#include "Debug.h"
#define PROGMEM
#define pgm_read_byte(addr) (*(const unsigned char *)(addr))

void screen_init();
void display_cards(Action action, std::vector<int> player_cards, std::vector<int> dealer_cards, int true_count, int winrate);




#endif