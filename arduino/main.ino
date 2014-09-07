/**
 * Name: nightsky/main
 * Author: Amjad Saadeh <mail@amjadsaadeh.de>
 *
 * Description: A simple firmware for an ArduinoUNO controller to manage a 5x6 LED-matrix
 *      with multiplexing. The used shift register if the 74HC595 (todo: link to build plan).
 *      The firmware saves the animation within the EEPROM and gives the user the ability to
 *      change animations with help of a simple protocol. An implementation of a client is
 *      in the "client" directory of this project.
 */

#include <Arduino.h>
#include <EEPROM.h>

#define FRAME_SIZE 5 // Frame size in byte
#define MAX_FRAME_COUNT 200 // Maximum amount of frames, that can be stored
#define STEP_DURATION 100 // Time of an animation step
#define LINE_AMOUNT 5
#define LINE_OFFSET 1 // It was easier not to connect Q0, so the first line is connected to Q1

// === Animation management ===
void loadFrame(int i);
void restartAnimation();

// Current frame state
unsigned short curFrameDuration = 0; // Left duration of the current frame
unsigned byte curFrame[LINE_AMOUNT]; // Current frame (one byte is one line)
unsigned byte curLine = 0; // Id of the line, that should be currently on
unsigned short nextFrameId = 0; // Id of the next frame

// Timestamp of the last step
unsigned long lastStepTime = 0;

// Pins
int latchPin = 8; // Pin connected to ST_CP of 74HC595
int clockPin = 12; // Pin connected to SH_CP of 74HC595
int dataPin = 11; // Pin connected to DS of 74HC595
// ========

// === Transmission ===
void processRequest();
void processPing();
void processFrameTransmission();
// Pin to indicate whether transmission is in progress
int infoPin = 13;
// ========


void setup() {
    // Animation setup
    pinMode(latchPin, OUTPUT);
    pinMode(clockPin, OUTPUT);
    pinMode(dataPin, OUTPUT);

    // Data transmission setup
    pinMode(infoPin, OUTPUT);
    Serial.begin(9600);
}

void loop() {

    // Load next frame, when it's over
    if (curFrameDuration < 1) {
        loadFrame(nextFrameId);
        nextFrameId++;
    }

    // Render current line
    digitalWrite(latchPin, LOW);
    shiftOut(dataPin, clockPin, MSBFIRST, curFrame[curLine]); // Shift in activated cols of the line
    shiftOut(dataPin, clockPin, MSBFIRST, 1 << (curLine + LINE_OFFSET)); // Shift in the current line
    digitalWrite(latchPin, HIGH);

    curLine = (curLine + 1) % LINE_AMOUNT;

    // Determine end of step
    if ((millis() - lastStepTime) >= STEP_DURATION || (millis() - lastStepTime) < 0) {
        lastStepTime = millis();
        curFrameDuration--;
    }
}

// Serial Event callback
void serialEvent() {
    processRequest();
}

// === Animation functions ===

/**
 * Loads a frame into the curFrame variable and the duration of the frame into curFrameDuration variable
 *
 * \param i the id of the frame
 */
void loadFrame(int i) {

    int startAddr = i * FRAME_SIZE;
    byte durationBuffer = EEPROM.read(startAddr);
    curFrameDuration = (durationBuffer << 2) + (EEPROM.read(startAddr + 1) >> 6);

    // Load next frame, by masking the necessary bits (bit flip is needed, because the shift register for the lines is a sink and needs to put to LOW)
    curFrame[0] = ~(EEPROM.read(startAddr + 1) & 63); // 63 = 00111111
    curFrame[1] = ~(EEPROM.read(startAddr + 2) >> 2);
    curFrame[2] = ~(((EEPROM.read(startAddr + 2) & 3) << 4) + (EEPROM.read(startAddr + 3) >> 4));
    curFrame[3] = ~(((EEPROM.read(startAddr + 3) & 15) << 2) + (EEPROM.read(startAddr + 4) >> 6));
    curFrame[4] = ~(EEPROM.read(startAddr + 4) & 63);
}

/**
 * Restarts the animation
 */
void restartAnimation() {
    curFrameDuration = 0;
    nextFrameId = 0;
    lastStepTime = millis();
}

// ========

// === Transmission functions ===

/**
 * Processes a request on the serial bus
 */
void processRequest() {
    digitalWrite(infoPin, HIGH);

    // Get initial message
    char msg[5];
    for (unsigned byte i = 0; i < 3; i++) {
        msg[i] = Serial.read();
    }
    msg[4] = '\0';

    // Determine request type
    if (strcmp(msg, "helo") == 0) {
        processFrameTransmission();
    } else if (strcmp(msg, "ping") == 0) {
        processPing();
    }
    digitalWrite(infoPin, LOW);
}

/**
 * Processes the transmission of a clip/animation
 */
void processClipTransmission() {
    Serial.write("helo"); // Respond, so client start sending frames

    // Receive frames
    byte frame[5];
    short frameId = 0;
    while (frameId < MAX_FRAME_COUNT) { // Prevent EEPROM overflow

        // Read first two byte for termination
        frame[0] = Serial.read();
        frame[1] = Serial.read();

        // Termination by client
        if (((frame[0] << 8) + frame[1]) == 0) {
            break;
        }

        // Read rest of frame
        frame[2] = Serial.read();
        frame[3] = Serial.read();
        frame[4] = Serial.read();

        // Write complete frame into EEPROM
        for (unsigned byte i = 0; i < FRAME_SIZE; i++) {
            EEPROM.write(frameId * FRAME_SIZE + i, frame[i]);
        }
        frameId++;
    }

    // Set end flag for animation
    EEPROM.write(frameId * FRAME_SIZE, 0);
    EEPROM.write(frameId * FRAME_SIZE + 1, 0);

    Serial.write("done"); // Say client that all is done

    restartAnimation();
}

/**
 * Processes a "ping"-request, which could be used by a client to identify the right port
 */
void processPing() {
    Serial.write("nsc1"); // Respond to ping
}

// ========
