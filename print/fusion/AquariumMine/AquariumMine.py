"""Fusion script: builds the aquarium mine (bottom + cap) with native timeline features.

Same dimensions as print/build_step.py (the FreeCAD/STEP model). All values in mm here;
Fusion works in cm internally, so every length goes through mm().

Run: Utilities > ADD-INS > Scripts and Add-Ins > "+" next to My Scripts > pick this folder > Run.
A new design opens; if a step fails, the message names it.
"""
import math
import traceback

import adsk.core
import adsk.fusion

CZ, RO, RI = 98.0, 40.0, 37.5          # sphere centre height, outer / inner radius
SPLIT = CZ + 15.0                      # cap / bottom split plane
LUG_HALF = 5.0                         # bayonet lug half-width (deg)

app = adsk.core.Application.get()
ui = app.userInterface
VI = adsk.core.ValueInput
OP = adsk.fusion.FeatureOperations


def mm(v):
    return v / 10.0


def P(x, y, z):
    return adsk.core.Point3D.create(mm(x), mm(y), mm(z))


class Builder:
    def __init__(self, comp, main_name):
        self.c, self.main_name, self.f = comp, main_name, comp.features

    @property
    def main(self):
        return self.c.bRepBodies.itemByName(self.main_name)

    def tokens(self):
        return {b.entityToken for b in self.c.bRepBodies}

    def new_bodies(self, before):
        coll = adsk.core.ObjectCollection.create()
        for b in self.c.bRepBodies:
            if b.entityToken not in before:
                coll.add(b)
        return coll

    # ---- sketches -------------------------------------------------------------------------
    def _xz_sketch(self):
        return self.c.sketches.add(self.c.xZConstructionPlane)

    def _xy_sketch(self):
        return self.c.sketches.add(self.c.xYConstructionPlane)

    @staticmethod
    def _to(sk, x, y, z):
        return sk.modelToSketchSpace(P(x, y, z))

    def revolve(self, outline, op, name=None):
        """outline: list of ('L', (r, z)) / ('A', (r_mid, z_mid), (r, z)) steps in the r-z half plane, closed."""
        sk = self._xz_sketch()
        lines, arcs = sk.sketchCurves.sketchLines, sk.sketchCurves.sketchArcs
        start = self._to(sk, outline[0][1][0], 0, outline[0][1][1])
        cur = start
        for seg in outline[1:]:
            if seg[0] == "L":
                nxt = self._to(sk, seg[1][0], 0, seg[1][1])
                lines.addByTwoPoints(cur, nxt)
            else:
                mid = self._to(sk, seg[1][0], 0, seg[1][1])
                nxt = self._to(sk, seg[2][0], 0, seg[2][1])
                arcs.addByThreePoints(cur, mid, nxt)
            cur = nxt
        lines.addByTwoPoints(cur, start)
        inp = self.f.revolveFeatures.createInput(sk.profiles.item(0), self.c.zConstructionAxis, op)
        inp.setAngleExtent(False, VI.createByString("360 deg"))
        if op in (OP.JoinFeatureOperation, OP.CutFeatureOperation) and self.main:
            inp.participantBodies = [self.main]
        feat = self.f.revolveFeatures.add(inp)
        if name and op == OP.NewBodyFeatureOperation:
            feat.bodies.item(0).name = name
        return feat

    def rect_ring(self, r0, r1, z0, z1, op):
        return self.revolve([("L", (r0, z0)), ("L", (r1, z0)), ("L", (r1, z1)), ("L", (r0, z1))], op)

    def extrude_xy(self, draw, z0, z1, op):
        sk = self._xy_sketch()
        draw(sk)
        prof = sk.profiles.item(0)
        inp = self.f.extrudeFeatures.createInput(prof, op)
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(VI.createByReal(mm(z0)))
        inp.setDistanceExtent(False, VI.createByReal(mm(z1 - z0)))
        if op in (OP.JoinFeatureOperation, OP.CutFeatureOperation) and self.main:
            inp.participantBodies = [self.main]
        return self.f.extrudeFeatures.add(inp)

    def extrude_xz_sym(self, draw, length, op):
        sk = self._xz_sketch()
        draw(sk)
        inp = self.f.extrudeFeatures.createInput(sk.profiles.item(0), op)
        inp.setSymmetricExtent(VI.createByReal(mm(length)), True)
        if op in (OP.JoinFeatureOperation, OP.CutFeatureOperation) and self.main:
            inp.participantBodies = [self.main]
        return self.f.extrudeFeatures.add(inp)

    @staticmethod
    def polygon(sk, pts):
        lines = sk.sketchCurves.sketchLines
        sp = [adsk.core.Point3D.create(mm(x), mm(y), 0) for x, y in pts]
        for a, b in zip(sp, sp[1:] + sp[:1]):
            lines.addByTwoPoints(a, b)

    @staticmethod
    def sector(sk, r0, r1, a0, a1):
        def pt(r, a):
            return adsk.core.Point3D.create(mm(r * math.cos(math.radians(a))), mm(r * math.sin(math.radians(a))), 0)
        am = (a0 + a1) / 2
        lines, arcs = sk.sketchCurves.sketchLines, sk.sketchCurves.sketchArcs
        lines.addByTwoPoints(pt(r0, a0), pt(r1, a0))
        arcs.addByThreePoints(pt(r1, a0), pt(r1, am), pt(r1, a1))
        lines.addByTwoPoints(pt(r1, a1), pt(r0, a1))
        arcs.addByThreePoints(pt(r0, a1), pt(r0, am), pt(r0, a0))

    # ---- body operations ------------------------------------------------------------------
    def rotate(self, bodies, axis, deg):
        inp = self.f.moveFeatures.createInput2(bodies)
        inp.defineAsRotate(axis, VI.createByString(f"{deg} deg"))
        self.f.moveFeatures.add(inp)

    def lift(self, bodies, dz):
        inp = self.f.moveFeatures.createInput2(bodies)
        inp.defineAsTranslateXYZ(VI.createByReal(0), VI.createByReal(0), VI.createByReal(mm(dz)), True)
        self.f.moveFeatures.add(inp)

    def pattern(self, bodies, count):
        before = self.tokens()
        inp = self.f.circularPatternFeatures.createInput(bodies, self.c.zConstructionAxis)
        inp.quantity = VI.createByReal(count)
        inp.totalAngle = VI.createByString("360 deg")
        self.f.circularPatternFeatures.add(inp)
        for b in self.new_bodies(before):
            bodies.add(b)
        return bodies

    def combine(self, tools, op):
        inp = self.f.combineFeatures.createInput(self.main, tools)
        inp.operation = op
        inp.isKeepToolBodies = False
        self.f.combineFeatures.add(inp)

    # ---- parts of the mine ----------------------------------------------------------------
    def horn_tool(self, lat, az):
        """Horn built at the sphere centre pointing +Z, then turned to (lat, az) and lifted to CZ."""
        before = self.tokens()
        self.revolve([("L", (0, 37)), ("L", (4, 37)), ("L", (4, 38.8)), ("L", (6.5, 38.8)), ("L", (6.5, 41.8)),
                      ("L", (4, 41.8)), ("L", (4, 49)), ("A", (4.472, 54.236), (0, 57))], OP.NewBodyFeatureOperation)
        tool = self.new_bodies(before)
        if 90 - lat:
            self.rotate(tool, self.c.yConstructionAxis, 90 - lat)
        if az:
            self.rotate(tool, self.c.zConstructionAxis, az)
        self.lift(tool, CZ)
        return tool

    def radial_rod_tool(self, r, d0, d1, lat, az):
        before = self.tokens()
        self.rect_ring(0, r, d0, d1, OP.NewBodyFeatureOperation)
        tool = self.new_bodies(before)
        self.rotate(tool, self.c.yConstructionAxis, 90 - lat)
        self.rotate(tool, self.c.zConstructionAxis, az)
        self.lift(tool, CZ)
        return tool

    def sector_tool(self, r0, r1, a0, a1, z0, z1):
        before = self.tokens()
        self.extrude_xy(lambda sk: self.sector(sk, r0, r1, a0, a1), z0, z1, OP.NewBodyFeatureOperation)
        return self.new_bodies(before)


