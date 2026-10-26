"""Workshop drawings (A3) for the Thermomine parts, to SN EN ISO conventions:
first-angle projection (ISO 5456-2), line types (ISO 128), dimensioning (ISO 129-1),
sheet + title block (ISO 5457 / ISO 7200), general tolerances ISO 2768-m.
Views are hidden-line projections of the exact STEP solids (FreeCAD TechDraw).

   freecadcmd make_drawings.py      -> Thermomine_TM-001-01_bottom.svg, ..._02_cap.svg
"""
import math
import os

import Part
import TechDraw
from FreeCAD import Vector as V

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
PRINT = os.path.dirname(HERE)
W, H = 420.0, 297.0                       # A3 landscape
THICK, THIN = 0.5, 0.25                   # ISO 128 line widths (mm)
TXT = 3.5                                 # ISO 3098 lettering height
FONT = "DejaVu Sans, Arial, sans-serif"
DATE = "2026-10-26"


# ----------------------------------------------------------------------------- svg helpers
class Sheet:
    def __init__(self):
        self.out = []

    def add(self, s):
        self.out.append(s)

    def line(self, x1, y1, x2, y2, w=THIN, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<line x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}" stroke="#000" stroke-width="{w}"{d}/>')

    def text(self, x, y, s, size=TXT, anchor="middle", rot=0, weight="normal"):
        t = f' transform="rotate({rot} {x:.3f} {y:.3f})"' if rot else ""
        self.add(f'<text x="{x:.3f}" y="{y:.3f}" font-family="{FONT}" font-size="{size}" text-anchor="{anchor}" '
                 f'font-weight="{weight}"{t}>{s}</text>')

    def arrow(self, x, y, ang):
        """Filled ISO arrowhead, tip at (x, y), pointing along ang (radians)."""
        l, w = 3.0, 0.5
        bx, by = x - l * math.cos(ang), y - l * math.sin(ang)
        px, py = -math.sin(ang) * w, math.cos(ang) * w
        self.add(f'<path d="M {x:.3f} {y:.3f} L {bx + px:.3f} {by + py:.3f} L {bx - px:.3f} {by - py:.3f} Z" fill="#000"/>')

    def render(self, path):
        body = "\n".join(self.out)
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}">\n'
               '<defs><pattern id="hatch" patternUnits="userSpaceOnUse" width="2.5" height="2.5" '
               'patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="2.5" stroke="#000" stroke-width="0.18"/>'
               '</pattern></defs>\n<rect width="100%" height="100%" fill="#fff"/>\n' + body + "\n</svg>\n")
        open(path, "w").write(svg)


