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
void restartAnimation();
void loadFrame(int i);
void saveFrame(int frameId, char* frame);
void setEndFlag(int frameId);
bool isEndFlag(int frameId);
void writeDefaultClip();

// Current frame state
unsigned short curFrameDuration = 0; // Left duration of the current frame
byte curFrame[LINE_AMOUNT]; // Current frame (one byte is one line)
byte curLine = 0; // Id of the line, that should be currently on
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
void processClipTransmission();
void processReset();
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
        // Restart animation, if the end is reached
        if (isEndFlag(nextFrameId)) {
            // Write default clip into EEPROM, if there is no clip stored
            if (nextFrameId == 0) {
                writeDefaultClip();
            }
            restartAnimation();
        }
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
    curFrame[0] = EEPROM.read(startAddr + 1) & 63; // 63 = 00111111
    curFrame[1] = EEPROM.read(startAddr + 2) >> 2;
    curFrame[2] = ((EEPROM.read(startAddr + 2) & 3) << 4) + (EEPROM.read(startAddr + 3) >> 4);
    curFrame[3] = ((EEPROM.read(startAddr + 3) & 15) << 2) + (EEPROM.read(startAddr + 4) >> 6);
    curFrame[4] = EEPROM.read(startAddr + 4) & 63;

    // Put the bits to right position according to the line offset and flip them, because the cols needs to be LOW to be on
    for (unsigned short j = 0; j < LINE_AMOUNT; j++) {
        curFrame[j] = ~(curFrame[j] << LINE_OFFSET);
    }
}

/**
 * Saves a frame at desired position
 *
 * \param frameId index (position) of the frame
 * \param frame the frame that should be written in
 */
void saveFrame(int frameId, char* frame) {
    for (byte i = 0; i < FRAME_SIZE; i++) {
        EEPROM.write(frameId * FRAME_SIZE + i, frame[i]);
    }
}

/**
 * Sets end of clip at desired position
 *
 * \param frameId index (position) of end frame
 */
void setEndFlag(int frameId) {
    EEPROM.write(frameId * FRAME_SIZE, 0);
    EEPROM.write(frameId * FRAME_SIZE + 1, 0);
}

/**
 * Restarts the animation
 */
void restartAnimation() {
    curFrameDuration = 0;
    nextFrameId = 0;
    lastStepTime = millis();
}

/**
 * Checks whether the end of clip is reached
 *
 * \param frameId index of the frame that should be checked
 * \return true if it's the end flag
 */
bool isEndFlag(int frameId) {
    int startAddr = frameId * FRAME_SIZE;
    return ((EEPROM.read(startAddr) << 8) + EEPROM.read(startAddr + 1)) == 0;
}

/**
 * Writes a default clip into EEPROM
 */
