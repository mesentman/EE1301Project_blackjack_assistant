// LCD_2inch.h
#pragma once
#include "Particle.h"
#include "LCD_Driver.h"
#include "GUI_Paint.h"
#include "fonts.h"
#include "DEV_Config.h"

// Initialize LCD and image buffer
void LCD_Init_Display();

// Update the time display
void LCD_UpdateTime(PAINT_TIME* currentTime);