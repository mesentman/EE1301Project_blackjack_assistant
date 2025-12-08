#include "GUI_Paint.h"
#include "DEV_Config.h"
#include "GUI_Paint.h"
#include "Paint_DrawCard.h"
#include <stdint.h>
#include <stdlib.h>
#include <string.h> //memset()
#include <math.h>



//sizes 1,2,3, for red diamonds (cards)
//ex. code
//Paint_DrawDiamond(80, 80, 1, RED);
void Paint_DrawDiamond(UWORD x, UWORD y0, UWORD size, UWORD color) {
    // Draw upper half (▲)
    int y = y0 + 2;
    for (int i = 0; i < 6 * size; i++) {
        Paint_DrawLine(
            x - i, y,               // left side starts at top
            x, y - i,               // top tip
            color, DOT_PIXEL_1X1, LINE_STYLE_SOLID
        );
        Paint_DrawLine(
            x + i, y,               // right side
            x, y - i,
            color, DOT_PIXEL_1X1, LINE_STYLE_SOLID
        );
    }

    // Draw lower half (▼)
    for (int i = 0; i < 6 * size; i++) {
        Paint_DrawLine(
            x - i, y,               // left side down
            x, y + i,
            color, DOT_PIXEL_1X1, LINE_STYLE_SOLID
        );
        Paint_DrawLine(
            x + i, y,               // right side down
            x, y + i,
            color, DOT_PIXEL_1X1, LINE_STYLE_SOLID
        );
    }
}


//sizes 1,2,3, for red hearts (cards)
//ex. code
//Paint_DrawHeart(80, 80, 1, RED);
void Paint_DrawHeart(UWORD centerX, UWORD centerY, int sizeLevel, UWORD color) {
    int radius, height;

    // 🎚️ Slightly smaller sizing
    switch (sizeLevel) {
        case 1:  // small
            radius = 3;   // reduced from 4
            height = 6;   // reduced proportionally
            break;
        case 2:  // medium
            radius = 5;   // reduced from 7
            height = 12;  // reduced proportionally
            break;
        case 3:  // large
            radius = 8;   // reduced from 10
            height = 16;  // reduced proportionally
            break;
        default:
            radius = 5;
            height = 12;
            break;
    }

    int leftCenterX  = centerX - radius;
    int rightCenterX = centerX + radius;
    int topY = centerY;
    int bottomY = centerY + height;
    int midX = centerX;

    // ❤️ Draw filled top semicircles
    auto drawFilledTopSemiCircle = [&](int cX, int cY, int r, UWORD col) {
        int16_t XCurrent = 0;
        int16_t YCurrent = r;
        int16_t Esp = 3 - (r << 1);
        while (XCurrent <= YCurrent) {
            for (int x = cX - YCurrent; x <= cX + YCurrent; x++) {
                Paint_DrawPoint(x, cY - XCurrent, col, DOT_PIXEL_1X1, DOT_STYLE_DFT);
            }
            for (int x = cX - XCurrent; x <= cX + XCurrent; x++) {
                Paint_DrawPoint(x, cY - YCurrent, col, DOT_PIXEL_1X1, DOT_STYLE_DFT);
            }
            if (Esp < 0)
                Esp += 4 * XCurrent + 6;
            else {
                Esp += 10 + 4 * (XCurrent - YCurrent);
                YCurrent--;
            }
            XCurrent++;
        }
    };

    drawFilledTopSemiCircle(leftCenterX, topY, radius, color);
    drawFilledTopSemiCircle(rightCenterX, topY, radius, color);

    // 🔻 Draw inverted triangle bottom half
    int halfWidth = (rightCenterX - leftCenterX) / 2 + radius;
    for (int y = topY; y <= bottomY; y++) {
        int width = map(y, topY, bottomY, halfWidth, 0);
        for (int x = midX - width; x <= midX + width; x++) {
            Paint_DrawPoint(x, y, color, DOT_PIXEL_1X1, DOT_STYLE_DFT);
        }
    }
}


