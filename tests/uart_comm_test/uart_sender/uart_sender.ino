#include <math.h>

struct Sample { float pan, tilt, dist; };   // degrees, degrees, distance units
Sample sphereSampleFibonacci(uint16_t i, uint16_t n, float radius = 1.0f);
void printBin(byte aByte);
const uint16_t N_POINTS = 500;
uint16_t idx = 0;
uint16_t sync1 = 0x55;
uint16_t sync2 = 0x66;

void setup() {
  Serial.begin(115200);
}

void loop() {
  Sample s = sphereSampleFibonacci(idx, N_POINTS, 1.0f);


  //2 bytes sync
  Serial.print(sync1, BIN);
  Serial.print('|'); //TESTING ONLY
  
  Serial.print(sync2, BIN);
  Serial.print('|'); //TESTING ONLY


  //TODO: Figure out how to pad dist, pan, and tilt to 2 bytes per.
  
  // 2 bytes pan, tilt, dist
  uint8_t panBits;
  memcpy(&panBits, &s.pan, sizeof(panBits));
  Serial.print(panBits, BIN);
  Serial.print('|'); //TESTING ONLY
  
  uint8_t tiltBits;
  memcpy(&tiltBits, &s.tilt, sizeof(tiltBits));
  Serial.print(tiltBits, BIN);
  Serial.print('|'); //TESTING ONLY
  
  Serial.print(1, BIN);
  Serial.println();

  idx = (idx + 1) % N_POINTS;

  delay(10); // 100 Hz transmission frequency testing
}

void printBin(byte aByte) {
  for (int8_t aBit = 7; aBit >= 0; aBit--)
    Serial.print(bitRead(aByte, aBit) ? '1' : '0');

Sample sphereSampleFibonacci(uint16_t i, uint16_t n, float radius = 1.0f)
{
    const float GOLDEN_ANGLE = 2.39996323f;               // radians
    float z = 1.0f - 2.0f * (i + 0.5f) / n;               // sin(tilt), uniform in (-1, 1)

    Sample s;
    s.tilt = asinf(z) * RAD_TO_DEG;
    s.pan  = fmodf(i * GOLDEN_ANGLE, 2.0f * PI) * RAD_TO_DEG;
    s.dist = radius;
    return s;
}
