#include "LiquidCrystal_I2C_Spark.h"
#include "Particle.h"
#include "Wire.h"
#include "blackjack.hpp"

// LCD setup (adjust address if screen stays blank)
LiquidCrystal_I2C lcd(0x27, 16, 2);

void init_screen() {
  Wire.begin();

  // Initialize LCD
  lcd.init();
  lcd.backlight();
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Blackjack Ready");
  delay(1500);
  lcd.clear();
}

void print_scanning() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("SCANNING CARDS...");
}

void print_action(Action action, int player_total) {
  lcd.clear();
  lcd.setCursor(0, 0);

  switch (action) {
  case HIT:
    lcd.print("HIT");
    break;
  case STAND:
    lcd.print("STAND");
    break;
  case DOUBLE_DOWN:
    lcd.print("DOUBLE");
    break;
  case SURRENDER:
    lcd.print("SURRENDER");
    break;
  case SPLIT:
    lcd.print("SPLIT");
    break;
  }

  lcd.setCursor(0, 1);
  lcd.print("COUNT: ");
  lcd.print(player_total);
}