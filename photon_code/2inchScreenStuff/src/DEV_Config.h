#ifndef _DEV_CONFIG_H_
#define _DEV_CONFIG_H_

#include <stdint.h>
#include <SPI.h>
#include "Debug.h"

#define UBYTE   uint8_t
#define UWORD   uint16_t
#define UDOUBLE uint32_t

// Pin mapping
#define DEV_CS_PIN   S3   // Chip select
#define DEV_DC_PIN   D2   // Data/Command
#define DEV_RST_PIN  D3   // Reset
#define DEV_BL_PIN   -1   // Backlight pin not used; tied to 3.3V

// GPIO read and write
#define DEV_Digital_Write(_pin, _value) digitalWrite(_pin, _value == 0 ? LOW : HIGH)
#define DEV_Digital_Read(_pin) digitalRead(_pin)

// SPI
#define DEV_SPI_WRITE(_dat)   SPI.transfer(_dat)

// delay x ms
#define DEV_Delay_ms(__xms)    delay(__xms)

// PWM_BL (not used because backlight is tied to 3.3V)
#define DEV_Set_PWM(_Value)    // nothing

void Config_Init();

#endif