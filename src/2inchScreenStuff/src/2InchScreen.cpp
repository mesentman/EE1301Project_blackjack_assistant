#include "GUI_Paint.h"
#include "screen.hpp"
#include "2InchScreen.hpp"
#include "LCD_Driver.h"
#include "Paint_DrawCard.h" //personal header file for all the card drawing functions
#include "Particle.h"
#include "blackjack.hpp"
#include "fonts.h" // make sure your font file is included
// Screen Pinout
//   VCC -> 3V3
//   GND -> GND 
//   DIN -> S0(MO)
//   CLK -> S2(SCK)
//   CS -> S3
//   DC -> D2
//   RST -> D3
//   BL -> 3V3

SYSTEM_THREAD(ENABLED);

//******************************************************************************
// 🂱 Define suit constants
#define HEART 0
#define DIAMOND 1
#define CLUB 2
#define SPADE 3
// 🂡 Define rank constants
#define ACE 1
#define TWO 2
#define THREE 3
#define FOUR 4
#define FIVE 5
#define SIX 6
#define SEVEN 7
#define EIGHT 8
#define NINE 9
#define TEN 10
#define JACK 11
#define QUEEN 12
#define KING 13
//******************************************************************************




//  2	+1
//  3	+1
//  4	+1
//  5	+1
//  6	+1
//  7	0
//  8	0
//  9	0
//  10 -1 
//  J -1
//  Q -1
//  K	–1
//  A	–1







// if hit is true
// Paint_DrawString_EN(17, 75, "   HIT   ", &Font24, BLACK, RED);  //centered

// if stand is true
// Paint_DrawString_EN(17, 75, "  STAND  ", &Font24, BLACK, RED);

// if double is true
// Paint_DrawString_EN(25, 75, " DOUBLE  ", &Font24, BLACK, RED);

// if split is true
// Paint_DrawString_EN(17, 75, "  SPLIT  ", &Font24, BLACK, RED);

// if surrender is true
// Paint_DrawString_EN(17, 75, "SURRENDER", &Font24, BLACK, RED);

void screen_init() {
  SPI.begin();
  SPI.beginTransaction(SPISettings(25000000, MSBFIRST, SPI_MODE0));
  pinMode(DEV_CS_PIN, OUTPUT);
  pinMode(DEV_DC_PIN, OUTPUT);
  pinMode(DEV_RST_PIN, OUTPUT);

  LCD_Init();
  Paint_NewImage(LCD_WIDTH, LCD_HEIGHT, ROTATE_0, WHITE);
  Paint_Clear(BLACK);

  // Info table
  // setup----------------------------------------------------------------
  //---------- LINES SETUP ----------------
  Paint_DrawLine(5, 5, 315, 5, WHITE, DOT_PIXEL_2X2,
                 LINE_STYLE_SOLID); // top of big box
  Paint_DrawLine(180, 5, 180, 118, WHITE, DOT_PIXEL_1X1,
                 LINE_STYLE_SOLID); // small middle vert
  Paint_DrawLine(181, 63, 315, 63, WHITE, DOT_PIXEL_1X1,
                 LINE_STYLE_SOLID); // small middle hori
  Paint_DrawLine(5, 5, 5, 118, WHITE, DOT_PIXEL_2X2,
                 LINE_STYLE_SOLID); // side of big box
  Paint_DrawLine(315, 5, 315, 118, WHITE, DOT_PIXEL_2X2,
                 LINE_STYLE_SOLID); // side of big box
  Paint_DrawLine(5, 120, 315, 120, WHITE, DOT_PIXEL_2X2,
                 LINE_STYLE_SOLID); // bottom of big box
  //---------- LINES SETUP ----------------

  //---------- WORDS SETUP ----------------
  Paint_DrawString_EN(41, 15, "PLAYER", &Font24, BLACK, WHITE);  // centered
  Paint_DrawString_EN(41, 36, "SHOULD", &Font24, BLACK, WHITE);  // centered
  Paint_DrawString_EN(17, 75, "   ---   ", &Font24, BLACK, RED); // centered
  Paint_DrawString_EN(188, 10, "Run", &Font20, BLACK, WHITE);    // centered
  Paint_DrawString_EN(234, 10, "Count", &Font20, BLACK, WHITE);  // centered
  Paint_DrawString_EN(225, 34, "--", &Font24, BLACK, RED);      // centered
  Paint_DrawString_EN(196, 67, "Win", &Font20, BLACK, WHITE);    // centered
  Paint_DrawString_EN(242, 67, "Rate", &Font20, BLACK, WHITE);   // centered
  Paint_DrawString_EN(225, 91, "--", &Font24, BLACK, RED);      // centered
  //---------- WORDS SETUP ----------------
  // Info table
  // setup----------------------------------------------------------------

  // card table
  // setup----------------------------------------------------------------
  Paint_DrawLine(1, 125, 320, 125, RED, DOT_PIXEL_1X1, LINE_STYLE_SOLID);
  Paint_DrawString_EN(22, 130, "DEALER", &Font20, BLACK, WHITE); //          CENTERED
  Paint_DrawLine(129, 126, 129, 150, RED, DOT_PIXEL_1X1, LINE_STYLE_SOLID);
  Paint_DrawLine(1, 151, 320, 151, RED, DOT_PIXEL_1X1, LINE_STYLE_SOLID);
  Paint_DrawString_EN(130, 130, "--", &Font20, BLACK, WHITE);
  Paint_DrawString_EN(162, 130, "--", &Font20, BLACK, WHITE);
  Paint_DrawLine(191, 126, 191, 150, RED, DOT_PIXEL_1X1, LINE_STYLE_SOLID);
  Paint_DrawString_EN(213, 130, "PLAYER", &Font20, BLACK, WHITE); //        CENTERED
  Paint_DrawLine(1, 151, 320, 151, RED, DOT_PIXEL_1X1, LINE_STYLE_SOLID);
  Paint_DrawLine(160, 126, 160, 240, RED, DOT_PIXEL_2X2, LINE_STYLE_SOLID);
  // card table
  // setup----------------------------------------------------------------
}

