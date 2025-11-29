#include "Particle.h"
#include "blackjack.hpp"
#include "screen.hpp"

SYSTEM_MODE(AUTOMATIC);
SerialLogHandler logHandler(LOG_LEVEL_INFO);

Action getActionFromTable(int player_total, bool useable_ace, int dealer_upcard,
                          int true_count) {
  if (player_total < 0) {
    player_total = 0;
  } else if (player_total > 21) {
    player_total = 21;
  }
  int ace = useable_ace ? 1 : 0;
  if (dealer_upcard < 0) {
    dealer_upcard = 0;
  } else if (dealer_upcard > 9) {
    dealer_upcard = 9;
  }
  true_count += 5; // Change into an index in the table
  if (true_count < 0) {
    true_count = 0;
  } else if (true_count > 11) {
    true_count = 11;
  }
  int ret = blackjack_policy[player_total][ace][dealer_upcard][true_count];
  return HIT;
}

void setup() {
  Serial.begin(9600);
  lcd_init();
}

void loop() {
  int player_total = 16;
  bool usable_ace = false;
  int dealer_upcard = 10;
  int true_count = 0;

  Action action =
      getActionFromTable(player_total, usable_ace, dealer_upcard, true_count);
  display_action(action, player_total);

  Serial.printf("Player total: %d, usable ace: %d, Dealer: %d -> Action: %d\n",
                player_total, usable_ace ? 1 : 0, dealer_upcard, (int)action);

  delay(5000);
}
