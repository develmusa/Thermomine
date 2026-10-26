"""Turn KiCad outputs into JLCPCB upload files: gerbers zip, BOM csv, CPL csv."""
import csv
import os
import sys
import zipfile
from collections import OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_board import HERE, PARTS

FAB = os.path.join(HERE, "fab")

# Gerbers + drill in one zip
with zipfile.ZipFile(os.path.join(FAB, "aquarium_mine_ctrl_gerbers.zip"), "w", zipfile.ZIP_DEFLATED) as z:
    gdir = os.path.join(FAB, "gerber")
    for f in sorted(os.listdir(gdir)):
        z.write(os.path.join(gdir, f), f)

# BOM grouped by LCSC part
groups = OrderedDict()
for ref, (fp_id, value, x, y, rot, padnets, mpn, lcsc) in PARTS.items():
    if not lcsc:
        continue  # mounting holes
    g = groups.setdefault(lcsc, {"value": value, "fp": fp_id[1], "mpn": mpn, "refs": []})
    if g["value"] != value:
        g["value"] = mpn  # grouped parts with different labels (J2/J3, SW1/SW2)
    g["refs"].append(ref)
with open(os.path.join(FAB, "aquarium_mine_ctrl_bom.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Comment", "Designator", "Footprint", "Quantity", "Manufacturer Part", "LCSC Part #"])
    for lcsc, g in groups.items():
        w.writerow([g["value"], ",".join(g["refs"]), g["fp"], len(g["refs"]), g["mpn"], lcsc])

# CPL from KiCad's position export (KiCad writes Y negative; JLC wants the KiCad sign convention as exported)
with open(os.path.join(FAB, "positions_raw.csv")) as src, \
        open(os.path.join(FAB, "aquarium_mine_ctrl_cpl.csv"), "w", newline="") as dst:
    w = csv.writer(dst)
    w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
    for row in csv.DictReader(src):
        if not PARTS.get(row["Ref"], (None,) * 8)[7]:
            continue
        w.writerow([row["Ref"], f'{float(row["PosX"]):.3f}mm', f'{float(row["PosY"]):.3f}mm',
                    "Top" if row["Side"] == "top" else "Bottom", f'{float(row["Rot"]):.0f}'])
print("BOM lines:", len(groups), "| parts placed:", sum(len(g["refs"]) for g in groups.values()))
