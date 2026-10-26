"""Rebuild the aquarium mine as exact B-rep solids and export STEP (mm).
Same dimensions and boolean steps as the Blender model that produced the STLs.
   freecadcmd build_step.py
"""
import math
import os

import FreeCAD as App
import Part
from FreeCAD import Vector as V

OUT = os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else os.getcwd()
CZ, RO, RI = 98.0, 40.0, 37.5
SPLIT = CZ + 15.0
CTR = V(0, 0, CZ)


def sph(r, c):
    return Part.makeSphere(r, c)


def inner_sphere():
    """Cavity sphere, turned so its seam and poles do not coincide with the outer sphere (OCC boolean bug)."""
    s = Part.makeSphere(RI, V(0, 0, 0))
    s.rotate(V(0, 0, 0), V(1, 0.3, 0), 17.0)
    s.translate(CTR)
    return s


def cyl(r, p0, p1):
    p0, p1 = V(*p0), V(*p1)
    return Part.makeCylinder(r, (p1 - p0).Length, p0, p1 - p0)


def box(size, centre, rotz=0.0):
    sx, sy, sz = size
    b = Part.makeBox(sx, sy, sz, V(-sx / 2, -sy / 2, -sz / 2))
    b.rotate(V(0, 0, 0), V(0, 0, 1), math.degrees(rotz))
    b.translate(V(*centre))
    return b


def sector(r0, r1, z0, z1, a0, a1):
    """Ring sector between radii r0..r1, heights z0..z1, angles a0..a1 (degrees)."""
    span = a1 - a0
    outer = Part.makeCylinder(r1, z1 - z0, V(0, 0, z0), V(0, 0, 1), span)
    inner = Part.makeCylinder(r0, z1 - z0, V(0, 0, z0), V(0, 0, 1), span)
    s = outer.cut(inner)
    s.rotate(V(0, 0, 0), V(0, 0, 1), a0)
    return s


def sph_dir(lat, az):
    la, a = math.radians(lat), math.radians(az)
    return V(math.cos(la) * math.cos(a), math.cos(la) * math.sin(a), math.sin(la))


def horn(d):
    stem = cyl(4.0, CTR + d * 37, CTR + d * 52)
    tip = sph(5.0, CTR + d * 52)
    collar = cyl(6.5, CTR + d * 38.8, CTR + d * 41.8)
    return [stem, tip, collar]


def step(msg):
    print('[step] ' + msg, flush=True)


def cut_each(shape, cutters, label):
    for k, c in enumerate(cutters):
        step(f'{label} cut {k + 1}/{len(cutters)}')
        shape = shape.cut(c)
    return shape


def fuse(shapes):
    s = shapes[0].fuse(shapes[1:]) if len(shapes) > 1 else shapes[0]
    return s.removeSplitter()


def octagon_prism(r, z0, z1):
    pts = [V(r * math.cos(math.radians(22.5 + 45 * k)), r * math.sin(math.radians(22.5 + 45 * k)), z0) for k in range(8)]
    face = Part.Face(Part.makePolygon(pts + [pts[0]]))
    return face.extrude(V(0, 0, z1 - z0))


# ---------------- bottom part ----------------
add = [sph(RO, CTR), cyl(41.5, (0, 0, CZ - 4.5), (0, 0, CZ + 4.5)), cyl(6.0, (0, 0, 16), (0, 0, 62)),
       octagon_prism(30.0, 0, 18), cyl(6.0, (-31.7, -8, 9), (-31.7, 8, 9))]
for i in range(5):
    add += horn(sph_dir(-30, i * 72 + 36))