//sizes 1,2,3, for black spades (cards)
//ex. code
//Paint_DrawSpade(80, 80, 1, BLACK);
void Paint_DrawSpade(UWORD centerX, UWORD center1Y, int sizeLevel, UWORD color) {
    int radius, height;

    // 🎚️ Slightly smaller sizing
    switch (sizeLevel) {
        case 1:  // small
            radius = 3;   
            height = 6;   
            break;
        case 2:  // medium
            radius = 5;   
            height = 12;  
            break;
        case 3:  // large
            radius = 8;   
            height = 16;  
            break;
        default:
            radius = 5;
            height = 12;
            break;
    }

    int centerY = center1Y - (height/2);
    int leftCenterX  = centerX - radius;
    int rightCenterX = centerX + radius;
    int topY = centerY;
    int bottomY = centerY + height;

    // 🔻 Draw inverted semicircles (curved side down)
    auto drawFilledBottomSemiCircle = [&](int cX, int cY, int r, UWORD col) {
        int16_t XCurrent = 0;
        int16_t YCurrent = r;
        int16_t Esp = 3 - (r << 1);
        while (XCurrent <= YCurrent) {
            for (int x = cX - YCurrent; x <= cX + YCurrent; x++) {
                Paint_DrawPoint(x, cY + XCurrent, col, DOT_PIXEL_1X1, DOT_STYLE_DFT);
            }
            for (int x = cX - XCurrent; x <= cX + XCurrent; x++) {
                Paint_DrawPoint(x, cY + YCurrent, col, DOT_PIXEL_1X1, DOT_STYLE_DFT);
            }
            if (Esp < 0)
                Esp += 4 * XCurrent + 6;
            else {
                Esp += 10 + 4 * (XCurrent - YCurrent);
                YCurrent--;
            }
            XCurrent++;
        }
    };

    drawFilledBottomSemiCircle(leftCenterX, bottomY, radius, color);
    drawFilledBottomSemiCircle(rightCenterX, bottomY, radius, color);

    // ▲ Draw upward triangle top half

    int baseY = topY + height;
    for (int y = 0; y <= height; y++) {
        int startX =  centerX - ((2*radius) - y);
        int endX = centerX + ((2*radius) - y);
        Paint_DrawLine(startX, baseY - y, endX, baseY  - y, color, DOT_PIXEL_1X1, LINE_STYLE_SOLID);
    }

    // ▲ Draw small upward triangle (stem)
    int stemBaseY = baseY + (2*radius);
    for (int y = 0; y <= (height + (0.5*radius)); y++) {
        int startX =  centerX - ((0.7*radius) - (y/2));
        int endX = centerX + ((0.7*radius) - (y/2));

        Paint_DrawLine(startX, stemBaseY - y, endX, stemBaseY  - y, color, DOT_PIXEL_1X1, LINE_STYLE_SOLID);
    }
}


//sizes 1,2,3, for black clubs (cards)
//ex. code
//Paint_DrawClub(80, 80, 1, BLACK);
void Paint_DrawClub(UWORD centerX, UWORD centerY, int sizeLevel, UWORD color) {
    int r;

    // Set radius based on size level
    switch(sizeLevel) {
        case 1: r = 3; break;   // small
        case 2: r = 5; break;   // medium
        case 3: r = 8; break;   // large
        default: r = 3; break;
    }

    int x = centerX;
    int y = centerY;

    // Top circle
    Paint_DrawCircle(x, y, r, color, DOT_PIXEL_1X1, DRAW_FILL_FULL);

    // Bottom-left circle
    Paint_DrawCircle(x - int(1.2 * r), y + int(1.6 * r), r, color, DOT_PIXEL_1X1, DRAW_FILL_FULL);

    // Bottom-right circle
    Paint_DrawCircle(x + int(1.2 * r), y + int(1.6 * r), r, color, DOT_PIXEL_1X1, DRAW_FILL_FULL);

    // Stem triangle
    int height = 2 * r;
    int baseY = y + r + height;
    for (int i = 0; i <= height; i++) {
        int startX = x - ((0.5 * r) - (i / 2));
        int endX   = x + ((0.5 * r) - (i / 2));
        Paint_DrawLine(startX, baseY - i, endX, baseY - i, color, DOT_PIXEL_1X1, LINE_STYLE_SOLID);
    }
}



