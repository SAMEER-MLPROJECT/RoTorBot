"""RoToRBot detailed CAD model (CadQuery). Real-dimension component models placed inside the
envelopes defined in layout.py, so the mass budget and centre of gravity stay consistent.
Units: mm. Frame: origin at the sphere centre, x forward, y left (along the fixed axle), z up.
Run:  pip install -r requirements.txt  &&  python cad_detail.py
Outputs: build/RoToRBot_assembly.step, build/stl/*.stl, build/parts.json"""
import math, json, os, shutil
import cadquery as cq
from layout import R, R_IN, BAND_T, props

Rm, Ri = R * 1000, R_IN * 1000
shutil.rmtree("build/stl", ignore_errors=True); os.makedirs("build/stl", exist_ok=True)
parts = []
def add(name, shape, colour, group="fixed", opacity=1.0):
    parts.append((name, shape, colour, group, opacity))

# ---------- helpers ----------
def bx(cx, cy, cz, dx, dy, dz, f=0.0, sel="|Z"):
    b = cq.Workplane("XY").box(dx, dy, dz)
    if f:
        try: b = b.edges(sel).fillet(f)
        except Exception: pass
    return b.translate((cx, cy, cz))
def cy_y(r, y0, y1, x=0.0, z=0.0, rin=0.0):
    w = cq.Workplane("XZ", origin=(x, y0, z)).circle(r)
    if rin: w = w.circle(rin)
    return w.extrude(-(y1 - y0))
def cy_x(r, x0, x1, y=0.0, z=0.0):
    return cq.Workplane("YZ", origin=(x0, y, z)).circle(r).extrude(x1 - x0)
def cy_z(r, z0, z1, x=0.0, y=0.0, rin=0.0):
    w = cq.Workplane("XY", origin=(x, y, z0)).circle(r)
    if rin: w = w.circle(rin)
    return w.extrude(z1 - z0)
def toothed_y(r_o, r_r, n, y0, width, x=0.0, z=0.0, bore=0.0):
    pts = []
    for k in range(n):
        a0 = 2 * math.pi * k / n; p = 2 * math.pi / n
        for frac, rr in ((0.0, r_o), (0.42, r_o), (0.50, r_r), (0.86, r_r), (0.94, r_o)):
            a = a0 + frac * p
            pts.append((r_o * 0 + rr * math.cos(a), rr * math.sin(a)))
    w = cq.Workplane("XZ", origin=(x, y0, z)).polyline(pts).close().extrude(-width)
    if bore: w = w.cut(cy_y(bore, y0 - 1, y0 + width + 1, x=x, z=z))
    return w
def union(*ws):
    out = ws[0]
    for w in ws[1:]: out = out.union(w)
    return out

AL, AL2, STEEL, BLK, PCBG = "#a0aec0", "#7d8790", "#4a4a4a", "#1f2328", "#2f6b3a"

# ---------- shell (rotates) ----------
shell = cq.Workplane("XY").sphere(Rm).cut(cq.Workplane("XY").sphere(Ri)).cut(cy_y(36, -Rm - 5, Rm + 5))
for sgn, tag in ((1, "L"), (-1, "R")):
    half = shell.intersect(bx(0, sgn * (Rm + 5) / 2, 0, 2 * Rm + 10, Rm + 5, 2 * Rm + 10))
    add(f"Shell hemisphere {tag} (PC)", half, "#cfd8e3", "shell", 0.22)
band = cq.Workplane("XY").sphere(Rm + BAND_T * 1000).cut(cq.Workplane("XY").sphere(Rm)).intersect(bx(0, 0, 0, 2 * Rm + 20, 60, 2 * Rm + 20))
add("Traction band 60 mm", band, "#2a2a2a", "shell")
flange = cy_y(Ri, -4, 4).cut(cy_y(Ri - 16, -5, 5))
for k in range(16):  # bolt heads around the flange
    a = 2 * math.pi * k / 16; rr = Ri - 8
    flange = flange.union(cy_y(3.5, 4, 7, x=rr * math.cos(a), z=rr * math.sin(a)))
