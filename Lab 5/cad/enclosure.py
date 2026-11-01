"""
Bedside enclosure for the Quiet Coyote Sleep Tracker (parametric, in millimetres).

The Raspberry Pi 5 stands upright behind the front face, components forward, so the
Mini PiTFT on the GPIO header looks out through a window. The USB and Ethernet ports
face a cut-out in the right wall (webcam, USB mic, USB speaker), and the power cable
leaves through a notch in the back plate. Two rolling hills are recessed into the front,
like the hills on the screen. The webcam clips onto the flat top.

    python enclosure.py            # writes shell.stl, back_plate.stl, preview.png, drawing.png

Two printed parts: the shell (print front face down) and the back plate (print flat).
The Pi screws onto the back plate's standoffs (M2.5); the plate screws into the shell (M3).

Pi 5 sizes and hole positions are from the Raspberry Pi mechanical drawing. The position
of the Mini PiTFT's screen (SCREEN_*) is an estimate: measure it before printing.
"""
import math
import os

import numpy as np
import trimesh
from manifold3d import CrossSection, Manifold

HERE = os.path.dirname(os.path.abspath(__file__))

# --- parameters -------------------------------------------------------------------------
WALL = 2.5                     # shell wall
W, D, H = 96.0, 32.0, 84.0     # outer width (x), depth (y, front at y=0), height (z)
PLATE = 2.5                    # back plate thickness (sits inside the back opening)
FIT = 0.3                      # clearance around the back plate

PI_W, PI_H, PCB = 85.0, 56.0, 1.6          # Pi 5 board, standing with the GPIO edge on top
PI_X, PI_Z = WALL + 1.0, WALL + 16.0       # board's lower-left corner: 16 mm below for the USB-C plug and its bend
PI_Y = WALL + 0.5 + 13.0                   # board's front face: front wall + gap + PiTFT stack height
HOLES = [(3.5, 3.5), (61.5, 3.5), (3.5, 52.5), (61.5, 52.5)]   # from the board's top-left (GPIO) corner

SCREEN_CX, SCREEN_CZ = 32.5, 12.0          # screen centre from the board's left edge / top edge (estimate)
SCREEN_W, SCREEN_H = 30.0, 18.0            # window; the 1.14" panel's active area is about 25 x 15

HILL_DEPTH = 0.8                           # recess of the hills on the front face
NOTCH_X = WALL + 10.0                      # power-cable notch starts after the corner screw boss


def box(x, y, z, sx, sy, sz):
    return Manifold.cube([sx, sy, sz]).translate([x, y, z])


def cyl_y(x, y, z, r, h):
    """Cylinder along +y starting at (x, y, z)."""
    return Manifold.cylinder(h, r, r, 48).rotate([-90, 0, 0]).translate([x, y, z])


def pi_hole(i):
    hx, hz = HOLES[i]
    return PI_X + hx, PI_Z + PI_H - hz


def shell():
    s = box(0, 0, 0, W, D, H) - box(WALL, WALL, WALL, W - 2 * WALL, D, H - 2 * WALL)   # open at the back
    # screen window
    cx, cz = PI_X + SCREEN_CX, PI_Z + PI_H - SCREEN_CZ
    s -= box(cx - SCREEN_W / 2, -1, cz - SCREEN_H / 2, SCREEN_W, WALL + 2, SCREEN_H)
    # right wall: USB-A and Ethernet face this side
    s -= box(W - WALL - 1, WALL, PI_Z + 2, WALL + 2, PI_Y - WALL + 2, PI_H - 4)
    # left wall vents
    for i in range(6):
        s -= box(-1, 8 + i * 3.5, 15, WALL + 2, 1.8, H - 30)
    # top vents near the back, away from where the webcam clip sits at the front
    for i in range(8):
        s -= box(15 + i * 9, D - 12, H - WALL - 1, 4, 8, WALL + 2)
    # corner bosses for the back plate screws (M3, 2.5 mm pilot holes)
    for bx, bz in [(WALL, WALL), (W - WALL - 7, WALL), (WALL, H - WALL - 7), (W - WALL - 7, H - WALL - 7)]:
        boss = box(bx, D - PLATE - FIT - 10, bz, 7, 10, 7)
        s += boss - cyl_y(bx + 3.5, D - PLATE - FIT - 11, bz + 3.5, 1.25, 12)
    # two hills recessed into the front, echoing the screen
    for amp, base, phase, k in [(4.0, 16.0, 1.0, 38.0), (3.0, 10.0, 3.0, 55.0)]:
        pts = [(x, base + amp * math.sin(x / k + phase)) for x in np.linspace(4, W - 4, 60)]
        pts = (pts + [(W - 4, 4.0), (4, 4.0)])[::-1]      # counter-clockwise, or the area counts as empty
        hill = CrossSection([pts]).extrude(HILL_DEPTH + 1).rotate([90, 0, 0]).translate([0, HILL_DEPTH, 0])
        s -= hill
    return s