//******************************************************************************
// 🂱 Define suit constants
#define HEART  0
#define DIAMOND 1
#define CLUB   2
#define SPADE  3
// 🂡 Define rank constants
#define ACE   1
#define TWO   2
#define THREE 3
#define FOUR  4
#define FIVE  5
#define SIX   6
#define SEVEN 7
#define EIGHT 8
#define NINE  9
#define TEN   10
#define JACK  11
#define QUEEN 12
#define KING  13
//******************************************************************************




//-----------------CARD DOWN STUFF--------------------------------------
// draw card down
//ex. code
//Paint_DrawCardDown(1, 152);
void Paint_DrawCardDown(UWORD centerX, UWORD centerY) {
  Paint_DrawCardTopWhiteBrim(centerX, centerY);
  Paint_DrawMiddleCard(centerX, centerY);
  Paint_DrawCardBottomWhiteBrim(centerX, centerY);
}
// draw card down
//ex. code
//Paint_DrawCardDown(1, 152);
void Paint_DrawCardTopWhiteBrim(int x, int y) {
  int w = 64;   // card width
  int r = 8;    // corner radius
  int r2 = r * r;
  int brimHeight = 4;  // height of top white band

  int x0 = x;
  int y0 = y;
  int x1 = x + w;
  int y1 = y + brimHeight;  // only top brim area

  for (int py = y0; py < y1; py++) {
    for (int px = x0; px < x1; px++) {
      bool inside = false;

      // Rounded corners logic
      if (px >= x0 + r && px < x1 - r) inside = true;
      else if (py >= y0 + r) inside = true; // below rounded arc
      else {
        int cx = (px < x0 + r) ? (x0 + r - 1) : (x1 - r);
        int cy = y0 + r - 1;
        int dx = px - cx;
        int dy = py - cy;
        if (dx * dx + dy * dy <= r2) inside = true;
      }

      if (inside) {
        Paint_DrawPoint(px, py, WHITE, DOT_PIXEL_1X1, DOT_STYLE_DFT);
      }
    }
  }
  Paint_DrawQuarterCircle((x+r-4+55), (y+r-4), r-4, 1, BLACK);  // top-right
  Paint_DrawLine((x+r-4), y, (x+r-4+55), y, BLACK, DOT_PIXEL_1X1, LINE_STYLE_SOLID);
  Paint_DrawQuarterCircle((x+r-4), (y+r-4), r-4, 2, BLACK);  // top-left
}
void Paint_DrawCardBottomWhiteBrim(int x, int y) {
  int w = 64;   // card width
  int h = 88;   // card height
  int r = 8;    // corner radius
  int r2 = r * r;
  int brimHeight = 4;  // height of bottom white band

  int x0 = x;
  int y0 = y + h - brimHeight + 1;  // start brim at bottom edge
  int x1 = x + w;
  int y1 = y + h;               // bottom of card

  for (int py = y0; py < y1; py++) {
    for (int px = x0; px < x1; px++) {
      bool inside = false;

      // Rounded corners logic for bottom edge
      if (px >= x0 + r && px < x1 - r) inside = true;
      else if (py <= y1 - r - 2) inside = true; // above rounded arc
      else {
        int cx = (px < x0 + r) ? (x0 + r - 1) : (x1 - r);
        int cy = y1 - r;
        int dx = px - cx;
        int dy = py - cy;
        if (dx * dx + dy * dy <= r2) inside = true;
      }

      if (inside) {
        Paint_DrawPoint(px, py, WHITE, DOT_PIXEL_1X1, DOT_STYLE_DFT);
      }
    }
  }

  // bottom border arcs and lines
  Paint_DrawQuarterCircle((x+r-4), (y+r-4+80), r-4, 3, BLACK);  // bottom-left
  Paint_DrawLine((x+r-4), (y+r+80), (x+r-4+55), (y+r+80), BLACK, DOT_PIXEL_1X1, LINE_STYLE_SOLID);
  Paint_DrawQuarterCircle((x+r-4+55), (y+r-4+80), r-4, 4, BLACK);  // bottom-right
}
void Paint_DrawMiddleCard(UWORD x, UWORD y) {
  int startY = y + 4;
  int innerH = 82;
  int innerW = 56;
  for (int y0 = 0; y0 < innerH; y0++) {
    Paint_DrawPoint(x, startY+y0, BLACK, DOT_PIXEL_1X1, DOT_STYLE_DFT);
    Paint_DrawLine(x+1, startY + y0, x+1+2, startY + y0, WHITE, DOT_PIXEL_1X1, LINE_STYLE_SOLID);
    Paint_DrawLine(x+1+2+1, startY + y0, x+1+2+1+innerW, startY + y0, RED, DOT_PIXEL_1X1, LINE_STYLE_SOLID);
    Paint_DrawLine(x+1+2+1+innerW, startY + y0, x+1+2+1+innerW+3, startY + y0, WHITE, DOT_PIXEL_1X1, LINE_STYLE_SOLID);
    Paint_DrawPoint(x+1+2+1+innerW+3, startY+y0, BLACK, DOT_PIXEL_1X1, DOT_STYLE_DFT);
  }
}
//-----------------CARD DOWN STUFF--------------------------------------