int dealCardPositionDealer;
int suitDealer;
int valDealer;

int dealCardPositionPlayer;
int suitPlayer;
int valPlayer;



void display_cards(Action action, std::vector<int> player_cards, std::vector<int> dealer_cards, int true_count, int winrate) {
  bool runOnce = false;
  int dcs = 1;   // dealer card start
  int pcs = 162; // player card start
  int CSW = 19;  // card stack width

  int dealerCount = 0;
  int playerCount = 0;
  int trueCount = 0;
  String dealerScount;
  String playerScount;
  String winSrate;
  String trueScount;
  while (runOnce == false) {

    // clear card table first
    // output dealers
    // then players
    // then action






    //-------------- CLEAR TABLE -----------------
    Paint_DrawRectangle(1, 152, 158, 240, BLACK, DOT_PIXEL_1X1, DRAW_FILL_FULL);
    Paint_DrawRectangle(162, 152, 320, 240, BLACK, DOT_PIXEL_1X1, DRAW_FILL_FULL);
    Paint_DrawString_EN(130, 130, "--", &Font20, BLACK, WHITE);
    Paint_DrawString_EN(162, 130, "--", &Font20, BLACK, WHITE);
    //-------------- CLEAR TABLE -----------------










    //-------------- DEALER CARDS -----------------
    if (dealer_cards.size() >= 0) {
      dealCardPositionDealer = 0;
      for (size_t i = 0; i < dealer_cards.size(); i++) {

        suitDealer = 0;
        valDealer = (dealer_cards.at(i) % 13) + 1;

        if ((dealer_cards.at(i) / 13) == 1) {
          suitDealer = 0;
        } // Brocks int HEART to my int HEART
        if ((dealer_cards.at(i) / 13) == 2) {
          suitDealer = 1;
        } // Brocks int DIAMOND to my int DIAMOND
        if ((dealer_cards.at(i) / 13) == 3) {
          suitDealer = 2;
        } // Brocks int CLUB to my int CLUB
        if ((dealer_cards.at(i) / 13) == 0) {
          suitDealer = 3;
        } // Brocks int SPADE to my int SPADE

        //        draw dealer card
        Paint_DrawCardUp(dcs + (CSW * dealCardPositionDealer), 152, suitDealer, valDealer);

        //        draw dealer count
        switch (valDealer) {
        case 1:
          valDealer = 11;
          break;
        case 11:
          valDealer = 10;
          break;
        case 12:
          valDealer = 10;
          break;
        case 13:
          valDealer = 10;
          break;
        }

        if (valDealer >= 2 && valDealer <= 6) {
          trueCount++;
        }
        if (valDealer == 10 || valDealer == 11) {
          trueCount--;
        }

        dealerCount = dealerCount + valDealer;
        if ((dealerCount > 21) && valDealer == 11) {
          dealerCount = dealerCount - 10;
        }
        ChangeToString(
            dealerCount,
            &dealerScount); // check references and pointers if not working
        Paint_DrawString_EN(130, 130, dealerScount, &Font20, BLACK, WHITE); // Dealer count
        
        dealCardPositionDealer++;
      }
    }
    //-------------- DEALER CARDS -----------------











    //-------------- PLAYER CARDS -----------------
    if (player_cards.size() >= 0) {
      int dealCardPositionPlayer = 0;
      for (size_t i = 0; i < player_cards.size(); i++) {

        int valPlayer = (player_cards.at(i) % 13) + 1;

        if ((player_cards.at(i) / 13) == 1) {
          suitPlayer = 0;
        } // Brocks int HEART to my int HEART
        if ((player_cards.at(i) / 13) == 2) {
          suitPlayer = 1;
        } // Brocks int DIAMOND to my int DIAMOND
        if ((player_cards.at(i) / 13) == 3) {
          suitPlayer = 2;
        } // Brocks int CLUB to my int CLUB
        if ((player_cards.at(i) / 13) == 0) {
          suitPlayer = 3;
        } // Brocks int SPADE to my int SPADE

        //        draw player card
        Paint_DrawCardUp(pcs + (CSW * dealCardPositionPlayer), 152, suitPlayer, valPlayer);

        //        draw player count
        switch (valPlayer) {
        case 1:
          valPlayer = 11;
          break;
        case 11:
          valPlayer = 10;
          break;
        case 12:
          valPlayer = 10;
          break;
        case 13:
          valPlayer = 10;
          break;
        }

        if (valPlayer >= 2 && valPlayer <= 6) {
          trueCount++;
        }
        if (valPlayer == 10 || valPlayer == 11) {
          trueCount--;
        }

        playerCount = playerCount + valPlayer;
        if ((playerCount > 21) && valPlayer == 11) {
          playerCount = playerCount - 10;
        }
        ChangeToString(playerCount, &playerScount); // check references and pointers if not working
        Paint_DrawString_EN(162, 130, playerScount, &Font20, BLACK, WHITE); // Player count

        dealCardPositionPlayer++;
      }
    }
    //-------------- PLAYER CARDS -----------------








    //----------------- ACTION --------------------
    if ((action == HIT) || (action == STAND) || (action == DOUBLE_DOWN) ||
        (action == SPLIT)) {

      switch (action) {
      case HIT:
        Paint_DrawString_EN(17, 75, "   HIT   ", &Font24, BLACK, RED);
        break;
      case STAND:
        Paint_DrawString_EN(17, 75, "  STAND  ", &Font24, BLACK, RED);
        break;
      case DOUBLE_DOWN:
        Paint_DrawString_EN(17, 75, "         ", &Font24, BLACK,
                            RED); // clear previous area because double is
                                  // offset from others to be centered on screen
        Paint_DrawString_EN(25, 75, " DOUBLE  ", &Font24, BLACK, RED);
        break;
      case SPLIT:
        Paint_DrawString_EN(17, 75, "  SPLIT  ", &Font24, BLACK, RED);
        break;
      }
    } else {
      Paint_DrawString_EN(17, 75, "   ---   ", &Font24, BLACK, RED);
    }
    //----------------- ACTION --------------------








    //----------------- Run/True Count --------------------
      ChangeToString(trueCount, &trueScount);
      Paint_DrawString_EN(225, 34, "   ", &Font24, BLACK, RED);
      Paint_DrawString_EN(225, 34, trueScount, &Font24, BLACK, RED);
    //----------------- Run/True Count --------------------









    //----------------- Win Rate --------------------
    //if (winrate >= 0) {
      if (winrate == 100) {winrate = 99;}

      ChangeToString(winrate, &winSrate);
      Paint_DrawString_EN(225, 91, "   ", &Font24, BLACK, RED);
      Paint_DrawString_EN(225, 91, winSrate, &Font24, BLACK, RED);

    //}
    //else {Paint_DrawString_EN(225, 91, "---", &Font24, BLACK, RED);}
    //----------------- Win Rate --------------------


















    // Draw the counts on the screen
    // ChangeToString(dealerCount, &dealerScount); // check references and
    // pointers if not working ChangeToString(playerCount, &playerScount); //
    // check references and pointers if not working Paint_DrawString_EN(130,
    // 130, dealerScount, &Font20, BLACK, WHITE); // Dealer count
    // Paint_DrawString_EN(162, 130, playerScount, &Font20, BLACK, WHITE); //
    // Player count

    runOnce = true;
  }
}