def back_plate():
    y0 = D - PLATE
    p = box(WALL + FIT, y0, WALL + FIT, W - 2 * (WALL + FIT), PLATE, H - 2 * (WALL + FIT))
    # standoffs for the Pi, reaching forward to the back of the board
    length = y0 - (PI_Y + PCB)
    for i in range(4):
        x, z = pi_hole(i)
        p += cyl_y(x, PI_Y + PCB, z, 3.0, length + 0.01) - cyl_y(x, PI_Y + PCB - 1, z, 1.1, length + 2)
    # screw holes into the shell bosses
    for bx, bz in [(WALL, WALL), (W - WALL - 7, WALL), (WALL, H - WALL - 7), (W - WALL - 7, H - WALL - 7)]:
        p -= cyl_y(bx + 3.5, y0 - 1, bz + 3.5, 1.7, PLATE + 2)
    # notch for the USB-C power cable, which plugs into the bottom edge of the Pi
    p -= box(NOTCH_X, y0 - 1, WALL - 1, 40, PLATE + 2, PI_Z - WALL - 3)     # clear of the corner screw and the standoffs
    return p


def ghosts():
    """Stand-ins (not printed) for the preview: Pi, Mini PiTFT, webcam."""
    pi = box(PI_X, PI_Y, PI_Z, PI_W, PCB, PI_H)
    cx, cz = PI_X + SCREEN_CX, PI_Z + PI_H - SCREEN_CZ
    tft = box(cx - 25, WALL + 0.5, cz - 11, 50, 13, 22)
    cam = box(W / 2 - 25, 2, H, 50, 26, 30)
    return {"Pi 5": pi, "Mini PiTFT": tft, "webcam (clips on top)": cam}


def to_trimesh(m):
    mesh = m.to_mesh()
    return trimesh.Trimesh(vertices=np.asarray(mesh.vert_properties)[:, :3], faces=np.asarray(mesh.tri_verts))


