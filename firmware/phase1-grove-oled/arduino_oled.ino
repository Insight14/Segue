/*
  Convo Coach - OLED display
  Board: Grove Beginner Kit for Arduino (Seeeduino Lotus) - select "Arduino Uno" in the IDE.
  Library needed: U8g2 (Sketch > Include Library > Manage Libraries > "U8g2")

  The computer sends one frame per line over USB serial (9600 baud):
      line0|line1|line2|...|line7\n
  Each '|'-separated piece is drawn on its own OLED row (16 characters x 8 rows).
  When you press the Grove button (D6) the board sends "BTN\n" back to the computer,
  which the Python script uses as "show me the next suggestion".
*/
#include <Arduino.h>
#include <U8x8lib.h>

U8X8_SSD1306_128X64_NONAME_HW_I2C u8x8(/* reset=*/ U8X8_PIN_NONE);

const uint8_t BUTTON_PIN = 6;    // Grove button (D6) - reads HIGH when pressed
const uint8_t LED_PIN    = 4;    // Grove LED (D4) - quick blink when a new frame arrives
const uint8_t COLS       = 16;
const uint8_t ROWS       = 8;
const uint8_t BUF_SIZE   = 140;  // 8 rows x 16 chars + 7 separators + safety margin

char buf[BUF_SIZE];
uint8_t len = 0;
bool lastPressed = false;
unsigned long lastPressMs = 0;

void drawFrame(char *msg) {
  u8x8.clear();
  uint8_t row = 0;
  char *line = msg;
  while (line != NULL && row < ROWS) {
    char *next = NULL;
    char *sep = strchr(line, '|');
    if (sep != NULL) {
      *sep = '\0';
      next = sep + 1;
    }
    if (strlen(line) > COLS) line[COLS] = '\0';   // never run past the screen edge
    u8x8.drawString(0, row, line);
    row++;
    line = next;
  }
}

void setup() {
  Serial.begin(9600);
  pinMode(BUTTON_PIN, INPUT);
  pinMode(LED_PIN, OUTPUT);

  u8x8.begin();
  u8x8.setFlipMode(1);                          // matches Seeed's example for this kit
  u8x8.setFont(u8x8_font_chroma48medium8_r);
  u8x8.drawString(0, 0, "Convo Coach");
  u8x8.drawString(0, 2, "Waiting for");
  u8x8.drawString(0, 3, "computer...");
}

void loop() {
  // ---- receive a frame ----
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n') {
      buf[len] = '\0';
      if (len > 0) {
        drawFrame(buf);
        digitalWrite(LED_PIN, HIGH);
        delay(40);
        digitalWrite(LED_PIN, LOW);
      }
      len = 0;
    } else if (c != '\r' && len < BUF_SIZE - 1) {
      buf[len++] = c;
    }
  }

  // ---- button -> tell the computer ----
  bool pressed = (digitalRead(BUTTON_PIN) == HIGH);
  if (pressed && !lastPressed && millis() - lastPressMs > 250) {
    Serial.println("BTN");
    lastPressMs = millis();
  }
  lastPressed = pressed;
}
