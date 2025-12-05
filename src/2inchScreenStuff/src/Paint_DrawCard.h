#ifndef __Paint_DrawCard_H
#define __Paint_DrawCard_H

#include "DEV_Config.h"
#include "LCD_Driver.h"
#include "fonts.h"
#include "Debug.h"
#define PROGMEM
#define pgm_read_byte(addr) (*(const unsigned char *)(addr))

//card counts functions
void ChangeToString(int x, String *Scount);

//card symbols
void Paint_DrawDiamond(UWORD x, UWORD y, UWORD size, UWORD color);
void Paint_DrawHeart(UWORD centerX, UWORD centerY, int sizeLevel, UWORD color);
void Paint_DrawSpade(UWORD centerX, UWORD center1Y, int sizeLevel, UWORD color);
void Paint_DrawClub(UWORD centerX, UWORD centerY, int sizeLevel, UWORD color);

//card states
void Paint_DrawCardUp(UWORD x, UWORD y, int suit, int VALUE);
void Paint_DrawCardDown(UWORD centerX, UWORD centerY);
void Paint_DrawCardTopWhiteBrim(int x, int y);
void Paint_DrawCardBottomWhiteBrim(int x, int y);
void Paint_DrawMiddleCard(UWORD x, UWORD y);


#endif