def rasterize(parts, elev, azim, size=(900, 700)):
    """Tiny depth-buffered renderer (orthographic, Lambert shading). parts: [(trimesh, rgb)]."""
    e, a = math.radians(elev), math.radians(azim)
    # camera looks along -view; screen axes right/up
    view = np.array([math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)])
    right = np.cross([0, 0, 1], view); right /= np.linalg.norm(right)
    up = np.cross(view, right)
    allv = np.vstack([tm.vertices for tm, _ in parts])
    sx, sy = allv @ right, allv @ up
    w, h = size
    scale = 0.9 * min(w / (sx.max() - sx.min()), h / (sy.max() - sy.min()))
    ox, oy = (sx.max() + sx.min()) / 2, (sy.max() + sy.min()) / 2
    img = np.ones((h, w, 3))
    depth = np.full((h, w), -np.inf)
    light = view * 0.6 + np.array([0.3, -0.5, 0.6]); light /= np.linalg.norm(light)
    for tm, rgb in parts:
        v = tm.vertices
        px = (v @ right - ox) * scale + w / 2
        py = h / 2 - (v @ up - oy) * scale
        pz = v @ view
        normals = tm.face_normals
        for f, n in zip(tm.faces, normals):
            if n @ view <= 0:                       # back face
                continue
            x, y, z = px[f], py[f], pz[f]
            x0, x1 = max(int(x.min()), 0), min(int(x.max()) + 1, w)
            y0, y1 = max(int(y.min()), 0), min(int(y.max()) + 1, h)
            if x0 >= x1 or y0 >= y1:
                continue
            gx, gy = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
            d = (y[1] - y[2]) * (x[0] - x[2]) + (x[2] - x[1]) * (y[0] - y[2])
            if abs(d) < 1e-9:
                continue
            l0 = ((y[1] - y[2]) * (gx - x[2]) + (x[2] - x[1]) * (gy - y[2])) / d
            l1 = ((y[2] - y[0]) * (gx - x[2]) + (x[0] - x[2]) * (gy - y[2])) / d
            l2 = 1 - l0 - l1
            inside = (l0 >= -1e-6) & (l1 >= -1e-6) & (l2 >= -1e-6)
            zz = l0 * z[0] + l1 * z[1] + l2 * z[2]
            region = depth[y0:y1, x0:x1]
            hit = inside & (zz > region)
            region[hit] = zz[hit]
            k = 0.35 + 0.65 * max(0.0, float(n @ light))
            img[y0:y1, x0:x1][hit] = np.array(rgb) * k
    return img