add("Equator flange ring + M4 bolts", flange, "#9aa5b1", "shell")
for sgn, tag in ((1, "L"), (-1, "R")):
    y_in = math.sqrt(Ri ** 2 - 55 ** 2) - 1
    ya, yb = (y_in - 12, y_in) if sgn > 0 else (-y_in, -y_in + 12)
    hub = cy_y(55, ya, yb, rin=18.5)
    for k in range(6):
        a = 2 * math.pi * k / 6
        hub = hub.cut(cy_y(2.6, ya - 1, yb + 1, x=45 * math.cos(a), z=45 * math.sin(a)))
    add(f"Pole hub {tag} (aluminium)", hub, "#b0b7bf", "shell")
    add(f"Pole hub {tag} 6805 bearing", cy_y(18.5, ya - 1, ya + 6, rin=12.6), "#d9dee3", "shell")
    py = 272 if sgn > 0 else -287
    pul = toothed_y(42.4, 40.3, 54, py, 15, bore=18.5)
    pul = pul.union(cy_y(44.5, py - 1.2, py, rin=18.5)).union(cy_y(44.5, py + 15, py + 16.2, rin=18.5))
    add(f"Hub pulley 54T {tag} HTD-5M", pul, "#e2e8f0", "shell")

# ---------- fixed axle + camera pods ----------
add("Fixed shaft 25 mm Al tube", cy_y(12.5, -370, 370, rin=10), "#8c96a0")
for sgn, tag in ((1, "L"), (-1, "R")):
    pod = bx(0, sgn * 365, 0, 80, 75, 70, f=10, sel="|Y")
    add(f"Camera pod {tag}", pod, "#1f6fb2")
    add(f"Camera lens window {tag}", cq.Workplane("YZ", origin=(40, sgn * 365, 6)).circle(13).circle(9).extrude(7), "#111111")
    add(f"Camera glass {tag}", cq.Workplane("YZ", origin=(40, sgn * 365, 6)).circle(9).extrude(8), "#63b3ed")
    sock_y = sgn * 365
    add(f"Pod socket {tag} ({'arming plug' if sgn > 0 else 'charge port'})", bx(-41, sock_y, -18, 4, 16, 9, f=1), "#f2c94c")
    add(f"Pod guard {tag}", cy_y(40, sgn * 398 - (3 if sgn > 0 else 0), sgn * 398 + (0 if sgn > 0 else 3), rin=36).intersect(bx(0, sgn * 398, 0, 120, 10, 60)) , "#2d3748")

# ---------- pendulum frame ----------
for sgn, tag in ((1, "L"), (-1, "R")):
    y = sgn * 130
    plate = bx(0, y, -82, 180, 4, 205, f=12, sel="|Y")
    for hx in (-50, 50):
        plate = plate.cut(cy_y(19, y - 3, y + 3, x=hx, z=-95))
    plate = plate.cut(cy_y(12.6, y - 3, y + 3))
    add(f"Side plate {tag}, 4 mm Al", plate, AL2)
    add(f"Shaft clamp {tag} (axle bearing housing)", cy_y(24, y - 12, y + 12, rin=12.6), "#6b7480")
for zc, nm in ((-60, "Deck A (compute)"), (-125, "Deck B (power)")):
    d = bx(0, 0, zc, 160, 252, 3, f=6)
    for hx in (-60, 60):
        for hy in (-100, 100):
            d = d.union(cy_z(2.5, zc - 1.5, zc + 6, x=hx, y=hy))   # standoffs
    add(nm, d, "#5d6770")

# ---------- compute deck A ----------
# Raspberry Pi 5: PCB 85 (y) x 56 (x), centre (-10, -45), PCB top at z = -51.9
px, pyc, pz = -10, -45, -53.5
pi = bx(px, pyc, pz + 0.8, 56, 85, 1.6, f=3)
for hx in (-24.5, 24.5):
    for hy in (-29, 29):
        pi = pi.cut(cy_z(1.35, pz - 1, pz + 3, x=px + hx, y=pyc + hy))
add("Raspberry Pi 5 PCB", pi, PCBG)
pz1 = pz + 1.6
add("Pi 5 active cooler", union(bx(px + 4, pyc + 6, pz1 + 4.5, 40, 44, 9, f=2),
                                 cy_z(14, pz1 + 9, pz1 + 13, x=px + 4, y=pyc + 6)), "#9aa3ad")
