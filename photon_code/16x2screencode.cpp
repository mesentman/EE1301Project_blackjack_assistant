#include <Particle.h>
#include <iostream>
#include <Wire.h>       //download lib!!!!!

// ST7032 default I2C address
#define LCD_ADDR 0x3E

int buttonPin1 = D3;   // Button input pin
int buttonPin2 = D4;   // Button input pin
int buttonPin3 = D5;   // Button input pin
int buttonPin4 = D6;   // Button input pin
int buttonPin5 = D7;   // Button input pin
int buttonState1 = HIGH;     // Default state (HIGH because of pull-up)
int buttonState2 = HIGH;     // Default state (HIGH because of pull-up)
int buttonState3 = HIGH;     // Default state (HIGH because of pull-up)
int buttonState4 = HIGH;     // Default state (HIGH because of pull-up)
int buttonState5 = HIGH;     // Default state (HIGH because of pull-up)


// ARE WE USING WIN RATE ON THE SCREEN


int command = -1;     // to display the action from Matthews code

// 0 - hit 
// 1 - stand
// 2 - double
// 3 - split 
// 4 - surrender

int numCount = -4;
int winRate = 100;

void lcdCommand(uint8_t cmd) {      //LCD function -- AI
    Wire.beginTransmission(LCD_ADDR);
    Wire.write(0x00); // Control byte: Co = 0, RS = 0
    Wire.write(cmd);
    Wire.endTransmission();
}

void lcdData(uint8_t data) {        //LCD fucntion -- AI
    Wire.beginTransmission(LCD_ADDR);
    Wire.write(0x40); // Control byte: Co = 0, RS = 1
    Wire.write(data);
    Wire.endTransmission();
}

void lcdInit() {        //LCD function -- AI
    delay(50);
    lcdCommand(0x38); // Function set: 8-bit, 2 line, normal instruction
    lcdCommand(0x39); // Function set: extended instruction
    lcdCommand(0x14); // Bias set
    lcdCommand(0x70 | 0x0A); // Contrast set (lower 4 bits)
    lcdCommand(0x5C); // Power/icon/contrast control
    lcdCommand(0x6C); // Follower control
    delay(200);
    lcdCommand(0x38); // Function set: normal instruction
    lcdCommand(0x0C); // Display ON, cursor OFF, blink OFF
    lcdCommand(0x01); // Clear display
    delay(2);
} 

void lcdSetCursor(uint8_t col, uint8_t row) {   //LCD function -- AI
    const uint8_t row_offsets[] = {0x00, 0x40};
    lcdCommand(0x80 | (col + row_offsets[row]));
}

void lcdPrint(const char *str) {        //LCD function -- AI
    while (*str) {
        lcdData(*str++);
    }
}

void setup() {
    Wire.begin();
    lcdInit();

    pinMode(buttonPin1, INPUT_PULLDOWN);  
    pinMode(buttonPin2, INPUT_PULLDOWN);  
    pinMode(buttonPin3, INPUT_PULLDOWN);  
    pinMode(buttonPin4, INPUT_PULLDOWN);  
    pinMode(buttonPin5, INPUT_PULLDOWN);  
}