def render(parts, path, views, title):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, len(views), figsize=(6.5 * len(views), 5.5))
    for ax, (elev, azim, label) in zip(np.atleast_1d(axs), views):
        ax.imshow(rasterize(parts, elev, azim))
        ax.set_title(label)
        ax.axis("off")
    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def drawing(path):
    """Front, right and top views with the main dimensions."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle, Circle
    fig, axs = plt.subplots(1, 3, figsize=(16, 6))
    cx, cz = PI_X + SCREEN_CX, PI_Z + PI_H - SCREEN_CZ

    def dim(ax, x0, y0, x1, y1, text, off=(0, 0)):
        ax.annotate("", (x0, y0), (x1, y1), arrowprops=dict(arrowstyle="<->", lw=0.8))
        ax.text((x0 + x1) / 2 + off[0], (y0 + y1) / 2 + off[1], text, ha="center", va="center", fontsize=8,
                bbox=dict(fc="white", ec="none", pad=1))

    a = axs[0]; a.set_title("Front (x-z)")
    a.add_patch(Rectangle((0, 0), W, H, fill=False, lw=1.5))
    a.add_patch(Rectangle((cx - SCREEN_W / 2, cz - SCREEN_H / 2), SCREEN_W, SCREEN_H, fill=False, lw=1))
    xs = np.linspace(4, W - 4, 60)
    for amp, base, phase, k in [(4.0, 16.0, 1.0, 38.0), (3.0, 10.0, 3.0, 55.0)]:
        a.plot(xs, base + amp * np.sin(xs / k + phase), lw=0.8, color="gray")
    dim(a, 0, -6, W, -6, f"{W:.0f}"); dim(a, -6, 0, -6, H, f"{H:.0f}")
    dim(a, cx - SCREEN_W / 2, cz + SCREEN_H / 2 + 4, cx + SCREEN_W / 2, cz + SCREEN_H / 2 + 4, f"window {SCREEN_W:.0f} x {SCREEN_H:.0f}")
    a.text(cx, cz, f"centre\n({cx:.1f}, {cz:.1f})", ha="center", va="center", fontsize=7)
    a.text(W / 2, 6, "recessed hills, 0.8 deep", ha="center", fontsize=7, color="gray")

    a = axs[1]; a.set_title("Right side (y-z)")
    a.add_patch(Rectangle((0, 0), D, H, fill=False, lw=1.5))
    a.add_patch(Rectangle((WALL, PI_Z + 2), PI_Y - WALL + 2, PI_H - 4, fill=False, lw=1, ls="--"))
    a.text(WALL + (PI_Y - WALL) / 2, PI_Z + PI_H / 2, "USB / Ethernet\ncut-out", ha="center", fontsize=7, rotation=90)
    a.add_patch(Rectangle((PI_Y, PI_Z), PCB, PI_H, color="green", alpha=0.4))
    a.add_patch(Rectangle((D - PLATE, WALL), PLATE, H - 2 * WALL, color="tab:blue", alpha=0.3))
    dim(a, 0, -6, D, -6, f"{D:.0f}"); dim(a, -6, 0, -6, H, f"{H:.0f}")
    dim(a, 0, H + 6, PI_Y, H + 6, f"{PI_Y:.1f} to Pi board")
    a.text(D - PLATE / 2, H / 2, "back plate", rotation=90, ha="center", va="center", fontsize=7)

    a = axs[2]; a.set_title("Back plate (x-z, from behind the Pi)")
    a.add_patch(Rectangle((WALL + FIT, WALL + FIT), W - 2 * (WALL + FIT), H - 2 * (WALL + FIT), fill=False, lw=1.5))
    a.add_patch(Rectangle((PI_X, PI_Z), PI_W, PI_H, fill=False, lw=0.8, ls=":"))
    for i in range(4):
        x, z = pi_hole(i)
        a.add_patch(Circle((x, z), 3.0, fill=False)); a.add_patch(Circle((x, z), 1.1, fill=False))
    a.add_patch(Rectangle((NOTCH_X, WALL + FIT), 40, PI_Z - WALL - 4, fill=False, lw=1, ls="--"))
    a.text(NOTCH_X + 20, WALL + 4, "power-cable notch, 40 wide", ha="center", fontsize=7)
    x0, z0 = pi_hole(2); x1, z1 = pi_hole(3)
    dim(a, x0, z0 + 7, x1, z1 + 7, "58 (M2.5 standoffs)")
    x2, z2 = pi_hole(0)
    dim(a, x0 - 6, z0, x2 - 6, z2, "49")
    a.text(PI_X + PI_W / 2, PI_Z + PI_H - 4, "Pi 5 outline, GPIO edge up", ha="center", fontsize=7)

    for a in axs:
        a.set_aspect("equal"); a.axis("off"); a.margins(0.12)
    fig.suptitle("Quiet Coyote enclosure: main dimensions in mm (screen position is an estimate - measure first)")
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


if __name__ == "__main__":
    s, p = shell(), back_plate()
    to_trimesh(s).export(os.path.join(HERE, "shell.stl"))
    to_trimesh(p).export(os.path.join(HERE, "back_plate.stl"))
    shell_rgb, plate_rgb = (0.93, 0.90, 0.84), (0.55, 0.70, 0.90)
    colors = {"Pi 5": (0.2, 0.6, 0.3), "Mini PiTFT": (0.12, 0.12, 0.18), "webcam (clips on top)": (0.35, 0.35, 0.38)}
    ghost = [(to_trimesh(m), colors[k]) for k, m in ghosts().items()]
    render([(to_trimesh(s), shell_rgb), (to_trimesh(p), plate_rgb)] + ghost, os.path.join(HERE, "preview.png"),
           [(20, -110, "front: screen window, hills, webcam on top"), (25, 40, "back: plate with Pi standoffs")],
           "Quiet Coyote enclosure (Pi, Mini PiTFT and webcam shown as blocks)")
    render([(to_trimesh(s), shell_rgb)], os.path.join(HERE, "shell.png"),
           [(15, -100, "shell, front"), (25, 60, "shell, back (open)")], "Shell")
    render([(to_trimesh(p), plate_rgb)], os.path.join(HERE, "back_plate.png"),
           [(25, -70, "back plate, Pi side"), (25, 110, "back plate, outside")],
           "Back plate (the Pi screws onto the four standoffs)")
    drawing(os.path.join(HERE, "drawing.png"))
    for name, m in [("shell", s), ("back_plate", p)]:
        t = to_trimesh(m)
        print(f"{name}: watertight={t.is_watertight}, volume={t.volume / 1000:.1f} cm3, "
              f"bounds={np.round(t.bounds, 1).tolist()}")