void Paint_DrawMiddleCardWhite(UWORD x, UWORD y) {
  int startY = y + 4;
  int innerH = 82;
  int innerW = 56;
  for (int y0 = 0; y0 < innerH; y0++) {
    Paint_DrawPoint(x, startY+y0, BLACK, DOT_PIXEL_1X1, DOT_STYLE_DFT);
    Paint_DrawLine(x+1, startY + y0, x+1+2, startY + y0, WHITE, DOT_PIXEL_1X1, LINE_STYLE_SOLID);
    Paint_DrawLine(x+1+2+1, startY + y0, x+1+2+1+innerW, startY + y0, WHITE, DOT_PIXEL_1X1, LINE_STYLE_SOLID);
    Paint_DrawLine(x+1+2+1+innerW, startY + y0, x+1+2+1+innerW+3, startY + y0, WHITE, DOT_PIXEL_1X1, LINE_STYLE_SOLID);
    Paint_DrawPoint(x+1+2+1+innerW+3, startY+y0, BLACK, DOT_PIXEL_1X1, DOT_STYLE_DFT);
  }
}



void Paint_DrawWhiteCardBack(UWORD centerX, UWORD centerY) {
  Paint_DrawCardTopWhiteBrim(centerX, centerY);
  Paint_DrawMiddleCardWhite(centerX, centerY);
  Paint_DrawCardBottomWhiteBrim(centerX, centerY);
}



