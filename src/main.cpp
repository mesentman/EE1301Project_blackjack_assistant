#include "Particle.h"
#include "blackjack.hpp"
#include "screen.hpp"
#include <vector>

SYSTEM_MODE(AUTOMATIC);
SerialLogHandler log_handler(LOG_LEVEL_INFO);

std::vector<int> player_cards;
std::vector<int> dealer_cards;
bool new_hand = false;

int get_card_value(int card) {
  int rank = card % 13;
  if (rank == 0)
    return 11; // Ace
  if (rank >= 9)
    return 10;     // 10, J, Q, K
  return rank + 1; // 2-9
}

int get_hi_lo_count(int card) {
  int rank = card % 13;
  if (rank >= 9 || rank == 0)
    return -1; // 10, J, Q, K, A
  if (rank >= 1 && rank <= 5)
    return 1; // 2-6
  return 0;   // 7-9
}

void parse_card_list(String data, std::vector<int> &out) {
  out.clear();
  data.trim();
  if (data.length() == 0)
    return;

  int pos = 0;
  while (pos < (int)data.length()) {
    int comma_pos = data.indexOf(',', pos);
    String card_str;
    if (comma_pos == -1) {
      card_str = data.substring(pos);
      pos = data.length();
    } else {
      card_str = data.substring(pos, comma_pos);
      pos = comma_pos + 1;
    }
    card_str.trim();
    if (card_str.length() > 0) {
      out.push_back(card_str.toInt());
    }
  }
}

int receive_cards(String data) {
  data.trim();
  if (data.length() == 0)
    return 0;

  int separator_pos = data.indexOf('|');
  String player_data;
  String dealer_data;

  if (separator_pos == -1) {
    player_data = data;
    dealer_data = "";
  } else {
    player_data = data.substring(0, separator_pos);
    dealer_data = data.substring(separator_pos + 1);
  }

  parse_card_list(player_data, player_cards);
  parse_card_list(dealer_data, dealer_cards);

  Log.info("Player cards: %d, Dealer cards: %d", player_cards.size(),
           dealer_cards.size());
  for (int card : player_cards) {
    Log.info("Player card: %d (value: %d)", card, get_card_value(card));
  }
  for (int card : dealer_cards) {
    Log.info("Dealer card: %d (value: %d)", card, get_card_value(card));
  }

  new_hand = true;
  return player_cards.size() + dealer_cards.size();
}

Action get_action_from_table(int player_total, bool useable_ace,
                             int dealer_upcard, int true_count) {
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
  return HIT; // TODO: Change to reflect table output
}

void setup() {
  Serial.begin(9600);
  lcd_init();
  Particle.function("receive_cards", receive_cards);
  display_scanning();
}

int true_count = 0;

void loop() {
  if (new_hand) {
    int player_total = 0;
    int ace_count = 0;
    for (int card : player_cards) {
      player_total += get_card_value(card);
      if (card % 13 == 0)
        ace_count++;
    }
    while (player_total > 21 && ace_count > 0) {
      player_total -= 10;
      ace_count--;
    }
    bool usable_ace = ace_count > 0 && player_total <= 21;

    int dealer_upcard = 0;
    if (!dealer_cards.empty()) {
      dealer_upcard = get_card_value(dealer_cards[0]);
    }

    for (int card : player_cards) {
      true_count += get_hi_lo_count(card);
    }
    for (int card : dealer_cards) {
      true_count += get_hi_lo_count(card);
    }

    Action action = get_action_from_table(player_total, usable_ace,
                                          dealer_upcard, true_count);
    display_action(action, player_total);

    Serial.printf(
        "Player total: %d, usable ace: %d, Dealer: %d -> Action: %d\n",
        player_total, usable_ace ? 1 : 0, dealer_upcard, (int)action);
    new_hand = false;
  }
  delay(500);
}