def user_params(design):
    params = [("outer_radius", "40 mm", "Sphere outer radius"), ("wall", "2.5 mm", "Shell wall"),
              ("split_height", "113 mm", "Cap/bottom split plane"), ("bayonet_clearance", "0.3 mm", "Lug to slot"),
              ("base_wall", "2.5 mm", "Hollow base wall"), ("base_top", "3 mm", "Hollow base ceiling"),
              ("slot_count", "16", "Glow slots in the band")]
    for name, val, note in params:
        if not design.userParameters.itemByName(name):
            unit = "" if val.isdigit() else "mm"
            design.userParameters.add(name, VI.createByString(val), unit, note)


def build_bottom(b):
    s = math.sqrt
    b.revolve([("L", (0, CZ - RO)), ("A", (28.284, CZ - 28.284), (s(RO**2 - 15**2), SPLIT)),
               ("L", (s(RI**2 - 15**2), SPLIT)), ("A", (26.517, CZ - 26.517), (0, CZ - RI))],
              OP.NewBodyFeatureOperation, name=b.main_name)                                   # shell
    b.rect_ring(37.3, 41.5, CZ - 4.5, CZ + 4.5, OP.JoinFeatureOperation)                        # band
    b.rect_ring(0, 6.0, 16, 62, OP.JoinFeatureOperation)                                        # tether
    b.rect_ring(0, 8.0, 58, 94, OP.JoinFeatureOperation)                                        # LED holder
    b.rect_ring(34.4, 37.5, CZ + 5, SPLIT, OP.JoinFeatureOperation)                              # bayonet ring
    octa = [(30 * math.cos(math.radians(22.5 + 45 * k)), 30 * math.sin(math.radians(22.5 + 45 * k))) for k in range(8)]
    b.extrude_xy(lambda sk: b.polygon(sk, octa), 0, 18, OP.JoinFeatureOperation)                # base
    ri = (30 * math.cos(math.radians(22.5)) - 2.5) / math.cos(math.radians(22.5))
    inner = [(ri * math.cos(math.radians(22.5 + 45 * k)), ri * math.sin(math.radians(22.5 + 45 * k))) for k in range(8)]
    b.extrude_xy(lambda sk: b.polygon(sk, inner), -1, 15, OP.CutFeatureOperation)               # hollow base
    b.extrude_xy(lambda sk: sk.sketchCurves.sketchCircles.addByCenterRadius(P(0, 0, 0), mm(6)), 0, 15.5,
                 OP.JoinFeatureOperation)                                                         # cable tube
    b.revolve([("L", (0, -1)), ("L", (3.5, -1)), ("L", (3.5, 78)), ("L", (6.15, 78)), ("L", (6.15, 95)), ("L", (0, 95))],
              OP.CutFeatureOperation)                                                             # bore + LED pocket
    b.extrude_xy(lambda sk: b.polygon(sk, [(0, -3.5), (34, -3.5), (34, 3.5), (0, 3.5)]), -1, 6,
                 OP.CutFeatureOperation)                                                          # cable notch
    b.extrude_xz_sym(lambda sk: sk.sketchCurves.sketchCircles.addByCenterRadius(b._to(sk, -31.7, 0, 9), mm(6)), 16,
                     OP.JoinFeatureOperation)                                                     # probe clip
    b.extrude_xz_sym(lambda sk: sk.sketchCurves.sketchCircles.addByCenterRadius(b._to(sk, -31.7, 0, 9), mm(3.2)), 18,
                     OP.CutFeatureOperation)

    def clip_slot(sk):
        pts = [b._to(sk, x, 0, z) for x, z in ((-40, 6.7), (-33, 6.7), (-33, 11.3), (-40, 11.3))]
        for p0, p1 in zip(pts, pts[1:] + pts[:1]):
            sk.sketchCurves.sketchLines.addByTwoPoints(p0, p1)
    b.extrude_xz_sym(clip_slot, 20, OP.CutFeatureOperation)
    b.combine(b.pattern(b.horn_tool(-30, 36), 5), OP.JoinFeatureOperation)                     # 5 lower horns
    before = b.tokens()                                                                           # 16 glow slots
    b.extrude_xy(lambda sk: b.polygon(sk, [(34, -1.75), (46, -1.75), (46, 1.75), (34, 1.75)]), CZ - 3.25, CZ + 3.25,
                 OP.NewBodyFeatureOperation)
    slot = b.new_bodies(before)
    b.rotate(slot, b.c.zConstructionAxis, 11.25)
    b.combine(b.pattern(slot, 16), OP.CutFeatureOperation)
    a = 60                                                                                        # bayonet slots x3
    entry = b.sector_tool(34.0, 35.6, a - LUG_HALF - 1.5, a + LUG_HALF + 1.5, 107.2, SPLIT + 1)
    chan = b.sector_tool(34.0, 35.6, a - 30 - LUG_HALF - 1.5, a + LUG_HALF + 1.5, 107.2, 110.3)
    for t in chan:
        entry.add(t)
    b.combine(b.pattern(entry, 3), OP.CutFeatureOperation)
    d0 = a - 30 + LUG_HALF + 2.0                                                                  # 0.3 mm detent ridge
    b.combine(b.pattern(b.sector_tool(35.0, 35.7, d0 - 0.05, d0 + 1.05, 107.2, 110.3), 3), OP.JoinFeatureOperation)


