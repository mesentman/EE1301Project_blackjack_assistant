// LCD_2inch.cpp
#include "LCD_2inch.h"

// Image buffer
UBYTE image_buffer[LCD_WIDTH * LCD_HEIGHT * 2];

void LCD_Init_Display() {
    // Initialize SPI & GPIO
    Config_Init();  

    // Initialize LCD
    LCD_Init();
  

    // Prepare image buffer
    Paint_NewImage(LCD_WIDTH, LCD_HEIGHT, ROTATE_0, WHITE);
    Paint_Clear(WHITE);
    Paint_SetRotate(ROTATE_0);
    Paint_SetMirroring(MIRROR_NONE);
}

void LCD_UpdateTime(PAINT_TIME* currentTime) {
    static uint32_t lastUpdate = 0;
    if (millis() - lastUpdate > 1000) {
        lastUpdate = millis();

        // Increment seconds
        currentTime->Sec++;
        if (currentTime->Sec >= 60) { currentTime->Sec = 0; currentTime->Min++; }
        if (currentTime->Min >= 60) { currentTime->Min = 0; currentTime->Hour++; }
        if (currentTime->Hour >= 24) { currentTime->Hour = 0; }

        // Clear time area
        Paint_ClearWindows(10, 100, 150, 120, WHITE);

        // Draw updated time
        Paint_DrawTime(10, 100, currentTime, &Font16, WHITE, BLACK);
    }
}