//64unitsx88units
//Card up outline
//ex. code
//Paint_DrawCardUp(80, 80, HEART, KING);
void Paint_DrawCardUp(UWORD x, UWORD y, int suit, int VALUE) {
//(x,y) top left of card(not center point of radius) 
//card dimesnions 64x88, 8 radius corners
// Card size and radius
    const int cardW = 64;
    const int cardH = 88;

    // Draw white rounded rectangle (card)
    Paint_DrawWhiteCardBack(x, y);

    // Determine color based on suit
    UWORD color;
    if (suit == 0 || suit == 1) {
        color = RED;
    }
    else {
        color = BLACK;
    }

    // Symbol size (scaled down to fit card)
    int sizeLevel = 1;

    // Top-left position for suit symbol
    int topX = x + 14;
    int topY = y + 18;

    // Bottom-right position (mirrored)
    int bottomX = x + cardW - 14;
    int bottomY = y + cardH - 18;

    // Draw top-left symbol
    switch (suit) {
        case 0:
            Paint_DrawHeart(topX-5, topY+1, sizeLevel, color);
            break;
        case 1:
            Paint_DrawDiamond(topX-5, topY+1, sizeLevel, color);
            break;
        case 2:
            Paint_DrawClub(topX-5, topY+1, sizeLevel, color);
            break;
        case 3:
            Paint_DrawSpade(topX-5, topY+1, sizeLevel, color);
            break;
    }

    // Draw bottom-right symbol (mirrored upside-down)
    // Just reuse same function; small offset works well visually
    switch (suit) {
        case 0:
            Paint_DrawHeart(bottomX+3, bottomY+6, sizeLevel, color);
            break;
        case 1:
            Paint_DrawDiamond(bottomX+3, bottomY+6, sizeLevel, color);
            break;
        case 2:
            Paint_DrawClub(bottomX+3, bottomY+6, sizeLevel, color);
            break;
        case 3:
            Paint_DrawSpade(bottomX+3, bottomY+6, sizeLevel, color);
            break;
    }

    // --- Draw card VALUE ---

    if (VALUE == 10) {
        //top corner
        Paint_DrawString_EN(x, y + 3, "1", &Font16, WHITE, color);
        Paint_DrawString_EN(x + 7, y + 3, "0", &Font16, WHITE, color);


        // --- Draw large center value ---
        int centerX = x + cardW / 2 - (9);  // slight horizontal offset
        int centerY = y + cardH / 2 - 12; // vertical offset for balance
        Paint_DrawString_EN(centerX, centerY, "10", &Font24, WHITE, color);


        //bottom corner
        Paint_DrawString_EN(x + cardW - 20, y + cardH - 28, "1", &Font16, WHITE, color);
        Paint_DrawString_EN(x + cardW - 13, y + cardH - 28, "0", &Font16, WHITE, color);
    }


    else {
    // Convert VALUE (1–13) into text (A, 2–10, J, Q, K)
    char valueStr[3];
    switch (VALUE) {
        case 1:  strcpy(valueStr, "A"); break;
        case 11: strcpy(valueStr, "J"); break;
        case 12: strcpy(valueStr, "Q"); break;
        case 13: strcpy(valueStr, "K"); break;
        default: snprintf(valueStr, sizeof(valueStr), "%d", VALUE); break;
    }

    // Top-left value
    Paint_DrawString_EN(x + 3, y + 3, valueStr, &Font16, WHITE, color);
    // Bottom-right value (mirrored corner)
    Paint_DrawString_EN(x + cardW - 17, y + cardH - 28, valueStr, &Font16, WHITE, color);


    // --- Draw large center value ---
    int centerX = x + cardW / 2 - (9);  // slight horizontal offset
    int centerY = y + cardH / 2 - 12; // vertical offset for balance
    Paint_DrawString_EN(centerX, centerY, valueStr, &Font24, WHITE, color);
}
}