def build_cap(b):
    s = math.sqrt
    b.revolve([("L", (s(RO**2 - 15**2), SPLIT)), ("A", (20.0, CZ + 34.641), (0, CZ + RO)), ("L", (0, CZ + RI)),
               ("A", (18.75, CZ + 32.476), (s(RI**2 - 15**2), SPLIT))], OP.NewBodyFeatureOperation, name=b.main_name)
    b.rect_ring(32.07, 34.07, CZ + 8, CZ + 19, OP.JoinFeatureOperation)                          # bayonet collar
    b.combine(b.pattern(b.sector_tool(33.0, 35.3, 60 - 30 - LUG_HALF, 60 - 30 + LUG_HALF, 107.5, 110.0), 3),
              OP.JoinFeatureOperation)                                                            # 3 lugs
    b.combine(b.horn_tool(90, 0), OP.JoinFeatureOperation)                                      # top horn
    b.combine(b.pattern(b.horn_tool(42, 0), 5), OP.JoinFeatureOperation)                        # 5 upper horns
    vents = adsk.core.ObjectCollection.create()                                                   # 4 air vents
    for i in range(4):
        for t in b.radial_rod_tool(1.5, 30, 45, 65, i * 72 + 36):
            vents.add(t)
    b.combine(vents, OP.CutFeatureOperation)


def run(context):
    step = "start"
    try:
        app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = adsk.fusion.Design.cast(app.activeProduct)
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        user_params(design)
        root = design.rootComponent
        for name, builder in (("Mine_Bottom", build_bottom), ("Mine_Cap", build_cap)):
            step = name
            occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
            occ.component.name = name
            builder(Builder(occ.component, name))
        vol = {o.component.name: sum(bd.volume for bd in o.component.bRepBodies) * 1.0 for o in root.occurrences}
        ui.messageBox("Aquarium mine built.\n\n" + "\n".join(f"{k}: {v:.2f} cm³ (STEP: "
                      f"{'66.62' if 'Bottom' in k else '25.07'} cm³)" for k, v in vol.items()))
    except Exception:
        ui.messageBox(f"Failed while building {step}:\n{traceback.format_exc()}")