class View:
    """Places model coordinates (u right, v up, mm) on the sheet at (ox, oy) with a scale."""

    def __init__(self, sheet, ox, oy, scale=1.0):
        self.s, self.ox, self.oy, self.k = sheet, ox, oy, scale

    def P(self, u, v):
        return self.ox + u * self.k, self.oy - v * self.k

    def projection(self, shape):
        svg = TechDraw.projectToSVG(shape, V(0, 0, 1))
        svg = svg.replace('stroke-width="1.0"', f'stroke-width="{THICK / self.k:.3f}"')
        self.s.add(f'<g transform="translate({self.ox:.3f} {self.oy:.3f}) scale({self.k})">{svg}</g>')

    def section_faces(self, wires):
        """Hatched cut faces (u = x, v = z of the cut plane); even-odd fill handles holes."""
        d = []
        for w in wires:
            pts = w.discretize(Deflection=0.02)
            d.append("M " + " L ".join(f"{self.P(p.x, p.z)[0]:.3f} {self.P(p.x, p.z)[1]:.3f}" for p in pts) + " Z")
        self.s.add(f'<path d="{" ".join(d)}" fill="url(#hatch)" fill-rule="evenodd" stroke="#000" stroke-width="{THICK}"/>')

    def centre_v(self, u, v0, v1):
        (x, y0), (_, y1) = self.P(u, v0 - 4), self.P(u, v1 + 4)
        self.s.line(x, y0, x, y1, THIN, "12 2 2 2")

    def centre_h(self, v, u0, u1):
        (x0, y), (x1, _) = self.P(u0 - 4, v), self.P(u1 + 4, v)
        self.s.line(x0, y, x1, y, THIN, "12 2 2 2")

    # ISO 129-1 linear dimensions: extension lines 1 mm gap, 2 mm overshoot; text above the line
    def dim_h(self, u1, u2, v_obj1, v_obj2, v_dim, label):
        s = self.s
        (x1, yo1), (x2, yo2), (_, yd) = self.P(u1, v_obj1), self.P(u2, v_obj2), self.P(0, v_dim)
        for x, yo in ((x1, yo1), (x2, yo2)):
            sgn = 1 if yd > yo else -1
            s.line(x, yo + sgn * 1.0, x, yd + sgn * 2.0)
        s.line(x1, yd, x2, yd)
        if abs(x2 - x1) > 9:
            s.arrow(x1, yd, math.pi if x1 < x2 else 0); s.arrow(x2, yd, 0 if x1 < x2 else math.pi)
            s.text((x1 + x2) / 2, yd - 1.0, label)
        else:                                       # too narrow: arrows from outside, text beside
            lo, hi = min(x1, x2), max(x1, x2)
            s.line(lo - 6, yd, lo, yd); s.line(hi, yd, hi + 6, yd)
            s.arrow(lo, yd, 0); s.arrow(hi, yd, math.pi)
            s.text(hi + 7, yd - 1.0, label, anchor="start")

    def dim_v(self, v1, v2, u_obj1, u_obj2, u_dim, label):
        s = self.s
        (xo1, y1), (xo2, y2), (xd, _) = self.P(u_obj1, v1), self.P(u_obj2, v2), self.P(u_dim, 0)
        for xo, y in ((xo1, y1), (xo2, y2)):
            sgn = 1 if xd > xo else -1
            s.line(xo + sgn * 1.0, y, xd + sgn * 2.0, y)
        s.line(xd, y1, xd, y2)
        if abs(y2 - y1) > 9:
            s.arrow(xd, y1, math.pi / 2 if y1 < y2 else -math.pi / 2); s.arrow(xd, y2, -math.pi / 2 if y1 < y2 else math.pi / 2)
            s.text(xd - 1.0, (y1 + y2) / 2, label, rot=-90)
        else:
            lo, hi = min(y1, y2), max(y1, y2)
            s.line(xd, lo - 6, xd, lo); s.line(xd, hi, xd, hi + 6)
            s.arrow(xd, lo, math.pi / 2); s.arrow(xd, hi, -math.pi / 2)
            s.text(xd - 1.0, lo - 7, label, rot=-90, anchor="start")

    def leader(self, u, v, dx, dy, label, anchor="start"):
        """Leader with arrow onto the object point, text at the end of a short shoulder."""
        s = self.s
        x, y = self.P(u, v)
        ex, ey = x + dx, y + dy
        s.line(x, y, ex, ey)
        s.arrow(x, y, math.atan2(y - ey, x - ex))
        sh = 4 if anchor == "start" else -4
        s.line(ex, ey, ex + sh, ey)
        s.text(ex + sh + (1 if sh > 0 else -1), ey + 1.2, label, anchor=anchor)


