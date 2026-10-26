// Aquarium mine thermometer
// Reads a waterproof DS18B20 probe and colours a WS2811 12 mm bullet pixel
// inside the printed mine: blue = too cold, green = in range, red = too warm.
//
// Libraries (Arduino Library Manager): OneWire, DallasTemperature, Adafruit NeoPixel
// Board: the aquarium mine controller PCB (ESP32-C3). In the Arduino IDE pick
// "ESP32C3 Dev Module" and enable "USB CDC On Boot". For an Arduino Nano use pins 2 and 6.

#include <OneWire.h>
#include <DallasTemperature.h>
#include <Adafruit_NeoPixel.h>

// ---- Settings ---------------------------------------------------------------
const uint8_t PIN_TEMP = 4;      // IO4: DS18B20 data (4.7k pull-up to 3V3 on the board)
const uint8_t PIN_LED  = 5;      // IO5: pixel data, shifted to 5 V by U3, 330 ohm series resistor
const uint8_t NUM_LEDS = 1;

const float TEMP_LOW   = 24.0;   // bottom of the healthy range, deg C
const float TEMP_HIGH  = 27.0;   // top of the healthy range, deg C
const float FADE_BAND  = 1.5;    // deg C over which green fades to blue / red

const uint8_t BRIGHTNESS = 60;   // 0-255, keep low so it does not stress fish
// Many WS2811 bullet pixels are RGB order; if colours look swapped, try NEO_GRB.
Adafruit_NeoPixel pixel(NUM_LEDS, PIN_LED, NEO_RGB + NEO_KHZ800);
// -----------------------------------------------------------------------------

OneWire oneWire(PIN_TEMP);
DallasTemperature sensors(&oneWire);

struct Rgb { uint8_t r, g, b; };

const Rgb COLD = {0, 60, 255};
const Rgb GOOD = {0, 255, 60};
const Rgb WARM = {255, 30, 0};

Rgb blend(Rgb a, Rgb b, float t) {
  t = constrain(t, 0.0f, 1.0f);
  return { (uint8_t)(a.r + (b.r - a.r) * t),
           (uint8_t)(a.g + (b.g - a.g) * t),
           (uint8_t)(a.b + (b.b - a.b) * t) };
}

Rgb colourFor(float c) {
  if (c < TEMP_LOW)  return blend(GOOD, COLD, (TEMP_LOW - c) / FADE_BAND);
  if (c > TEMP_HIGH) return blend(GOOD, WARM, (c - TEMP_HIGH) / FADE_BAND);
  return GOOD;
}

void show(Rgb c) {
  for (uint8_t i = 0; i < NUM_LEDS; i++) pixel.setPixelColor(i, pixel.Color(c.r, c.g, c.b));
  pixel.show();
}

void setup() {
  Serial.begin(115200);
  sensors.begin();
  pixel.begin();
  pixel.setBrightness(BRIGHTNESS);
  show({0, 0, 0});
}

void loop() {
  sensors.requestTemperatures();
  float c = sensors.getTempCByIndex(0);

  if (c == DEVICE_DISCONNECTED_C || c < -10 || c > 60) {
    // Sensor missing or unplugged: slow purple blink
    static bool on = false;
    on = !on;
    show(on ? Rgb{120, 0, 120} : Rgb{0, 0, 0});
    Serial.println("Temperature sensor not found");
    delay(1000);
    return;
  }

  show(colourFor(c));
  Serial.print("Water: "); Serial.print(c, 1); Serial.println(" C");
  delay(2000);
}
