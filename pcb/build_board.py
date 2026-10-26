"""Generate the aquarium mine controller PCB (KiCad 10, pcbnew API).

Run with KiCad's Python:
  python3 -I build_board.py place   -> aquarium_mine_ctrl.kicad_pcb + .dsn for freerouting
  python3 -I build_board.py finish  -> imports .ses, pours GND, saves the board
"""
import os
import sys

sys.path.insert(0, os.environ.get("KICAD_PY", "/nix/store/h5p54wmx4s217irx8hwgg5vbirlyvdff-kicad-base-10.0.7/lib/python3.14/site-packages"))
import pcbnew

FP = os.environ.get("KICAD_FP", "/nix/store/47862rscpxscgqi0vx5var279vf8vpyj-kicad-footprints-25a0b01dd7/share/kicad/footprints/")
HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(HERE, "aquarium_mine_ctrl.kicad_pcb")
DSN = os.path.join(HERE, "aquarium_mine_ctrl.dsn")
SES = os.path.join(HERE, "aquarium_mine_ctrl.ses")

MM = pcbnew.FromMM
BOARD = (100.0, 100.0, 158.0, 142.0)   # x0, y0, x1, y1 in mm

R0603 = ("Resistor_SMD", "R_0603_1608Metric")
C0603 = ("Capacitor_SMD", "C_0603_1608Metric")
C0805 = ("Capacitor_SMD", "C_0805_2012Metric")
BTN = ("Button_Switch_SMD", "SW_Push_1P1T_XKB_TS-1187A")
TERM = ("TerminalBlock_Phoenix", "TerminalBlock_Phoenix_MKDS-1,5-3-5.08_1x03_P5.08mm_Horizontal")
HOLE = ("MountingHole", "MountingHole_3.2mm_M3")

# ref: (footprint, value, x, y, rotation, {pad: net}, MPN, LCSC)
PARTS = {
    "U1": (("RF_Module", "ESP32-C3-WROOM-02"), "ESP32-C3-WROOM-02-N4", 129.0, 118.5, 0,
           {"1": "+3V3", "2": "EN", "3": "TEMP_DQ", "4": "LED_3V3", "7": "IO8", "8": "IO9",
            "9": "GND", "13": "USB_DM", "14": "USB_DP", "16": "IO2", "19": "GND"},
           "ESP32-C3-WROOM-02-N4", "C2934560"),
    "J1": (("Connector_USB", "USB_C_Receptacle_HRO_TYPE-C-31-M-12"), "USB-C", 153.4, 119.5, 90,
           {"A1": "GND", "A12": "GND", "B1": "GND", "B12": "GND", "SH": "GND",
            "A4": "VBUS", "A9": "VBUS", "B4": "VBUS", "B9": "VBUS",
            "A5": "CC1", "B5": "CC2", "A6": "USB_DP", "B6": "USB_DP", "A7": "USB_DM", "B7": "USB_DM"},
           "TYPE-C-31-M-12", "C165948"),
    "U2": (("Package_TO_SOT_SMD", "SOT-223-3_TabPin2"), "AMS1117-3.3", 111.5, 128.5, 0,
           {"1": "GND", "2": "+3V3", "3": "VBUS"}, "AMS1117-3.3", "C6186"),
    "U3": (("Package_TO_SOT_SMD", "SOT-23-5"), "74AHCT1G125", 126.0, 128.2, 0,
           {"1": "GND", "2": "LED_3V3", "3": "GND", "4": "LED_5V", "5": "VBUS"},
           "74AHCT1G125DBVTG4", "C2870384"),
    "J2": (TERM, "LED +5V/DIN/GND", 120.0, 136.5, 0, {"1": "VBUS", "2": "LED_DIN", "3": "GND"},
           "KF301-5.0-3P", "C474882"),
    "J3": (TERM, "PROBE GND/DQ/3V3", 137.0, 136.5, 0, {"1": "GND", "2": "TEMP_DQ", "3": "+3V3"},
           "KF301-5.0-3P", "C474882"),
    "SW1": (BTN, "RESET", 104.5, 112.5, 0, {"1": "EN", "2": "GND"}, "TS-1187A-B-A-B", "C318884"),
    "SW2": (BTN, "BOOT", 104.5, 120.0, 0, {"1": "IO9", "2": "GND"}, "TS-1187A-B-A-B", "C318884"),
    "C1": (C0805, "10uF", 110.0, 135.0, 0, {"1": "VBUS", "2": "GND"}, "CL21A106KAYNNNE", "C15850"),
    "C2": (C0805, "22uF", 114.0, 135.0, 0, {"1": "+3V3", "2": "GND"}, "CL21A226MAQNNNE", "C45783"),
    "C3": (C0805, "10uF", 110.6, 107.5, 90, {"1": "+3V3", "2": "GND"}, "CL21A106KAYNNNE", "C15850"),
    "C4": (C0603, "100nF", 113.2, 107.5, 90, {"1": "+3V3", "2": "GND"}, "CC0603KRX7R9BB104", "C14663"),
    "C5": (C0603, "1uF", 113.2, 112.5, 90, {"1": "EN", "2": "GND"}, "CL10A105KB8NNNC", "C15849"),
    "C6": (C0603, "100nF", 122.4, 128.2, 90, {"1": "VBUS", "2": "GND"}, "CC0603KRX7R9BB104", "C14663"),
    "R1": (R0603, "10k", 110.6, 112.5, 90, {"1": "+3V3", "2": "EN"}, "0603WAF1002T5E", "C25804"),
    "R2": (R0603, "10k", 139.4, 128.2, 0, {"1": "+3V3", "2": "IO2"}, "0603WAF1002T5E", "C25804"),
    "R3": (R0603, "10k", 113.2, 120.0, 90, {"1": "+3V3", "2": "IO8"}, "0603WAF1002T5E", "C25804"),
    "R4": (R0603, "5.1k", 146.6, 113.5, 90, {"1": "CC1", "2": "GND"}, "0603WAF5101T5E", "C23186"),
    "R5": (R0603, "5.1k", 146.6, 125.5, 90, {"1": "CC2", "2": "GND"}, "0603WAF5101T5E", "C23186"),
    "R6": (R0603, "4.7k", 143.0, 128.2, 0, {"1": "+3V3", "2": "TEMP_DQ"}, "0603WAF4701T5E", "C23162"),
    "R7": (R0603, "330", 131.0, 128.2, 0, {"1": "LED_5V", "2": "LED_DIN"}, "0603WAF3300T5E", "C23138"),
    "H1": (HOLE, "M3", 103.5, 103.5, 0, {}, None, None),
    "H2": (HOLE, "M3", 154.5, 103.5, 0, {}, None, None),
    "H3": (HOLE, "M3", 103.5, 138.5, 0, {}, None, None),
    "H4": (HOLE, "M3", 154.5, 138.5, 0, {}, None, None),
}