def frame(s, title, number, mass, part_notes):
    """ISO 5457 border (20 mm filing margin) and ISO 7200 title block."""
    s.add(f'<rect x="20" y="10" width="{W - 30}" height="{H - 20}" fill="none" stroke="#000" stroke-width="0.7"/>')
    for k in range(1, 8):                              # centring marks
        pass
    s.line(W / 2, 0, W / 2, 10, 0.7); s.line(W / 2, H - 10, W / 2, H, 0.7); s.line(10, H / 2, 20, H / 2, 0.7); s.line(W - 10, H / 2, W, H / 2, 0.7)
    x0, x1, y0, y1 = W - 10 - 180, W - 10, H - 10 - 56, H - 10
    s.add(f'<rect x="{x0}" y="{y0}" width="180" height="56" fill="none" stroke="#000" stroke-width="0.7"/>')
    rows = [y0 + 8, y0 + 16, y0 + 24, y0 + 40]
    for y in rows:
        s.line(x0, y, x1, y, THIN)
    for x, ya, yb in ((x0 + 45, y0, y0 + 24), (x0 + 90, y0, y0 + 24), (x0 + 135, y0, y0 + 24),
                      (x0 + 120, y0 + 40, y1), (x0 + 150, y0 + 40, y1)):
        s.line(x, ya, x, yb, THIN)

    def field(x, y, label, value, size=3.5, w="normal"):
        s.text(x + 1.5, y + 2.6, label, size=1.8, anchor="start")
        s.text(x + 1.5, y + 6.8, value, size=size, anchor="start", weight=w)
    field(x0, y0, "Material", "PA12 (HP MJF)", 2.8)
    field(x0 + 45, y0, "Surface", "as printed, dyed black", 2.5)
    field(x0 + 90, y0, "Mass (approx.)", mass, 2.8)
    field(x0 + 135, y0, "Scale", "1:1", 3.5)
    field(x0, y0 + 8, "General tolerances", "ISO 2768-m", 2.8)
    field(x0 + 45, y0 + 8, "Unit", "mm", 2.8)
    field(x0 + 90, y0 + 8, "Created by / Date", f"develmusa / {DATE}", 2.4)
    field(x0 + 135, y0 + 8, "Approved by", "–", 2.8)
    field(x0, y0 + 16, "Document type", "Part drawing", 2.8)
    field(x0 + 45, y0 + 16, "Document status", "Prototype", 2.8)
    field(x0 + 90, y0 + 16, "Owner", "Thermomine", 2.8)
    field(x0 + 135, y0 + 16, "Projection", "", 2.8)
    # first-angle projection symbol (ISO 5456-2)
    cx, cy = x0 + 150, y0 + 21
    s.add(f'<path d="M {cx - 7} {cy - 1.5} L {cx - 1} {cy - 2.6} L {cx - 1} {cy + 2.6} L {cx - 7} {cy + 1.5} Z" fill="none" stroke="#000" stroke-width="0.35"/>')
    s.add(f'<circle cx="{cx + 6}" cy="{cy}" r="2.6" fill="none" stroke="#000" stroke-width="0.35"/>'
          f'<circle cx="{cx + 6}" cy="{cy}" r="1.5" fill="none" stroke="#000" stroke-width="0.35"/>')
    s.line(cx - 8, cy, cx + 10, cy, 0.18, "3 1 0.5 1")
    s.text(x0 + 2, y0 + 30, "Thermomine – aquarium mine thermometer", size=2.5, anchor="start")
    s.text(x0 + 2, y0 + 37.5, title, size=5, anchor="start", weight="bold")
    field(x0, y0 + 40, "Drawing number", number, 5, "bold")
    field(x0 + 120, y0 + 40, "Revision", "A", 5, "bold")
    field(x0 + 150, y0 + 40, "Sheet", "1/1", 5)
    # notes above the title block
    ny = y0 - 6 - 5.2 * len(part_notes)
    s.text(x0, ny - 2, "Notes", size=3.5, anchor="start", weight="bold")
    for i, n in enumerate(part_notes):
        s.text(x0, ny + 4 + 5.2 * i, n, size=2.6, anchor="start")


def front(shape):
    s = shape.copy(); s.rotate(V(0, 0, 0), V(1, 0, 0), -90)      # view from -Y: u = x, v = z
    return s


