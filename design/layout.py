"""RoToRBot layout: one source of truth for geometry, masses, centre of gravity and sizing.
Run: python layout.py   (standard library only; prints every number used in the Round 1 submission)

Frame: origin = sphere centre, x = forward (direction of roll), y = left (along the fixed shaft), z = up.
Groups: 'shell' rotates about the shaft; 'fixed' is fixed to the shaft and pendulum (swings in pitch);
'sled' is part of the pendulum but slides along y (steering mass).
Boxes: centre (x, y, z) and size (dx, dy, dz) in metres; used for clearance checks and the CAD model.
"""
import math, json

G = 9.81
OD = 0.640                 # shell outer diameter over PC, m
T_SHELL = 0.002            # average PC wall after thermoforming, m
R = OD / 2                 # rolling radius (band adds 2 mm; ignored)
R_IN = R - T_SHELL         # inner radius
BAND_T = 0.002             # traction band thickness
SLED_TRAVEL = 0.070        # +/- along y
BELT_RATIO = 54 / 18       # HTD-5M 18T motor pulley -> 54T hub pulley
ETA_BELT = 0.95

PC_RHO = 1200.0
shell_area = 4 * math.pi * (R - T_SHELL / 2) ** 2
m_hemis = PC_RHO * shell_area * T_SHELL