POWER_NETS = ("GND", "VBUS", "+3V3")


def setup_rules(board):
    ds = board.GetDesignSettings()
    ds.m_MinClearance = MM(0.2)
    ds.m_TrackMinWidth = MM(0.15)   # router necks down to 0.187 at fine-pitch pins; JLC 2-layer min is ~0.1
    ds.m_ViasMinSize = MM(0.6)
    ds.m_MinThroughDrill = MM(0.3)
    ds.m_CopperEdgeClearance = MM(0.25)  # JLC minimum is 0.2
    ns = ds.m_NetSettings
    default = ns.GetDefaultNetclass()
    default.SetClearance(MM(0.2)); default.SetTrackWidth(MM(0.25))
    default.SetViaDiameter(MM(0.6)); default.SetViaDrill(MM(0.3))
    power = pcbnew.NETCLASS("Power")
    power.SetClearance(MM(0.2)); power.SetTrackWidth(MM(0.5))
    power.SetViaDiameter(MM(0.8)); power.SetViaDrill(MM(0.4))
    ns.SetNetclass("Power", power)
    for n in POWER_NETS:
        ns.SetNetclassPatternAssignment(n, "Power")


def outline(board):
    x0, y0, x1, y1 = BOARD
    pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    for a, b in zip(pts, pts[1:] + pts[:1]):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1]))); s.SetEnd(pcbnew.VECTOR2I(MM(b[0]), MM(b[1])))
        s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.1))
        board.Add(s)


def silk_text(board, text, x, y, size=1.0, layer=pcbnew.F_SilkS):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(text); t.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
    t.SetLayer(layer); t.SetTextSize(pcbnew.VECTOR2I(MM(size), MM(size))); t.SetTextThickness(MM(0.15))
    if layer == pcbnew.B_SilkS:
        t.SetMirrored(True)
    board.Add(t)


