#include "Particle.h"
#include "LCD_Driver.h"
#include "GUI_Paint.h"
#include "Paint_DrawCard.h" //personal header file for all the card drawing functions
#include "Fonts.h"   // make sure your font file is included


//Screen Pinout
//  VCC -> 3V3 
//  GND -> GND 
//  DIN -> S0(MO) 
//  CLK -> S2(SCK) 
//  CS -> S3 
//  DC -> D2 
//  RST -> D3 
//  BL -> 3V3


SYSTEM_THREAD(ENABLED);

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

int dealerCount = 0;
int playerCount = 0;
String dealerScount; 
String playerScount;



    // if hit is true
    //Paint_DrawString_EN(17, 75, "   HIT   ", &Font24, BLACK, RED);  //centered

    // if stand is true
    //Paint_DrawString_EN(17, 70, "  STAND  ", &Font24, BLACK, RED);

    // if double is true
    //Paint_DrawString_EN(25, 70, " DOUBLE  ", &Font24, BLACK, RED);

    // if split is true
    //Paint_DrawString_EN(17, 70, "  SPLIT  ", &Font24, BLACK, RED);

    // if surrender is true
    //Paint_DrawString_EN(17, 70, "SURRENDER", &Font24, BLACK, RED);




void screenSetup () {
    SPI.begin();
    SPI.beginTransaction(SPISettings(25000000, MSBFIRST, SPI_MODE0));
    pinMode(DEV_CS_PIN, OUTPUT);
    pinMode(DEV_DC_PIN, OUTPUT);
    pinMode(DEV_RST_PIN, OUTPUT);

    LCD_Init();
    Paint_NewImage(LCD_WIDTH, LCD_HEIGHT, ROTATE_0, WHITE);
    Paint_Clear(BLACK);

    






    //Info table setup----------------------------------------------------------------
    //---------- LINES SETUP ----------------
    Paint_DrawLine(5, 5, 315, 5, WHITE, DOT_PIXEL_2X2, LINE_STYLE_SOLID);       //top of big box
    Paint_DrawLine(180, 5, 180, 118, WHITE, DOT_PIXEL_1X1, LINE_STYLE_SOLID); //small middle vert
    Paint_DrawLine(181, 63, 315, 63, WHITE, DOT_PIXEL_1X1, LINE_STYLE_SOLID); //small middle hori
    Paint_DrawLine(5, 5, 5, 118, WHITE, DOT_PIXEL_2X2, LINE_STYLE_SOLID);       //side of big box
    Paint_DrawLine(315, 5, 315, 118, WHITE, DOT_PIXEL_2X2, LINE_STYLE_SOLID);   //side of big box
    Paint_DrawLine(5, 120, 315, 120, WHITE, DOT_PIXEL_2X2, LINE_STYLE_SOLID);   //bottom of big box
    //---------- LINES SETUP ----------------

    //---------- WORDS SETUP ----------------
    Paint_DrawString_EN(41, 15, "PLAYER", &Font24, BLACK, WHITE);   //centered
    Paint_DrawString_EN(41, 36, "SHOULD", &Font24, BLACK, WHITE);   //centered
    Paint_DrawString_EN(17, 75, "   ---   ", &Font24, BLACK, RED);  //centered
    Paint_DrawString_EN(188, 10, "Run", &Font20, BLACK, WHITE); // centered
    Paint_DrawString_EN(234, 10, "Count", &Font20, BLACK, WHITE); // centered
    Paint_DrawString_EN(225, 34, "---", &Font24, BLACK, RED); // centered
    Paint_DrawString_EN(196, 67, "Win", &Font20, BLACK, WHITE); // centered
    Paint_DrawString_EN(242, 67, "Rate", &Font20, BLACK, WHITE); // centered
    Paint_DrawString_EN(225, 91, "---", &Font24, BLACK, RED); // centered
    //---------- WORDS SETUP ----------------
    //Info table setup----------------------------------------------------------------


    //card table setup----------------------------------------------------------------
    Paint_DrawLine(1, 125, 320, 125, RED, DOT_PIXEL_1X1, LINE_STYLE_SOLID);
    Paint_DrawString_EN(22, 130, "DEALER", &Font20, BLACK, WHITE);//          CENTERED
    Paint_DrawLine(129, 126, 129, 150, RED, DOT_PIXEL_1X1, LINE_STYLE_SOLID);
    Paint_DrawLine(1, 151, 320, 151, RED, DOT_PIXEL_1X1, LINE_STYLE_SOLID);
    Paint_DrawString_EN(130, 130, "--", &Font20, BLACK, WHITE);
    Paint_DrawString_EN(162, 130, "--", &Font20, BLACK, WHITE);
    Paint_DrawLine(191, 126, 191, 150, RED, DOT_PIXEL_1X1, LINE_STYLE_SOLID);
    Paint_DrawString_EN(213, 130, "PLAYER", &Font20, BLACK, WHITE);//        CENTERED
    Paint_DrawLine(1, 151, 320, 151, RED, DOT_PIXEL_1X1, LINE_STYLE_SOLID);
    Paint_DrawLine(160, 126, 160, 240, RED, DOT_PIXEL_2X2, LINE_STYLE_SOLID);
    //card table setup----------------------------------------------------------------

}


// change for running cards code on screen
bool runOnce = false;
// change for running cards code on screen



int dcs = 1; //dealer card pixel start
int pcs = 162; //player card pixel start
int CSW = 19; //card stack pixel width
void screenLOOP() {

    while (runOnce == false) {







        //DEALER CARDS-----------
        Paint_DrawCardUp(dcs, 152, 0, 1);           // Ace of Hearts
        Paint_DrawCardUp(dcs + CSW, 152, 2, 1);     // Ace of Clubs
        Paint_DrawCardUp(dcs + CSW*2, 152, 1, 1);   // Ace of Diamonds
        Paint_DrawCardUp(dcs + CSW*3, 152, 3, 1);   // Ace of Spades
        Paint_DrawCardUp(dcs + CSW*4, 152, 2, 8);   // Ace of Spades
        Paint_DrawCardDown(dcs + CSW*5, 152);       // waiting for player action
        //DEALER CARDS-----------

        //PLAYER CARDS-----------
        Paint_DrawCardUp(pcs, 152, 0, 1);           // Ace of Hearts
        Paint_DrawCardUp(pcs + CSW, 152, 2, 1);     // Ace of Clubs
        Paint_DrawCardUp(pcs + CSW*2, 152, 1, 1);   // Ace of Diamonds
        Paint_DrawCardUp(pcs + CSW*3, 152, 3, 1);   // Ace of Spades
        Paint_DrawCardUp(pcs + CSW*4, 152, 2, 8);   // Ace of Spades
        Paint_DrawCardDown(pcs + CSW*5, 152);       // waiting for player action
        //PLAYER CARDS-----------       
        
        

        // Draw the counts on the screen
        ChangeToString(dealerCount, &dealerScount); //check references and pointers if not working
        ChangeToString(playerCount, &playerScount); //check references and pointers if not working
        Paint_DrawString_EN(130, 130, dealerScount, &Font20, BLACK, WHITE); // Dealer count
        Paint_DrawString_EN(162, 130, playerScount, &Font20, BLACK, WHITE); // Player count
        
    runOnce = true;
    }

}