add("Pi 5 USB-A x2 + Ethernet", union(bx(px + 18, pyc - 39.5, pz1 + 8, 13.5, 17, 16),
                                       bx(px + 0, pyc - 39.5, pz1 + 8, 13.5, 17, 16),
                                       bx(px - 18, pyc - 39.5, pz1 + 7, 16, 21, 13.5)), "#c8ccd0")
add("Pi 5 GPIO header", bx(px - 24, pyc + 5, pz1 + 4.3, 5, 51, 8.5), BLK)
add("Pi 5 USB-C, micro-HDMI", union(bx(px + 26, pyc + 30, pz1 + 1.6, 7.5, 9, 3.2),
                                    bx(px + 26, pyc + 16, pz1 + 1.8, 7.5, 7, 3.5),
                                    bx(px + 26, pyc + 2, pz1 + 1.8, 7.5, 7, 3.5)), "#c8ccd0")
add("Pi 5 camera connectors (CSI x2)", union(bx(px + 8, pyc + 34, pz1 + 1.2, 18, 3, 2.4),
                                             bx(px - 8, pyc + 34, pz1 + 1.2, 18, 3, 2.4)), "#e2e8f0")
# ESP32-S3 DevKitC-1: 63 (y) x 25.4 (x), centre (45, 75)
ex, ey, ez = 45, 75, -58.5 + 6
add("ESP32-S3 DevKitC-1 PCB", bx(ex, ey, ez + 0.8, 25.4, 63, 1.6, f=1), BLK)
add("ESP32-S3 WROOM-1 module", union(bx(ex, ey + 14, ez + 2.4, 18, 25.5, 1.4), bx(ex, ey + 11, ez + 3.6, 15.8, 17.6, 2.4)), "#c0c6cc")
add("ESP32-S3 pin headers", union(bx(ex - 11.4, ey, ez - 4, 2.5, 56, 8.5), bx(ex + 11.4, ey, ez - 4, 2.5, 56, 8.5)), "#111111")
add("ESP32-S3 USB-C ports", union(bx(ex - 5, ey - 30.5, ez + 3, 9, 7.5, 3.2), bx(ex + 5, ey - 30.5, ez + 3, 9, 7.5, 3.2)), "#c8ccd0")
add("BNO085 IMU breakout", union(bx(45, 20, -56.9, 17.8, 25.4, 1.6, f=1), bx(45, 20, -55.6, 5.2, 3.8, 1.1)), "#3b2f7a")
# levelling servo (standard size, output parallel to axle) + gears
add("Levelling servo (metal gear)", union(bx(10, 109, -34, 40, 38, 20, f=2, sel="|Y"), bx(10, 113, -34, 54, 2.5, 20)), "#2b2b2b")
add("Levelling gear on shaft", toothed_y(22, 20.5, 40, 80, 8, bore=12.6), "#805ad5")
add("Levelling servo gear", toothed_y(12, 10.5, 20, 82, 7, z=-34), "#805ad5")

# ---------- power deck B (top surface z = -123.5) ----------
zb = -123.5
md = bx(0, 55, zb + 0.8 + 3, 62, 84, 1.6, f=2)
add("Dual 20 A motor driver PCB", md, "#8b1e1e")
add("Driver MOSFETs + capacitors", union(*[bx(-20 + 13 * k, 40, zb + 6.6, 6.5, 10, 2.3) for k in range(4)],
                                          *[bx(-20 + 13 * k, 70, zb + 6.6, 6.5, 10, 2.3) for k in range(4)],
                                          cy_z(5, zb + 5.4, zb + 21, x=22, y=55), cy_z(5, zb + 5.4, zb + 21, x=22, y=68)), "#222222")
add("Driver terminal blocks", union(bx(0, 14, zb + 10, 40, 8, 10), bx(0, 96, zb + 10, 30, 8, 10)), "#2f855a")
for k, (cx, nm) in enumerate(((50, "Buck 24-5 V 5.5 A (logic)"), (-50, "Buck 24-6 V 3 A (servo)"))):
    add(nm, union(bx(cx, -70, zb + 0.8 + 3, 21, 43, 1.6), cy_z(7, zb + 5.4, zb + 12.5, x=cx, y=-62),
                  cy_z(4, zb + 5.4, zb + 14, x=cx - 5, y=-82), cy_z(4, zb + 5.4, zb + 14, x=cx + 5, y=-82)), "#1e40af")