step('bottom: fuse outer'); bottom = fuse(add)
step('bottom: hollow'); bottom = bottom.cut(inner_sphere())
bottom = fuse([bottom, cyl(8.0, (0, 0, 58), (0, 0, 94)), cyl(37.5, (0, 0, CZ + 5), (0, 0, SPLIT + 1))])
# hollow base, open at the bottom: 2.5 mm walls, 3 mm ceiling, filled with sand and sealed with silicone by the user
BASE_WALL, BASE_TOP = 2.5, 3.0
inner_r = (30.0 * math.cos(math.radians(22.5)) - BASE_WALL) / math.cos(math.radians(22.5))
step('bottom: hollow base'); bottom = bottom.cut(octagon_prism(inner_r, -1.0, 18.0 - BASE_TOP))
# keep a tube round the cable bore so sand stays out of the tether
bottom = fuse([bottom, cyl(6.0, (0, 0, 0), (0, 0, 18.0 - BASE_TOP + 0.5))])
cuts = [cyl(6.15, (0, 0, 78), (0, 0, 95)), cyl(3.5, (0, 0, -1), (0, 0, 80)),
        box((34, 7, 7), (17, 0, 2.5)), cyl(3.2, (-31.7, -9, 9), (-31.7, 9, 9)), box((7, 20, 4.6), (-36.5, 0, 9)),
        cyl(34.4, (0, 0, CZ + 4), (0, 0, SPLIT + 2))]
for i in range(16):
    a = math.radians(i * 22.5 + 11.25)
    cuts.append(box((12, 3.5, 6.5), (math.cos(a) * 40, math.sin(a) * 40, CZ), a))
LUG_HALF = 5.0
for i in range(3):                      # bayonet: entry, locking channel with a 0.3 mm detent step
    a = i * 120 + 60
    end, d0 = a - 30 - LUG_HALF - 1.5, a - 30 + LUG_HALF + 2.0
    cuts += [sector(34.0, 35.6, 107.2, SPLIT + 1, a - LUG_HALF - 1.5, a + LUG_HALF + 1.5),
             sector(34.0, 35.6, 107.2, 110.3, end, d0 + 0.05),
             sector(34.0, 35.0, 107.2, 110.3, d0 - 0.1, d0 + 1.1),
             sector(34.0, 35.6, 107.2, 110.3, d0 + 0.95, a + LUG_HALF + 1.5)]
bottom = cut_each(bottom, cuts, 'bottom')
bottom = bottom.common(box((200, 200, SPLIT + 10), (0, 0, (SPLIT - 10) / 2))).removeSplitter()

# ---------------- cap ----------------
add = [sph(RO, CTR)] + horn(V(0, 0, 1))
for i in range(5):
    add += horn(sph_dir(42, i * 72))
step('cap: fuse outer'); cap = fuse(add)
step('cap: hollow'); cap = cap.cut(inner_sphere())
cap = cap.common(box((200, 200, 100), (0, 0, SPLIT + 50)))
lugs = [sector(33.0, 35.3, 107.5, 110.0, i * 120 + 60 - 30 - LUG_HALF, i * 120 + 60 - 30 + LUG_HALF) for i in range(3)]
cap = fuse([cap, cyl(34.07, (0, 0, CZ + 8), (0, 0, CZ + 19))] + lugs)
vents = [cyl(1.5, CTR + sph_dir(65, i * 72 + 36) * 30, CTR + sph_dir(65, i * 72 + 36) * 45) for i in range(4)]
cap = cut_each(cap, vents + [cyl(32.07, (0, 0, CZ + 7), (0, 0, CZ + 19.4))], 'cap').removeSplitter()

# ---------------- report + export ----------------
for name, s in (("bottom", bottom), ("cap", cap)):
    bb = s.BoundBox
    print(f"[step] {name}: valid={s.isValid()} solids={len(s.Solids)} faces={len(s.Faces)} "
          f"volume={s.Volume / 1000:.2f} cm3 z={bb.ZMin:.1f}..{bb.ZMax:.1f} size={bb.XLength:.1f}x{bb.YLength:.1f}x{bb.ZLength:.1f}")

bottom.exportStep(os.path.join(OUT, "mine_bottom.step"))
cap_print = cap.copy(); cap_print.translate(V(0, 0, -106.0))          # flat on the bed, like the STL
cap_print.exportStep(os.path.join(OUT, "mine_cap.step"))
assembly = Part.makeCompound([bottom, cap])                            # closed position, for checking fit
assembly.exportStep(os.path.join(OUT, "mine_assembly.step"))
print("[step] written:", ", ".join(f for f in sorted(os.listdir(OUT)) if f.endswith(".step")))
