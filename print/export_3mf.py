"""Exact bounds check of the STEP parts + 3MF export for the printer (mm).
   freecadcmd export_3mf.py
"""
import os

import FreeCAD as App
import Mesh
import MeshPart
import Part
from FreeCAD import Vector as V

HERE = os.getcwd()
parts = {}
for name in ("mine_bottom", "mine_cap"):
    shape = Part.read(os.path.join(HERE, f"{name}.step"))
    bb = shape.optimalBoundingBox()
    print(f"[3mf] {name}: exact size {bb.XLength:.2f} x {bb.YLength:.2f} x {bb.ZLength:.2f} mm, z {bb.ZMin:.2f}..{bb.ZMax:.2f}", flush=True)
    m = MeshPart.meshFromShape(Shape=shape, LinearDeflection=0.01, AngularDeflection=0.08, Relative=False)
    print(f"[3mf] {name}: {m.CountFacets} triangles, closed={m.isSolid()}, non-manifold={m.hasNonManifolds()}, "
          f"self-intersections={m.hasSelfIntersections()}, volume={m.Volume / 1000:.2f} cm3", flush=True)
    parts[name] = m
    m.write(os.path.join(HERE, f"{name}.3mf"))
    m.write(os.path.join(HERE, f"{name}.stl"))          # refresh the STLs from the exact solids too

# one print-ready 3MF with both parts side by side on the bed
doc = App.newDocument("plate")
cap = parts["mine_cap"].copy(); cap.translate(-cap.BoundBox.Center.x + 110, -cap.BoundBox.Center.y, 0)
for label, m in (("mine_bottom", parts["mine_bottom"]), ("mine_cap", cap)):
    f = doc.addObject("Mesh::Feature", label); f.Mesh = m
Mesh.export(list(doc.Objects), os.path.join(HERE, "mine_print_plate.3mf"))
print("[3mf] written:", ", ".join(sorted(f for f in os.listdir(HERE) if f.endswith((".3mf", ".step", ".stl")))), flush=True)