add("Relays K1 main + K2 kill (24 V, 40 A)", union(bx(0, -55, zb + 12.5, 28, 28, 25, f=2), bx(0, -25, zb + 12.5, 28, 28, 25, f=2)), "#1a1a1a")
add("2.4 GHz kill receiver", union(bx(-50, 55, zb + 7.25, 33, 40, 14.5, f=2),
                                   cy_x(0.6, -50, -50 + 0.1, y=55),
                                   cq.Workplane("XY", origin=(-62, 40, zb + 14)).circle(0.7).extrude(40).rotate((-62, 40, zb + 14), (-62, 41, zb + 14), 35),
                                   cq.Workplane("XY", origin=(-38, 40, zb + 14)).circle(0.7).extrude(40).rotate((-38, 40, zb + 14), (-38, 41, zb + 14), -35)), "#111111")
add("Fuse holder 25 A", bx(-50, 10, zb + 7.5, 18, 30, 15, f=2), "#c53030")
add("XT60 connectors", union(bx(-30, 18, zb + 6, 8, 16, 12), bx(-30, -2, zb + 6, 8, 16, 12)), "#f2c94c")
add("TMC2209 stepper driver", union(bx(-50, -30, zb + 6, 15, 20, 1.6), bx(-50, -30, zb + 9, 9, 9, 5)), "#6b46c1")

# ---------- drive train (both sides) ----------
for sgn, tag in ((1, "L"), (-1, "R")):
    s = sgn
    def Y(a, b):  # y-span inward..outward for this side
        return (a, b) if s > 0 else (-b, -a)
    a, b = Y(215, 265); add(f"Drive motor {tag} planetary gearbox", union(cy_y(21, a, b, z=-100), cy_y(23, *(Y(259, 265)), z=-100)), "#b7791f")
    a, b = Y(160, 215); add(f"Drive motor {tag} motor can (775)", cy_y(21, a, b, z=-100), "#d69e2e")
    a, b = Y(145, 160); add(f"Drive motor {tag} encoder cap", union(cy_y(18, a, b, z=-100), bx(0, s * 150, -118, 10, 8, 6)), "#2d3748")
    a, b = Y(265, 287); add(f"Motor shaft {tag}", cy_y(4, a, b, z=-100), "#a0aec0")
    py = 272 if s > 0 else -287
    pul = toothed_y(13.76, 11.7, 18, py, 15, z=-100, bore=4)
    pul = pul.union(cy_y(16, py - 1.2, py, z=-100, rin=4)).union(cy_y(16, py + 15, py + 16.2, z=-100, rin=4))
    add(f"Motor pulley 18T {tag}", pul, "#e2e8f0")
    # belt (outer tangents) 15 wide
    def belt_profile(r1, r2):
        d = 100.0; be = math.asin((r1 - r2) / d)
        p1r = (r1 * math.cos(be), r1 * math.sin(be)); p2r = (r2 * math.cos(be), -d + r2 * math.sin(be))
        return (cq.Workplane("XZ", origin=(0, py + 15, 0)).moveTo(*p2r).lineTo(*p1r)
                .threePointArc((0, r1), (-p1r[0], p1r[1])).lineTo(-p2r[0], p2r[1]).threePointArc((0, -d - r2), p2r).close())
    add(f"HTD-5M belt {tag}", belt_profile(45.0, 16.3).extrude(15).cut(belt_profile(43.0, 14.3).extrude(15)), "#1a202c")
    # motor face plate + two standoffs back to the side plate
    fp_a, fp_b = Y(265, 269)
    face = bx(0, (fp_a + fp_b) / 2, -96, 56, 4, 64, f=4, sel="|Y").cut(cy_y(5, fp_a - 1, fp_b + 1, z=-100))
    sa, sb = Y(132, 265)
    add(f"Motor bracket {tag} (face plate + standoffs)", union(face, cy_y(4, sa, sb, x=-24, z=-70), cy_y(4, sa, sb, x=24, z=-70)), AL)

# ---------- steering drive ----------
add("Steering stepper NEMA 17 body", union(bx(0, -154, -170, 42.3, 34, 42.3, f=4, sel="|Y"),
                                           bx(0, -172.5, -170, 42.3, 3, 42.3, f=4, sel="|Y")), "#3d4651")