# name, group, mass kg, centre (x,y,z), size (dx,dy,dz), colour, note
C = [
    ("PC hemispheres x2 (640 OD, 2 mm)", "shell", m_hemis, (0, 0, 0), None, "#cfd8e3", "thermoformed polycarbonate"),
    ("Equator flange ring + M4 bolts", "shell", 0.30, (0, 0, 0), None, "#9aa5b1", "internal, flush outside"),
    ("Traction band 60 x 2 mm rubber", "shell", 0.27, (0, 0, 0), None, "#222222", "over the seam"),
    ("Pole hubs x2 (6805 bearing + 54T pulley)", "shell", 0.60, (0, 0, 0), None, "#b0b7bf", "bolted to the poles"),

    ("Fixed shaft 25 x 2.5 Al tube", "fixed", 0.35, (0, 0, 0), (0.025, 0.74, 0.025), "#8c96a0", "hollow: camera cables run inside"),
    ("Camera pod L (camera, window, sockets)", "fixed", 0.12, (0, 0.365, 0), (0.080, 0.075, 0.070), "#1f6fb2", "outside the shell"),
    ("Camera pod R (camera, window, sockets)", "fixed", 0.12, (0, -0.365, 0), (0.080, 0.075, 0.070), "#1f6fb2", "outside the shell"),
    ("Shaft levelling servo + gear (inside)", "fixed", 0.12, (0, 0.105, -0.035), (0.040, 0.020, 0.040), "#805ad5", "keeps pods level"),
    ("Side plate L, 4 mm Al", "fixed", 0.28, (0, 0.130, -0.082), (0.180, 0.004, 0.205), "#7d8790", "hangs from shaft clamp"),
    ("Side plate R, 4 mm Al", "fixed", 0.28, (0, -0.130, -0.082), (0.180, 0.004, 0.205), "#7d8790", "hangs from shaft clamp"),
    ("Deck A (compute)", "fixed", 0.20, (0, 0, -0.060), (0.160, 0.252, 0.003), "#5d6770", ""),
    ("Deck B (power)", "fixed", 0.20, (0, 0, -0.125), (0.160, 0.252, 0.003), "#5d6770", ""),
    ("Raspberry Pi 5 + active cooler", "fixed", 0.075, (-0.010, -0.045, -0.045), (0.056, 0.085, 0.027), "#2e8b57", "vision"),
    ("ESP32-S3 controller", "fixed", 0.015, (0.045, 0.075, -0.052), (0.028, 0.069, 0.013), "#2b6cb0", "real-time control"),
    ("BNO085 IMU", "fixed", 0.005, (0.045, 0.020, -0.056), (0.025, 0.025, 0.005), "#c05621", "near the shaft"),
    ("Dual 20 A motor driver", "fixed", 0.11, (0, 0.055, -0.110), (0.062, 0.084, 0.026), "#b7791f", ""),
    ("Buck 24->5 V 5.5 A (logic)", "fixed", 0.03, (0.050, -0.070, -0.115), (0.025, 0.045, 0.015), "#6b46c1", ""),
    ("Buck 24->6 V 3 A (servos)", "fixed", 0.03, (-0.050, -0.070, -0.115), (0.025, 0.045, 0.015), "#6b46c1", ""),
    ("Relays K1 main + K2 kill", "fixed", 0.08, (0.000, -0.040, -0.108), (0.030, 0.060, 0.030), "#c53030", "24 V coil, 40 A"),
    ("2.4 GHz kill receiver", "fixed", 0.015, (-0.050, 0.055, -0.115), (0.040, 0.030, 0.012), "#c53030", "independent of Pi/ESP32"),
    ("Fuse 25 A + connectors", "fixed", 0.03, (-0.050, 0.010, -0.115), (0.020, 0.030, 0.015), "#c53030", ""),
    ("Wiring harness", "fixed", 0.30, (0, 0, -0.100), None, "#444444", ""),
    ("Fasteners and misc (contingency)", "fixed", 0.30, (0, 0, -0.100), None, "#444444", ""),
    ("Drive motor L (45 mm planetary, encoder)", "fixed", 0.70, (0, 0.205, -0.100), (0.045, 0.120, 0.045), "#d69e2e", ""),
    ("Drive motor R (45 mm planetary, encoder)", "fixed", 0.70, (0, -0.205, -0.100), (0.045, 0.120, 0.045), "#d69e2e", ""),
    ("Motor bracket, 18T pulley, belt L", "fixed", 0.10, (0, 0.260, -0.050), (0.040, 0.020, 0.140), "#a0aec0", ""),
    ("Motor bracket, 18T pulley, belt R", "fixed", 0.10, (0, -0.260, -0.050), (0.040, 0.020, 0.140), "#a0aec0", ""),
    ("Steering stepper NEMA 17", "fixed", 0.28, (0, -0.155, -0.170), (0.042, 0.040, 0.042), "#4a5568", "drives T8 lead screw"),
    ("Rails 2 x 8 mm + T8 lead screw", "fixed", 0.30, (0, 0, -0.170), (0.110, 0.256, 0.010), "#a0aec0", ""),
    ("Sled carriage (4 x LM8UU + nut)", "sled", 0.18, (0, 0, -0.185), (0.130, 0.060, 0.016), "#718096", ""),
    ("Battery 6S2P 18650 (21.6 V, 6 Ah)", "sled", 0.75, (0, 0, -0.213), (0.115, 0.100, 0.042), "#2f855a", "steering mass"),
    ("Steel ballast 130 x 130 x 30", "sled", round(7850*0.13*0.13*0.030, 2), (0, 0, -0.251), (0.130, 0.130, 0.030), "#4a4a4a", "steering mass, tunable"),
]

def props(sled=0.0):
    m = sum(c[2] for c in C)
    mx = sum(c[2] * c[3][0] for c in C)
    my = sum(c[2] * (c[3][1] + (sled if c[1] == "sled" else 0)) for c in C)
    mz = sum(c[2] * c[3][2] for c in C)
    return m, (mx / m, my / m, mz / m)

def clearance(sled):
    worst = (9, None)
    for name, grp, m, c, s, *_ in C:
        if s is None or "pod" in name or "shaft" in name:
            continue
        y0 = c[1] + (sled if grp == "sled" else 0)
        for sx in (-1, 1):
            for sy in (-1, 1):
                for sz in (-1, 1):
                    p = (c[0] + sx * s[0] / 2, y0 + sy * s[1] / 2, c[2] + sz * s[2] / 2)
                    gap = R_IN - math.sqrt(sum(v * v for v in p))
                    if gap < worst[0]:
                        worst = (gap, name)
    return worst

m, cg = props()
m_shell = sum(c[2] for c in C if c[1] == "shell")
m_pend = m - m_shell
mpl = -sum(c[2] * c[3][2] for c in C if c[1] != "shell")      # sum m*l of pendulum-fixed parts, kg*m
m_sled = sum(c[2] for c in C if c[1] == "sled")
h = -cg[2]