def place():
    board = pcbnew.CreateEmptyBoard()
    board.SetCopperLayerCount(2)
    setup_rules(board)
    outline(board)
    nets = {}
    for ref, (fp_id, value, x, y, rot, padnets, mpn, lcsc) in PARTS.items():
        for n in padnets.values():
            if n not in nets:
                ni = pcbnew.NETINFO_ITEM(board, n); board.Add(ni); nets[n] = ni
    for ref, (fp_id, value, x, y, rot, padnets, mpn, lcsc) in PARTS.items():
        fp = pcbnew.FootprintLoad(FP + fp_id[0] + ".pretty", fp_id[1])
        if fp is None:
            raise SystemExit(f"footprint not found: {fp_id}")
        fp.SetReference(ref); fp.SetValue(value)
        fp.Reference().SetLayer(pcbnew.F_Fab)  # keep refs on the assembly drawing, not silk
        fp.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
        fp.SetOrientationDegrees(rot)
        fp.Value().SetLayer(pcbnew.F_Fab)
        if mpn:
            for key, val in (("MPN", mpn), ("LCSC", lcsc)):
                fp.SetField(key, val)
                f = fp.GetField(key)
                f.SetVisible(False); f.SetLayer(pcbnew.F_Fab)
        if ref == "U1":
            # drop the 0.2 mm thermal vias in the GND pad (below standard fab drill size)
            for pad in [p for p in fp.Pads() if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]:
                fp.Remove(pad)
        board.Add(fp)
        for pad in fp.Pads():
            n = padnets.get(pad.GetNumber())
            if n:
                pad.SetNet(nets[n])
    silk_text(board, "AQUARIUM MINE v1", 129.0, 104.5, 1.2)
    # per-pin labels under the screw terminals, on both sides
    for x0, names in ((120.0, ("+5V", "DIN", "GND")), (137.0, ("GND", "DQ", "3V3"))):
        for k, name in enumerate(names):
            silk_text(board, name, x0 + 5.08 * k, 139.9, 0.8, pcbnew.B_SilkS)
    silk_text(board, "RST", 104.5, 108.6, 0.8)
    silk_text(board, "BOOT", 104.5, 123.9, 0.8)
    pcbnew.SaveBoard(PCB, board)
    write_project_rules()
    board = pcbnew.LoadBoard(PCB)
    ok = pcbnew.ExportSpecctraDSN(board, DSN)
    print("saved", PCB, "dsn:", ok, "nets:", len(nets))


def add_zone(board, layer, net):
    x0, y0, x1, y1 = BOARD
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    z.SetNet(board.FindNet(net))
    z.SetLocalClearance(MM(0.25))
    z.SetMinThickness(MM(0.25))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(MM(0.3)); z.SetThermalReliefSpokeWidth(MM(0.4))
    o = z.Outline()
    o.NewOutline()
    for px, py in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        o.Append(MM(px), MM(py))
    z.SetAssignedPriority(0)
    board.Add(z)


def write_project_rules():
    """KiCad 10 keeps DRC limits in the .kicad_pro; pcbnew saves defaults there, so set ours."""
    import json
    pro = PCB.replace(".kicad_pcb", ".kicad_pro")
    if os.path.exists(pro):
        d = json.load(open(pro))
    else:
        # pcbnew does not write a project file for a new board; KiCad fills in any missing keys
        d = {"meta": {"filename": os.path.basename(pro), "version": 3},
             "board": {"design_settings": {"rules": {}}},
             "net_settings": {"classes": [{"name": "Default"}], "meta": {"version": 4}}}
    rules = d["board"]["design_settings"]["rules"]
    rules.update(min_clearance=0.15, min_track_width=0.15, min_copper_edge_clearance=0.25,
                 min_via_diameter=0.6, min_through_hole_diameter=0.3)
    ns = d.setdefault("net_settings", {})
    base = next(c for c in ns["classes"] if c["name"] == "Default")
    base.update(track_width=0.25, clearance=0.2, via_diameter=0.6, via_drill=0.3)
    power = dict(base, name="Power", track_width=0.5, via_diameter=0.8, via_drill=0.4, priority=0)
    ns["classes"] = [base, power]
    ns["netclass_patterns"] = [{"netclass": "Power", "pattern": n} for n in POWER_NETS]
    json.dump(d, open(pro, "w"), indent=2)


def finish():
    board = pcbnew.LoadBoard(PCB)
    if not pcbnew.ImportSpecctraSES(board, SES):
        raise SystemExit("SES import failed")
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        add_zone(board, layer, "GND")
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(PCB, board)
    write_project_rules()
    tracks = [t for t in board.GetTracks() if t.GetClass() == "PCB_TRACK"]
    vias = [t for t in board.GetTracks() if t.GetClass() == "PCB_VIA"]
    print("finished:", len(tracks), "tracks,", len(vias), "vias")


if __name__ == "__main__":
    {"place": place, "finish": finish}[sys.argv[1]]()
