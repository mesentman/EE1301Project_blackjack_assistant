#include "Particle.h"
// INSTALL - #include "Wire.h"
// INSTALL - #include "LiquidCrystal_I2C_Spark.h"

SYSTEM_THREAD(ENABLED);

// LCD setup (adjust address if screen stays blank)
LiquidCrystal_I2C lcd(0x27, 16, 2);

enum Action { HIT=0, STAND=1, DOUBLE=2, SURRENDER=3, SPLIT=4};

// Example Q-table (player_total 4–21, usable_ace 0/1, dealer 1–10)
Action policy_table[22][2][11];  

void initPolicyTable() {
    for (int pt = 4; pt <= 21; pt++) {
        for (int ua = 0; ua <= 1; ua++) {
            for (int dealer = 1; dealer <= 10; dealer++) {
                if (pt >= 17) policy_table[pt][ua][dealer] = STAND;
                else if (pt <= 11) policy_table[pt][ua][dealer] = HIT;
                else policy_table[pt][ua][dealer] = DOUBLE;
            }
        }
    }
}

// Display the selected action and count
void displayAction(Action a, int player_total) {
    lcd.clear();
    lcd.setCursor(0, 0);

    switch (a) {
        case HIT:        lcd.print("HIT"); break;
        case STAND:      lcd.print("STAND"); break;
        case DOUBLE:     lcd.print("DOUBLE"); break;
        case SURRENDER:  lcd.print("SURRENDER"); break;
        case SPLIT:      lcd.print("SPLIT"); break;
    }

    lcd.setCursor(0, 1);
    lcd.print("COUNT: ");
    lcd.print(player_total);
}

// Simulated sensor input
int player_total = 0;
bool usable_ace = false;
int dealer_upcard = 0;

Action getActionFromPolicy(int pt, bool ua, int dealer) {
    if (pt < 4) pt = 4;
    if (pt > 21) pt = 21;
    int u = ua ? 1 : 0;
    if (dealer < 1) dealer = 1;
    if (dealer > 10) dealer = 10;
    return policy_table[pt][u][dealer];
}

void setup() {
    Serial.begin(9600);
    Wire.begin();

    // Initialize LCD
    lcd.init();
    lcd.backlight();
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Blackjack Ready");
    delay(1500);
    lcd.clear();

    initPolicyTable();
}

void loop() {
    // Between rounds: scanning message
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("SCANNING CARDS...");
    delay(2000);

    // Example: simulated inputs
    player_total = 16;
    usable_ace = false;
    dealer_upcard = 10;

    // Determine and display action
    Action a = getActionFromPolicy(player_total, usable_ace, dealer_upcard);
    displayAction(a, player_total);

    // Debug info to serial
    Serial.printf("Player total: %d, usable ace: %d, Dealer: %d -> Action: %d\n",
                  player_total, usable_ace ? 1 : 0, dealer_upcard, (int)a);

    delay(5000);
}




//During scanning:

// Display Line1: SCANNING CARDS...





//When to HIT ex.

// Display Line1: HIT
// Display Line2: COUNT: 14