//change integer card count to string for display
void ChangeToString(int x, String *Scount) {
    
    switch(x) {
        case -1:  *Scount = "-1";  break;
        case -2:  *Scount = "-2";  break;
        case -3:  *Scount = "-3";  break;
        case -4:  *Scount = "-4";  break;
        case -5:  *Scount = "-5";  break;
        case -6:  *Scount = "-6";  break;
        case -7:  *Scount = "-7";  break;
        case -8:  *Scount = "-8";  break;
        case -9:  *Scount = "-9";  break;
        case -10: *Scount = "-10"; break;

        case -11: *Scount = "-11"; break;
        case -12: *Scount = "-12"; break;
        case -13: *Scount = "-13"; break;
        case -14: *Scount = "-14"; break;
        case -15: *Scount = "-15"; break;
        case -16: *Scount = "-16"; break;
        case -17: *Scount = "-17"; break;
        case -18: *Scount = "-18"; break;
        case -19: *Scount = "-19"; break;
        case -20: *Scount = "-20"; break;

        case 0:  *Scount = " 0"; break;
        case 1:  *Scount = " 1"; break;
        case 2:  *Scount = " 2"; break;
        case 3:  *Scount = " 3"; break;
        case 4:  *Scount = " 4"; break;
        case 5:  *Scount = " 5"; break;
        case 6:  *Scount = " 6"; break;
        case 7:  *Scount = " 7"; break;
        case 8:  *Scount = " 8"; break;
        case 9:  *Scount = " 9"; break;
        case 10: *Scount = "10"; break;

        case 11: *Scount = "11"; break;
        case 12: *Scount = "12"; break;
        case 13: *Scount = "13"; break;
        case 14: *Scount = "14"; break;
        case 15: *Scount = "15"; break;
        case 16: *Scount = "16"; break;
        case 17: *Scount = "17"; break;
        case 18: *Scount = "18"; break;
        case 19: *Scount = "19"; break;
        case 20: *Scount = "20"; break;

        case 21: *Scount = "21"; break;
        case 22: *Scount = "22"; break;
        case 23: *Scount = "23"; break;
        case 24: *Scount = "24"; break;
        case 25: *Scount = "25"; break;
        case 26: *Scount = "26"; break;
        case 27: *Scount = "27"; break;
        case 28: *Scount = "28"; break;
        case 29: *Scount = "29"; break;
        case 30: *Scount = "30"; break;

        case 31: *Scount = "31"; break;
        case 32: *Scount = "32"; break;
        case 33: *Scount = "33"; break;
        case 34: *Scount = "34"; break;
        case 35: *Scount = "35"; break;
        case 36: *Scount = "36"; break;
        case 37: *Scount = "37"; break;
        case 38: *Scount = "38"; break;
        case 39: *Scount = "39"; break;
        case 40: *Scount = "40"; break;

        case 41: *Scount = "41"; break;
        case 42: *Scount = "42"; break;
        case 43: *Scount = "43"; break;
        case 44: *Scount = "44"; break;
        case 45: *Scount = "45"; break;
        case 46: *Scount = "46"; break;
        case 47: *Scount = "47"; break;
        case 48: *Scount = "48"; break;
        case 49: *Scount = "49"; break;
        case 50: *Scount = "50"; break;

        case 51: *Scount = "51"; break;
        case 52: *Scount = "52"; break;
        case 53: *Scount = "53"; break;
        case 54: *Scount = "54"; break;
        case 55: *Scount = "55"; break;
        case 56: *Scount = "56"; break;
        case 57: *Scount = "57"; break;
        case 58: *Scount = "58"; break;
        case 59: *Scount = "59"; break;
        case 60: *Scount = "60"; break;

        case 61: *Scount = "61"; break;
        case 62: *Scount = "62"; break;
        case 63: *Scount = "63"; break;
        case 64: *Scount = "64"; break;
        case 65: *Scount = "65"; break;
        case 66: *Scount = "66"; break;
        case 67: *Scount = "67"; break;
        case 68: *Scount = "68"; break;
        case 69: *Scount = "69"; break;
        case 70: *Scount = "70"; break;

        case 71: *Scount = "71"; break;
        case 72: *Scount = "72"; break;
        case 73: *Scount = "73"; break;
        case 74: *Scount = "74"; break;
        case 75: *Scount = "75"; break;
        case 76: *Scount = "76"; break;
        case 77: *Scount = "77"; break;
        case 78: *Scount = "78"; break;
        case 79: *Scount = "79"; break;
        case 80: *Scount = "80"; break;

        case 81: *Scount = "81"; break;
        case 82: *Scount = "82"; break;
        case 83: *Scount = "83"; break;
        case 84: *Scount = "84"; break;
        case 85: *Scount = "85"; break;
        case 86: *Scount = "86"; break;
        case 87: *Scount = "87"; break;
        case 88: *Scount = "88"; break;
        case 89: *Scount = "89"; break;
        case 90: *Scount = "90"; break;

        case 91: *Scount = "91"; break;
        case 92: *Scount = "92"; break;
        case 93: *Scount = "93"; break;
        case 94: *Scount = "94"; break;
        case 95: *Scount = "95"; break;
        case 96: *Scount = "96"; break;
        case 97: *Scount = "97"; break;
        case 98: *Scount = "98"; break;
        case 99: *Scount = "99"; break;
        case 100: *Scount = "99"; break;

        default:
            *Scount = "--";
            break;
    }
}