def half_for_section(shape):
    keep = Part.makeBox(400, 200, 400, V(-200, 0, -100))         # keep y >= 0, look from -Y
    return front(shape.common(keep))


def section_label(v, u, v_mid, text_name="A"):
    pass


def section_line(view, u0, u1, name="A"):
    """Cutting plane in the top view along y = 0, arrows show the viewing direction (+Y)."""
    s = view.s
    (x0, y), (x1, _) = view.P(u0, 0), view.P(u1, 0)
    s.line(x0 - 6, y, x0, y, 0.7); s.line(x1, y, x1 + 6, y, 0.7)
    s.line(x0, y, x1, y, THIN, "12 2 2 2")
    for x in (x0 - 3, x1 + 3):
        s.line(x, y, x, y - 7, THIN); s.arrow(x, y - 7, -math.pi / 2)
        s.text(x, y - 9, name, size=5)


# ----------------------------------------------------------------------------- bottom part
def drawing_bottom():
    shape = Part.read(os.path.join(PRINT, "mine_bottom.step"))
    s = Sheet()
    fv = View(s, 100, 150)                   # front view, z = 0 at sheet y 150
    fv.projection(front(shape))
    fv.centre_v(0, 0, 113); fv.centre_h(98, -42, 42)
    fv.dim_v(0, 113, -30, -34.4, -60, "113")                     # overall height
    fv.dim_v(0, 18, 27.7, 27.7, 55, "18")                         # base height
    fv.dim_v(0, 98, 41.5, 41.5, 66, "98")                         # equator / sphere centre
    fv.dim_v(93.5, 102.5, -41.5, -41.5, -52, "9")                 # band height
    fv.dim_h(-41.5, 41.5, 102.5, 102.5, 124, "⌀83")               # band
    fv.dim_h(-6, 6, 30, 30, 36, "⌀12")                            # tether
    fv.dim_h(-27.7, 27.7, 0, 0, -10, "55.4 (A/F)")                # octagon across flats

    tv = View(s, 100, 222)                   # top view below (first-angle projection)
    tv.projection(shape)
    tv.centre_v(0, -46, 46); tv.centre_h(0, -46, 46)
    section_line(tv, -46, 46)
    tv.leader(math.cos(math.radians(11.25)) * 41.5, math.sin(math.radians(11.25)) * 41.5, 22, -8,
              "16× slot 3.5 × 6.5, 22.5° pitch")
    tv.leader(-37.0, 3.5, -6, -20, "note 6", anchor="end")
    tv.dim_h(0, -31.7, 0, 0, -57, "31.7")

    sv = View(s, 245, 150)                   # section A-A
    half = shape.common(Part.makeBox(400, 200, 400, V(-200, 0, -100)))
    sv.projection(front(half))
    sv.section_faces(shape.slice(V(0, 1, 0), 0.0))
    sv.centre_v(0, 0, 113)
    s.text(245, 17, "A–A", size=5)
    sv.dim_h(-37.5, 37.5, 98, 98, 124, "⌀75 (wall 2.5)")
    sv.dim_h(-34.4, 34.4, 108, 108, 117, "⌀68.8")
    sv.dim_v(103, 113, 37.5, 37.5, 52, "10")
    sv.dim_v(94.75, 101.25, 41.5, 41.5, 58, "6.5")
    sv.dim_h(-6.15, 6.15, 86, 86, 86.0001, "⌀12.3")
    sv.dim_v(78, 95, -6.15, -6.15, -18, "17")
    sv.dim_h(-8, 8, 66, 66, 66.0001, "⌀16")
    sv.dim_h(-3.5, 3.5, 40, 40, 40.0001, "⌀7")
    sv.dim_v(0, 15, -25.2, -25.2, -44, "15")
    sv.dim_h(-25.2, 25.2, 7, 7, -8, "50.4 (A/F)")
    sv.leader(27.0, 16.5, 16, -10, "ceiling 3, wall 2.5")
    sv.leader(34.8, 108.7, 18, -22, "bayonet: see note 4")

    notes = [
        "1  Print in HP MJF PA12, no supports; powder must drain from the open base.",
        "2  Base cavity: fill with dry sand, seal flush with aquarium-safe silicone.",
        "3  Unspecified radii/edges as modelled; reference model mine_bottom.step.",
        "4  Bayonet: 3 L-slots at 120°, depth to ⌀71.2, entry 13°, turn 30° clockwise,",
        "    channel height 3.1, 0.3 mm detent step at end of travel.",
        "5  LED pocket ⌀12.3 fits a 12 mm WS2811 bullet pixel (push fit).",
        "6  Probe clip ⌀12 × 16, bore ⌀6.4 for a ⌀6 DS18B20 probe, opening 4.6.",
        "7  5× horn ⌀8 with ⌀10 tip, 30° below the equator, 72° pitch.",
    ]
    frame(s, "Bottom part (base, tether, lower shell)", "TM-001-01", "≈ 68 g + sand", notes)
    path = os.path.join(HERE, "Thermomine_TM-001-01_bottom.svg")
    s.render(path)
    return path


