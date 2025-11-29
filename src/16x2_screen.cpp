#include "blackjack.hpp"
#include <Particle.h>
#include <Wire.h>

// ST7032 default I2C address
#define LCD_ADDR 0x3E

void lcd_command(uint8_t cmd) { // LCD function -- AI
  Wire.beginTransmission(LCD_ADDR);
  Wire.write(0x00); // Control byte: Co = 0, RS = 0
  Wire.write(cmd);
  Wire.endTransmission();
}

void lcd_data(uint8_t data) { // LCD function -- AI
  Wire.beginTransmission(LCD_ADDR);
  Wire.write(0x40); // Control byte: Co = 0, RS = 1
  Wire.write(data);
  Wire.endTransmission();
}

void lcd_clear() { lcd_command(0x01); }

void lcd_init() { // LCD function -- AI
  Wire.begin();
  delay(50);
  lcd_command(0x38);        // Function set: 8-bit, 2 line, normal instruction
  lcd_command(0x39);        // Function set: extended instruction
  lcd_command(0x14);        // Bias set
  lcd_command(0x70 | 0x0A); // Contrast set (lower 4 bits)
  lcd_command(0x5C);        // Power/icon/contrast control
  lcd_command(0x6C);        // Follower control
  delay(200);
  lcd_command(0x38); // Function set: normal instruction
  lcd_command(0x0C); // Display ON, cursor OFF, blink OFF
  lcd_clear();
  delay(2);
}

void lcd_set_cursor(uint8_t col, uint8_t row) { // LCD function -- AI
  const uint8_t row_offsets[] = {0x00, 0x40};
  lcd_command(0x80 | (col + row_offsets[row]));
}

void lcd_print(const char *str) { // LCD function -- AI
  while (*str) {
    lcd_data(*str++);
  }
}

void display_scanning() {
  delay(5); // Give LCD time to clear fully

  lcd_set_cursor(0, 0);
  lcd_print("SCANNING");
  lcd_set_cursor(0, 1);
  lcd_print("CARDS");

  // Animate the dots with instant response
  for (int j = 0; j < 4; j++) {
    lcd_set_cursor(5, 1); // start after "CARDS"

    // Print j dots
    for (int k = 0; k < j; k++) {
      lcd_print(".");
    }
    delay(500);

    // Erase dots before next cycle
    lcd_set_cursor(5, 1);
    lcd_print("   ");
  }
}

void display_action(Action action, int player_total) {
  char buffer[16]; // converts numCount into a char so LCD can print it
  lcd_clear();
  lcd_set_cursor(0, 0);
  switch (action) {
  case HIT:
    lcd_print("HIT");
    break;
  case STAND:
    lcd_print("STAND");
    break;
  case DOUBLE_DOWN:
    lcd_print("DOUBLE");
    break;
  case SPLIT:
    lcd_print("SPLIT");
    break;
  case SURRENDER:
    lcd_print("SURRENDER");
    break;
  }
  lcd_set_cursor(0, 1);
  sprintf(buffer, "Count: %d", player_total);
  lcd_print(buffer);
}