void writeDefaultClip() {
    digitalWrite(infoPin, HIGH); // Indicating that there is some processing

    char frame[5];
    for (int j = 0; j < FRAME_SIZE; j++) frame[j] = 0; // Reset frame buffer

    // Blink line by line
    frame[1] = 255;
    saveFrame(0, frame);
    for (int j = 1; j < FRAME_SIZE; j++) frame[j] = 0; // Reset frame buffer

    frame[1] = 3 << 6;
    frame[2] = 63 << 2;
    saveFrame(1, frame);
    for (int j = 1; j < FRAME_SIZE; j++) frame[j] = 0; // Reset frame buffer

    frame[1] = 3 << 6;
    frame[2] = 3;
    frame[3] = 15 << 4;
    saveFrame(2, frame);
    for (int j = 1; j < FRAME_SIZE; j++) frame[j] = 0; // Reset frame buffer

    frame[1] = 3 << 6;
    frame[3] = 15;
    frame[4] = 3 << 6;
    saveFrame(3, frame);
    for (int j = 1; j < FRAME_SIZE; j++) frame[j] = 0; // Reset frame buffer

    frame[1] = 3 << 6;
    frame[4] = 63;
    saveFrame(4, frame);
    for (int j = 1; j < FRAME_SIZE; j++) frame[j] = 0; // Reset frame buffer

    // Blink col by col
    frame[1] = (3 << 6) + 1;
    frame[2] = 1 << 2;
    frame[3] = 1 << 4;
    frame[4] = (1 << 6) + 1;
    saveFrame(5, frame);
    for (int j = 1; j < FRAME_SIZE; j++) frame[j] = 0; // Reset frame buffer

    frame[1] = (3 << 6) + (1 << 1);
    frame[2] = 1 << 3;
    frame[3] = 1 << 5;
    frame[4] = (1 << 7) + (1 << 1);
    saveFrame(6, frame);
    for (int j = 1; j < FRAME_SIZE; j++) frame[j] = 0; // Reset frame buffer

    frame[1] = (3 << 6) + (1 << 2);
    frame[2] = 1 << 4;
    frame[3] = (1 << 6) + 1;
    frame[4] = 1 << 2;
    saveFrame(7, frame);
    for (int j = 1; j < FRAME_SIZE; j++) frame[j] = 0; // Reset frame buffer

    frame[1] = (3 << 6) + (1 << 3);
    frame[2] = 1 << 5;
    frame[3] = (1 << 7) + (1 << 1);
    frame[4] = 1 << 3;
    saveFrame(8, frame);
    for (int j = 1; j < FRAME_SIZE; j++) frame[j] = 0; // Reset frame buffer

    frame[1] = (3 << 6) + (1 << 4);
    frame[2] = (1 << 6) + 1;
    frame[3] = 1 << 2;
    frame[4] = 1 << 4;
    saveFrame(9, frame);
    for (int j = 1; j < FRAME_SIZE; j++) frame[j] = 0; // Reset frame buffer

    frame[1] = (3 << 6) + (1 << 5);
    frame[2] = (1 << 7) + (1 << 1);
    frame[3] = 1 << 3;
    frame[4] = 1 << 5;
    saveFrame(10, frame);
    for (int j = 1; j < FRAME_SIZE; j++) frame[j] = 0; // Reset frame buffer

    // All off
    frame[1] = 3 << 6;
    saveFrame(11, frame);

    // All on for about 3 seconds
    frame[0] = 3;
    for (int j = 1; j < FRAME_SIZE; j++) frame[j] = 255;
    saveFrame(12, frame);

    setEndFlag(13);

    digitalWrite(infoPin, LOW);
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
    Serial.readBytes(msg, 4);
    msg[4] = '\0';

    // Determine request type
    if (strcmp(msg, "helo") == 0) {
        processClipTransmission();
    } else if (strcmp(msg, "ping") == 0) {
        processPing();
    } else if (strcmp(msg, "rest") == 0) {
        processReset();
    }
    digitalWrite(infoPin, LOW);
}

/**
 * Processes the transmission of a clip/animation
 */
void processClipTransmission() {
    Serial.write("helo"); // Respond, so client start sending frames

    // Receive frames
    char frame[] = {0, 0, 0, 0, 0};
    short frameId = 0;
    while (frameId < MAX_FRAME_COUNT) { // Prevent EEPROM overflow

        // Read first two byte for termination
        Serial.readBytes(frame, 2);
        // Termination by client
        if (((frame[0] << 8) + frame[1]) == 0) {
            break;
        }

        // Read rest of frame
        Serial.readBytes(frame+2, 3);

        // Write complete frame into EEPROM
        saveFrame(frameId, frame);
        Serial.write("ok  ");
        frameId++;
    }

    // Set end flag for animation
    setEndFlag(frameId);

    Serial.write("done"); // Say client that all is done

    restartAnimation();
}

/**
 * Processes a "ping"-request, which could be used by a client to identify the right port
 */
void processPing() {
    Serial.write("nsd1"); // Respond to ping
}

void processReset() {
    writeDefaultClip();
    restartAnimation();
    Serial.write("done");
}
// ========
