#include <math.h>

struct Sample { float pan, tilt, dist; };   // degrees, degrees, distance units
Sample sphereSampleFibonacci(uint16_t i, uint16_t n, float radius = 1.0f);
const uint16_t N_POINTS = 500;
uint16_t idx = 0;

void setup() {
  Serial.begin(115200);
}

void loop() {
  Sample s = sphereSampleFibonacci(idx, N_POINTS, 1.0f);

  Serial.print(s.pan, 2);  Serial.print(',');
  Serial.print(s.tilt, 2); Serial.print(',');
  Serial.println(s.dist, 3);

  idx = (idx + 1) % N_POINTS;

  delay(10); // 100 Hz transmission frequency testing
}

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