void loop() {

char buffer1[16]; // converts winRate into a char so LCD can print it
char buffer2[16]; // converts numCount into a char so LCD can print it




//-----------------------just for buttons-------------------------
// 0 - hit 
// 1 - stand
// 2 - double
// 3 - split 
// 4 - surrender
buttonState1 = digitalRead(buttonPin1);
buttonState2 = digitalRead(buttonPin2);
buttonState3 = digitalRead(buttonPin3);
buttonState4 = digitalRead(buttonPin4);
buttonState5 = digitalRead(buttonPin5);
if (buttonState1 == HIGH) { // button pressed
    command = 0;
}
if (buttonState2 == HIGH) { // button pressed
    command = 1;
}
if (buttonState3 == HIGH) { // button pressed
    command = 2;
}
if (buttonState4 == HIGH) { // button pressed
    command = 3;
}
if (buttonState5 == HIGH) { // button pressed
    command = 4;
}
//----------------------------------------------------------------

if (winRate == 100) {
    winRate = 99;
}




if (command == 0) {
    lcdCommand(0x01); // Clear display
    while (command == 0) {
        lcdSetCursor(0, 0);   // Move the cursor to column 0, row 0 (top-left corner)
        lcdPrint("HIT");    // Print text to the LCD at the current cursor position

        lcdSetCursor(7, 0);   // Move the cursor to column 7, row 0
        sprintf(buffer1, "Win: 0.%d", winRate);  //switch winRate to a char
        lcdPrint(buffer1); // print Char of winRate

        lcdSetCursor(0, 1);   // Move the cursor to column 0, row 0 (top-left corner)
        sprintf(buffer2, "Count: %d", numCount);  //switch numCount to a char
        lcdPrint(buffer2); // print Char of numCount

        //--- only for buttons-----------------------------
        buttonState1 = digitalRead(buttonPin1);
        if (buttonState1 == LOW) {
            command = -1;
        }
        //-------------------------------------------------
    }
    lcdCommand(0x01); // Clear display
}
if (command == 1) {
    lcdCommand(0x01); // Clear display
    while (command == 1) {
        lcdSetCursor(0, 0);   // Move the cursor to column 0, row 0 (top-left corner)
        lcdPrint("STAND");    // Print text to the LCD at the current cursor position

        lcdSetCursor(7, 0);   // Move the cursor to column 7, row 0
        sprintf(buffer1, "Win: 0.%d", winRate);  //switch winRate to a char
        lcdPrint(buffer1); // print Char of winRate

        lcdSetCursor(0, 1);   // Move the cursor to column 0, row 0 (top-left corner)
        sprintf(buffer2, "Count: %d", numCount);  //switch numCount to a char
        lcdPrint(buffer2); // print Char of numCount

        //--- only for buttons-----------------------------
        buttonState2 = digitalRead(buttonPin2);
        if (buttonState2 == LOW) {
            command = -1;
        }
        //-------------------------------------------------
    }
    lcdCommand(0x01); // Clear display
}
if (command == 2) {
    lcdCommand(0x01); // Clear display
    while (command == 2) {
        lcdSetCursor(0, 0);   // Move the cursor to column 0, row 0 (top-left corner)
        lcdPrint("DOUBLE");    // Print text to the LCD at the current cursor position

        lcdSetCursor(7, 0);   // Move the cursor to column 7, row 0
        sprintf(buffer1, "Win: 0.%d", winRate);  //switch winRate to a char
        lcdPrint(buffer1); // print Char of winRate

        lcdSetCursor(0, 1);   // Move the cursor to column 0, row 0 (top-left corner)
        sprintf(buffer2, "Count: %d", numCount);  //switch numCount to a char
        lcdPrint(buffer2); // print Char of numCount

        //--- only for buttons-----------------------------
        buttonState3 = digitalRead(buttonPin3);
        if (buttonState3 == LOW) {
            command = -1;
        }
        //-------------------------------------------------
    }
    lcdCommand(0x01); // Clear display
}
if (command == 3) {
    lcdCommand(0x01); // Clear display
    while (command == 3) {
        lcdSetCursor(0, 0);   // Move the cursor to column 0, row 0 (top-left corner)
        lcdPrint("SPLIT");    // Print text to the LCD at the current cursor position

        lcdSetCursor(0, 1);   // Move the cursor to column 0, row 0 (top-left corner)
        sprintf(buffer2, "Count: %d", numCount);  //switch numCount to a char
        lcdPrint(buffer2); // print Char of numCount

        //--- only for buttons-----------------------------
        buttonState4 = digitalRead(buttonPin4);
        if (buttonState4 == LOW) {
            command = -1;
        }
        //-------------------------------------------------
    }
    lcdCommand(0x01); // Clear display
}
if (command == 4) {
    lcdCommand(0x01); // Clear display
    while (command == 4) {
        lcdSetCursor(0, 0);   // Move the cursor to column 0, row 0 (top-left corner)
        lcdPrint("SURRENDER");    // Print text to the LCD at the current cursor position

        lcdSetCursor(0, 1);   // Move the cursor to column 0, row 0 (top-left corner)
        sprintf(buffer2, "Count: %d", numCount);  //switch numCount to a char
        lcdPrint(buffer2); // print Char of numCount

        //--- only for buttons-----------------------------
        buttonState5 = digitalRead(buttonPin5);
        if (buttonState5 == LOW) {
            command = -1;
        }
        //-------------------------------------------------
    }
    lcdCommand(0x01); // Clear display
}

else { // Print SCAN CARDS while waiting for code to send instructions
    lcdCommand(0x01); // Clear display
    delay(5);        // Give LCD time to clear fully

    while (command == -1) {
        lcdSetCursor(0, 0);
        lcdPrint("SCANNING");
        lcdSetCursor(0, 1);
        lcdPrint("CARDS");

        // Animate the dots with instant response
        for (int j = 0; j < 4 && command == -1; j++) {  // Stop early if button pressed
            lcdSetCursor(5, 1);  // start after "CARDS"
            
            // Print j dots
            for (int k = 0; k < j; k++) {
                lcdPrint(".");
            }
            delay(500);

            //-----------------------just for buttons-------------------------
            // 0 - hit 
            // 1 - stand
            // 2 - double
            // 3 - split 
            // 4 - surrender
            buttonState1 = digitalRead(buttonPin1);
            buttonState2 = digitalRead(buttonPin2);
            buttonState3 = digitalRead(buttonPin3);
            buttonState4 = digitalRead(buttonPin4);
            buttonState5 = digitalRead(buttonPin5);
            if (buttonState1 == HIGH) { // button pressed
                command = 0;
            }
            if (buttonState2 == HIGH) { // button pressed
                command = 1;
            }
            if (buttonState3 == HIGH) { // button pressed
                command = 2;
            }
            if (buttonState4 == HIGH) { // button pressed
                command = 3;
            }
            if (buttonState5 == HIGH) { // button pressed
                command = 4;
            }
            if (command != -1) break; // exit early if a button was pressed
            //----------------------------------------------------------------

            // Erase dots before next cycle
            lcdSetCursor(5, 1);
            lcdPrint("   ");
        }
    }
}
}