# inertia about the shaft (y) axis through O, point-mass + shell
I_shell = 2 / 3 * m_shell * R ** 2
I_pend = sum(c[2] * (c[3][0] ** 2 + c[3][2] ** 2) for c in C if c[1] != "shell")
I_O = I_shell + I_pend
I_cm = I_O - m * h ** 2
I_P = I_cm + m * (R - h) ** 2
rock_T = 2 * math.pi / math.sqrt(m * G * h / I_P)

def phi_for(theta_deg, crr=0.0):
    t = math.radians(theta_deg)
    need = m * R * (math.sin(t) + crr * math.cos(t))
    s = need / mpl
    return math.degrees(math.asin(s)) if s <= 1 else float("nan")

def theta_max(phi_deg):
    return math.degrees(math.asin(mpl * math.sin(math.radians(phi_deg)) / (m * R)))

CRR = 0.015
v_cruise = 1.5
shell_rpm = v_cruise / R * 60 / (2 * math.pi)
motor_rpm = shell_rpm * BELT_RATIO
def shell_torque(theta_deg):
    t = math.radians(theta_deg)
    return m * G * R * (math.sin(t) + CRR * math.cos(t))
T15 = shell_torque(15)
T_design = 1.3 * shell_torque(phi_lim := 17) if False else None
# design peak: 17 deg (60 deg swing limit) plus 30 % for acceleration and losses
T_peak_shell = 1.3 * shell_torque(17)
T_motor = T_peak_shell / (2 * BELT_RATIO * ETA_BELT)
P_climb = shell_torque(15) * v_cruise / R / ETA_BELT
m_eff = m + I_shell / R ** 2 + I_pend / R ** 2 * 0  # pendulum does not spin when rolling steadily
KE = 0.5 * m_eff * v_cruise ** 2
h_momentum = KE / (m * G)

delta = m_sled * SLED_TRAVEL / m
alpha = math.degrees(math.atan(delta / h))
r_turn = R / math.tan(math.radians(alpha))

pod_out = max(c[3][1] + c[4][1] / 2 for c in C if "pod" in c[0])
protrusion = pod_out - R
width = 2 * pod_out

out = dict(
    OD_mm=OD * 1000, OD_ft=OD / 0.3048, OD_band_mm=(OD + 2 * BAND_T) * 1000, OD_band_ft=(OD + 2 * BAND_T) / 0.3048,
    pod_protrusion_mm=protrusion * 1000, pod_protrusion_ft=protrusion / 0.3048, width_mm=width * 1000,
    m_total=m, m_shell=m_shell, m_pend=m_pend, m_sled=m_sled, m_hemis=m_hemis,
    cg_mm=[v * 1000 for v in cg], mpl=mpl, l_p_mm=mpl / (m_pend) * 1000,
    I_O=I_O, I_P=I_P, rock_T=rock_T,
    phi10=phi_for(10, CRR), phi15=phi_for(15, CRR), phi17=phi_for(17, CRR),
    thmax60=theta_max(60), thmax90=theta_max(90),
    T15=T15, T_peak_shell=T_peak_shell, T_motor=T_motor, P_climb=P_climb,
    shell_rpm=shell_rpm, motor_rpm=motor_rpm, KE=KE, h_momentum_mm=h_momentum * 1000, m_eff=m_eff,
    mu_needed_15=math.tan(math.radians(15)),
    delta_mm=delta * 1000, alpha=alpha, r_turn=r_turn,
    clear_centre=clearance(0), clear_left=clearance(SLED_TRAVEL), clear_right=clearance(-SLED_TRAVEL),
    sled_trim_mm=-cg[1]*m/m_sled*1000,
    cg_sled_left_mm=[v * 1000 for v in props(SLED_TRAVEL)[1]],
)
if __name__ == "__main__":
    for k, v in out.items():
        print(f"{k:22s} {v}")
    print()
    for c in C:
        print(f"{c[0]:44s} {c[1]:6s} {c[2]:6.3f} kg  z={c[3][2]*1000:7.1f} mm")
    json.dump(out, open("numbers.json", "w"), indent=1, default=str)