// change integer to string WITH % sign for display
void ChangeToStringPercent(int x, String *Scount) {
    switch(x) {
        // ----- 0 -----
        case 0:   *Scount = " 0%";   break;
        case 1:   *Scount = " 1%";   break;
        case 2:   *Scount = " 2%";   break;
        case 3:   *Scount = " 3%";   break;
        case 4:   *Scount = " 4%";   break;
        case 5:   *Scount = " 5%";   break;
        case 6:   *Scount = " 6%";   break;
        case 7:   *Scount = " 7%";   break;
        case 8:   *Scount = " 8%";   break;
        case 9:   *Scount = " 9%";   break;
        case 10:  *Scount = "10%";  break;

        case 11:  *Scount = "11%";  break;
        case 12:  *Scount = "12%";  break;
        case 13:  *Scount = "13%";  break;
        case 14:  *Scount = "14%";  break;
        case 15:  *Scount = "15%";  break;
        case 16:  *Scount = "16%";  break;
        case 17:  *Scount = "17%";  break;
        case 18:  *Scount = "18%";  break;
        case 19:  *Scount = "19%";  break;
        case 20:  *Scount = "20%";  break;

        case 21:  *Scount = "21%";  break;
        case 22:  *Scount = "22%";  break;
        case 23:  *Scount = "23%";  break;
        case 24:  *Scount = "24%";  break;
        case 25:  *Scount = "25%";  break;
        case 26:  *Scount = "26%";  break;
        case 27:  *Scount = "27%";  break;
        case 28:  *Scount = "28%";  break;
        case 29:  *Scount = "29%";  break;
        case 30:  *Scount = "30%";  break;

        case 31: *Scount = "31%"; break;
        case 32: *Scount = "32%"; break;
        case 33: *Scount = "33%"; break;
        case 34: *Scount = "34%"; break;
        case 35: *Scount = "35%"; break;
        case 36: *Scount = "36%"; break;
        case 37: *Scount = "37%"; break;
        case 38: *Scount = "38%"; break;
        case 39: *Scount = "39%"; break;
        case 40: *Scount = "40%"; break;

        case 41: *Scount = "41%"; break;
        case 42: *Scount = "42%"; break;
        case 43: *Scount = "43%"; break;
        case 44: *Scount = "44%"; break;
        case 45: *Scount = "45%"; break;
        case 46: *Scount = "46%"; break;
        case 47: *Scount = "47%"; break;
        case 48: *Scount = "48%"; break;
        case 49: *Scount = "49%"; break;
        case 50: *Scount = "50%"; break;

        case 51: *Scount = "51%"; break;
        case 52: *Scount = "52%"; break;
        case 53: *Scount = "53%"; break;
        case 54: *Scount = "54%"; break;
        case 55: *Scount = "55%"; break;
        case 56: *Scount = "56%"; break;
        case 57: *Scount = "57%"; break;
        case 58: *Scount = "58%"; break;
        case 59: *Scount = "59%"; break;
        case 60: *Scount = "60%"; break;

        case 61: *Scount = "61%"; break;
        case 62: *Scount = "62%"; break;
        case 63: *Scount = "63%"; break;
        case 64: *Scount = "64%"; break;
        case 65: *Scount = "65%"; break;
        case 66: *Scount = "66%"; break;
        case 67: *Scount = "67%"; break;
        case 68: *Scount = "68%"; break;
        case 69: *Scount = "69%"; break;
        case 70: *Scount = "70%"; break;

        case 71: *Scount = "71%"; break;
        case 72: *Scount = "72%"; break;
        case 73: *Scount = "73%"; break;
        case 74: *Scount = "74%"; break;
        case 75: *Scount = "75%"; break;
        case 76: *Scount = "76%"; break;
        case 77: *Scount = "77%"; break;
        case 78: *Scount = "78%"; break;
        case 79: *Scount = "79%"; break;
        case 80: *Scount = "80%"; break;

        case 81: *Scount = "81%"; break;
        case 82: *Scount = "82%"; break;
        case 83: *Scount = "83%"; break;
        case 84: *Scount = "84%"; break;
        case 85: *Scount = "85%"; break;
        case 86: *Scount = "86%"; break;
        case 87: *Scount = "87%"; break;
        case 88: *Scount = "88%"; break;
        case 89: *Scount = "89%"; break;
        case 90: *Scount = "90%"; break;

        case 91: *Scount = "91%"; break;
        case 92: *Scount = "92%"; break;
        case 93: *Scount = "93%"; break;
        case 94: *Scount = "94%"; break;
        case 95: *Scount = "95%"; break;
        case 96: *Scount = "96%"; break;
        case 97: *Scount = "97%"; break;
        case 98: *Scount = "98%"; break;
        case 99: *Scount = "99%"; break;

        default:
            *Scount = "---";
            break;
    }
}