# ----------------------------------------------------------------------------- cap
def drawing_cap():
    shape = Part.read(os.path.join(PRINT, "mine_cap.step"))     # printed position: z 0..49
    s = Sheet()
    fv = View(s, 100, 130)
    fv.projection(front(shape))
    fv.centre_v(0, 0, 49)
    fv.dim_v(0, 49, -34.07, -5, -62, "49")
    fv.dim_v(0, 7, 34.07, 34.07, 50, "7")
    fv.dim_h(-37.08, 37.08, 7, 7, -14, "⌀74.2")
    fv.leader(0, 49, 18, -10, "6× horn ⌀8, tip ⌀10")

    tv = View(s, 100, 215)
    tv.projection(shape)
    tv.centre_v(0, -45, 45); tv.centre_h(0, -45, 45)
    section_line(tv, -45, 45)
    tv.leader(math.cos(math.radians(36)) * 17.0, math.sin(math.radians(36)) * 17.0, 26, -18, "4× vent ⌀3")

    sv = View(s, 245, 130)
    half = shape.common(Part.makeBox(400, 200, 400, V(-200, 0, -100)))
    sv.projection(front(half))
    sv.section_faces(shape.slice(V(0, 1, 0), 0.0))
    sv.centre_v(0, 0, 49)
    s.text(245, 62, "A–A", size=5)
    sv.dim_h(-34.07, 34.07, 0, 0, -10, "⌀68.14")
    sv.dim_h(-32.07, 32.07, 3, 3, 3.0001, "⌀64.14")
    sv.dim_v(0, 11, -34.07, -34.07, -46, "11")
    sv.dim_v(1.5, 4.0, 35.3, 35.3, 48, "2.5")
    sv.leader(35.3, 2.8, 14, 14, "3× lug to ⌀70.6, 10° wide")
    sv.dim_h(-37.5, 37.5, 22, 22, 60, "⌀75 (wall 2.5)")

    notes = [
        "1  Print in HP MJF PA12, no supports; open side down or up as the service prefers.",
        "2  Collar ⌀68.14 runs in ⌀68.8 of TM-001-01: 0.3 mm radial clearance.",
        "3  Lugs engage the bayonet slots of TM-001-01; detent clicks at end of travel.",
        "4  Unspecified radii/edges as modelled; reference model mine_cap.step.",
        "5  Inside surfaces light colour (undyed or painted) for brighter glow.",
    ]
    frame(s, "Cap (top shell, bayonet collar)", "TM-001-02", "≈ 25 g", notes)
    path = os.path.join(HERE, "Thermomine_TM-001-02_cap.svg")
    s.render(path)
    return path


for p in (drawing_bottom(), drawing_cap()):
    print("[draw] wrote", os.path.basename(p), os.path.getsize(p), "bytes", flush=True)