add("NEMA 17 end caps", union(bx(0, -136, -170, 42.3, 4, 42.3, f=4, sel="|Y"), cy_y(11, -134, -132, z=-170)), "#8a96a3")
add("NEMA 17 connector", bx(0, -165, -192, 16, 8, 5), "#f7f7f7")
add("NEMA 17 shaft + coupler", union(cy_y(2.5, -134, -110, z=-170), cy_y(9.5, -128, -103, z=-170)), "#cbd5e0")
for x in (-40, 40):
    add(f"Rail 8 mm x{x:+d}", cy_y(4, -128, 128, x=x, z=-170), "#cbd5e0")
add("T8 lead screw", cy_y(4, -103, 128, z=-170), "#b7791f")
add("Lead screw bearing (KFL08)", bx(0, 124, -170, 30, 6, 30, f=4, sel="|Y"), "#9aa5b1")

# ---------- steering sled ----------
car = bx(0, 0, -181, 130, 60, 6, f=4)
add("Sled carriage plate", car, "#718096", "sled")
add("LM8UU bearings x4", union(*[cy_y(7.5, yy - 12, yy + 12, x=xx, z=-170) for xx in (-40, 40) for yy in (-18, 18)]), "#e2e8f0", "sled")
add("T8 brass nut", union(cy_y(5.1, -8, 7, z=-170), cy_y(11, -8, -4.5, z=-170)), "#d4a017", "sled")
add("Battery tray straps", union(bx(-58.5, 0, -207, 2, 50, 46), bx(58.5, 0, -207, 2, 50, 46)), "#718096", "sled")
cells = []
for i in range(6):
    for j in range(2):
        cells.append(cy_y(9.25, -32.5, 32.5, x=-46.25 + 18.5 * i, z=-201.5 - 18.5 * j))
add("Battery 6S2P cells (18650)", union(*cells), "#3b5bdb", "sled")
add("Battery cell holders", union(bx(0, -40, -211, 115, 6, 42), bx(0, 40, -211, 115, 6, 42)), "#1f2328", "sled")
add("Battery nickel strips", union(*[bx(-46.25 + 37 * k + 9.25, -43.4, -211, 30, 0.6, 38) for k in range(3)]), "#c0c0c0", "sled")
add("6S BMS board", bx(0, 46, -211, 60, 1.6, 35), PCBG, "sled")
bal = bx(0, 0, -251, 130, 130, 30, f=3)
add("Steel ballast 130 x 130 x 30", bal, STEEL, "sled")
add("Ballast bolts M8 x4", union(*[cy_z(6.5, -236, -230.5, x=xx, y=yy) for xx in (-58, 58) for yy in (-58, 58)]), "#9aa5b1", "sled")

# ---------- markers ----------
m, cg = props()
add("CoG marker", cq.Workplane("XY").sphere(11).translate(tuple(v * 1000 for v in cg)), "#e53e3e", "marker")
add("Centre marker", cq.Workplane("XY").sphere(6), "#2d3748", "marker")

# ---------- export ----------
assy = cq.Assembly(name="RoToRBot")
manifest = []
for i, (name, shp, col, grp, op) in enumerate(parts):
    fn = f"p{i:03d}.stl"
    fine = name.startswith(("Shell", "Traction", "Equator"))
    cq.exporters.export(shp, f"build/stl/{fn}", tolerance=0.2 if fine else 0.25, angularTolerance=0.04 if fine else 0.12)
    manifest.append(dict(name=name, file=fn, color=col, group=grp, opacity=op))
    if grp != "marker":
        rgb = tuple(int(col[k:k + 2], 16) / 255 for k in (1, 3, 5))
        safe = "".join(ch if ch.isalnum() or ch in "_-." else "_" for ch in name)
        assy.add(shp, name=safe, color=cq.Color(*rgb, op if op > 0.5 else 0.35))
json.dump(manifest, open("build/parts.json", "w"), indent=0)
assy.save("build/RoToRBot_assembly.step")
print(len(parts), "parts;", sum(1 for p in parts if p[3] != "marker"), "in STEP; CoG mm", [round(v * 1000, 1) for v in cg], "mass", round(m, 2))
