# Aquarium mine thermometer

A naval-mine aquarium decoration that shows the water temperature as a glow colour: blue when it's too cold, green when it's just right, red when it's too warm.

| Folder | Contents |
|---|---|
| `print/` | Print files (`mine_print_plate.3mf` for the print service, plus STEP and STL), the CAD scripts (FreeCAD) and the assembly guide |
| `pcb/` | Controller board: KiCad board, `build_board.py`, and JLCPCB fab files (Gerber zip, BOM, CPL) |
| `firmware/` | Arduino sketch for the ESP32-C3 board: DS18B20 probe in, WS2811 pixel out |
| `marketing/` | Product renders, the Blender scene, render scripts, TikTok concept images and clips |

To order a print, start with `print/README.md`. For the board, start with `pcb/build_board.py` and the files in `pcb/fab/`.
