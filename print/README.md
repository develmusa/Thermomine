# Aquarium mine thermometer

A 155 mm tall naval mine for the tank. The LED inside glows blue, green or red to show the water temperature.

## Print (MJF, PA12)

| File | Part | Size |
|---|---|---|
| `mine_bottom.stl` | Base, tether, lower shell with 16 glow slots, LED pocket | 94 × 96 × 113 mm |
| `mine_cap.stl` | Top shell with horns, 4 air vents, bayonet collar with 3 lugs | 80 × 80 × 49 mm |

**File formats** (all in mm, built from the same exact CAD solids):

| File | Use |
|---|---|
| `mine_print_plate.3mf` | **Send this to the print service**: both parts on one plate, units built in |
| `mine_bottom.3mf`, `mine_cap.3mf` | Single parts, if the service wants one file per part |
| `mine_bottom.step`, `mine_cap.step` | Exact CAD solids, for quotes or for editing in CAD |
| `mine_assembly.step` | Both parts in the closed position, to check the fit |
| `mine_bottom.stl`, `mine_cap.stl` | Fallback for services that only take STL |

The STEP files are rebuilt with `freecadcmd build_step.py`, and the 3MF/STL with `freecadcmd export_3mf.py`. The meshes have a few grazing triangles where the horn collars meet the sphere, which print services repair automatically; the STEP solids are valid.

- Units are millimetres. Wall thickness is 2.5 mm and the smallest hole is 3 mm.
- Bayonet lock: three lugs on the cap's collar run in L-shaped slots in a ring inside the bottom shell. Each lug sticks out 1.2 mm, with 0.3 mm clearance all round. A 0.3 mm step near the end of the slot makes it click shut.
- Order the parts undyed (grey) or white. A lighter colour reflects more LED light inside the shell.
- Vapour smoothing is optional; it makes algae easier to wipe off.
- Before use, rinse the parts, soak them in tank water for 24 h, and rinse again.

## Parts list

- 1 × WS2811 12 mm bullet pixel, **5 V, IP68** (the waterproof kind that pushes into a 12 mm hole)
- 1 × DS18B20 waterproof probe (stainless steel tip, 6 mm diameter)
- 1 × controller board, ordered assembled (see `../pcb/`), and a 5 V USB-C power supply
- Aquarium-safe silicone (100 % silicone, no fungicide)

## Assembly

1. Cut the connector off the pixel's cable. Feed the cable end down from the LED pocket, through the tether, and out through the groove under the base. Push the pixel into the pocket so the LED points up.
2. Clip the temperature probe into the C-clip on the side of the base.
3. Close the bayonet: set the cap on so its lugs drop into the three open slots, push down, then turn it **clockwise about 30°** (seen from above) until it clicks. To open, turn it anticlockwise and lift. No glue is needed.
4. Water fills the shell through the slots, and air escapes through the top vents. This is on purpose: only the factory-sealed LED and probe are wet, so nothing printed needs to be watertight.
5. **Weight it with sand.** The base is hollow and open underneath: 2.5 mm walls, a 3 mm ceiling, and a centre tube around the cable bore. Turn the bottom part upside down, run the cable out through the notch in the rim, fill the cavity with dry aquarium sand or fine gravel, and seal the opening flush with a 3–4 mm layer of aquarium-safe silicone. Let it cure for 24 h before it goes into water. This saves about 30 % of the print material (bottom part 95.7 → 66.6 cm³).
6. Run both cables over the tank rim with a **drip loop**, so water running down the cables drips off before it reaches the electronics. The controller board and power supply stay dry, outside the tank.

## Wiring (screw terminals, labelled on the back of the board)

```
LED terminal   (J2):  +5V -> pixel red     DIN -> pixel data (green/white)   GND -> pixel black/blue
PROBE terminal (J3):  GND -> probe black   DQ  -> probe yellow                3V3 -> probe red
```

Wire colours vary by seller; check the labels on your pixel and probe.

## Firmware

`../firmware/aquarium_mine_temp/aquarium_mine_temp.ino`

The healthy range is set by `TEMP_LOW` and `TEMP_HIGH` and defaults to 24–27 °C (tropical). Outside it, the colour fades to blue (colder) or red (warmer) over 1.5 °C. A purple blink means the probe isn't connected.
