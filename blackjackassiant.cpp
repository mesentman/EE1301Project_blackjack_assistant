#include "Particle.h"

SYSTEM_THREAD(ENABLED);

// LED pins
#define LED_HIT       D2  // Green
#define LED_STAND     D3  // Red
#define LED_DOUBLE    D4  // Blue
#define LED_SURRENDER D5  // Amber

enum Action { HIT=0, STAND=1, DOUBLE=2, SURRENDER=3 };

// Example Q-table prototype (player_total 4-21, usable_ace 0/1, dealer 1-10)
// This is a small demo; fill with your full trained table later
Action policy_table[22][2][11];  

void initPolicyTable() {
    // Default to HIT
    for(int pt=4; pt<=21; pt++){
        for(int ua=0; ua<=1; ua++){
            for(int dealer=1; dealer<=10; dealer++){
                if(pt>=17) policy_table[pt][ua][dealer] = STAND;
                else if(pt<=11) policy_table[pt][ua][dealer] = HIT;
                else policy_table[pt][ua][dealer] = DOUBLE; // example
            }
        }
    }
}

// LED feedback
void indicateAction(Action a){
    digitalWrite(LED_HIT, LOW);
    digitalWrite(LED_STAND, LOW);
    digitalWrite(LED_DOUBLE, LOW);
    digitalWrite(LED_SURRENDER, LOW);

    switch(a){
        case HIT: digitalWrite(LED_HIT,HIGH); break;
        case STAND: digitalWrite(LED_STAND,HIGH); break;
        case DOUBLE: digitalWrite(LED_DOUBLE,HIGH); break;
        case SURRENDER: digitalWrite(LED_SURRENDER,HIGH); break;
    }
}

// Simulated sensor input
int player_total = 0;
bool usable_ace = false;
int dealer_upcard = 0;

Action getActionFromPolicy(int pt, bool ua, int dealer){
    if(pt<4) pt=4;
    if(pt>21) pt=21;
    int u = ua ? 1 : 0;
    if(dealer<1) dealer=1;
    if(dealer>10) dealer=10;
    return policy_table[pt][u][dealer];
}

void setup() {
    Serial.begin(9600);
    pinMode(LED_HIT, OUTPUT);
    pinMode(LED_STAND, OUTPUT);
    pinMode(LED_DOUBLE, OUTPUT);
    pinMode(LED_SURRENDER, OUTPUT);

    initPolicyTable();
}

void loop() {
    // --- Example: simulate sensor input ---
    player_total = 16;    // Player cards sum
    usable_ace = false;   // True if player has usable ace
    dealer_upcard = 10;   // Dealer upcard

    Action a = getActionFromPolicy(player_total, usable_ace, dealer_upcard);
    indicateAction(a);

    Serial.printf("Player total: %d, usable ace: %d, Dealer: %d -> Action: %d\n",
                  player_total, usable_ace?1:0, dealer_upcard, (int)a);

    delay(5000); // wait 5 seconds before next decision
}
