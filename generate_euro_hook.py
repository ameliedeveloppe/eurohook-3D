#!/usr/bin/env python3
"""Generate a 3D model (Wavefront .obj) of a euro hook / pegboard hook.

Classic "looped" euro hook made of a single steel wire (4 mm diameter):
  - two parallel horizontal display arms perpendicular to the panel,
    spaced 25.4 mm (1 inch pegboard grid),
  - a 180 deg loop/bridge behind the panel joining both prongs,
  - upturned (anti-slip) tips at the front of each arm.

Units: 1 OBJ unit = 1 mm. Panel face = plane x=0, arms point +X, +Z is up.
"""

import math

import numpy as np

# ----------------------------- parameters ---------------------------------
WIRE_DIA = 4.0                   # wire diameter (mm)
ARM_LEN = 200.0                  # arm length from panel face to tip-curl start (mm)
PRONG_SPACING = 25.4             # center-to-center prong spacing (mm)
BACK_LEN = 12.0                  # prong length behind the panel face (mm)
LOOP_R = PRONG_SPACING / 2.0     # 180 deg rear loop radius (mm)
TIP_R = 10.0                     # centerline radius of the upturned tip (mm)
TIP_ANGLE = math.radians(130.0)  # tip bend angle
RADIAL_SEGMENTS = 20             # resolution of the swept tube cross-section
STRAIGHT_STEP = 3.0              # sample step on straight sections (mm)
ARC_STEP_DEG = 5.0               # sample step on arcs (deg)

OUT_OBJ = "euro_hook_200mm.obj"

EX = np.array([1.0, 0.0, 0.0])
EY = np.array([0.0, 1.0, 0.0])
EZ = np.array([0.0, 0.0, 1.0])


def rot(v, axis, angle):
    axis = axis / np.linalg.norm(axis)
    return (
        v * math.cos(angle)
        + np.cross(axis, v) * math.sin(angle)
        + axis * np.dot(axis, v) * (1.0 - math.cos(angle))
    )


def arc_points(p0, d0, axis, radius, angle, sense):
    """Sample a circular arc: start p0, tangent d0, turning around `axis`.

    sense=+1: center on the +R*(axis x d0) side (left turn around axis).
    Returns sampled points (p0 excluded) and the end tangent direction.
    """
    n = max(2, int(round(math.degrees(angle) / ARC_STEP_DEG)))
    center = p0 + sense * radius * np.cross(axis, d0)
    pts = [center + rot(p0 - center, axis, sense * angle * i / n) for i in range(1, n + 1)]
    return np.array(pts), rot(d0, axis, sense * angle)


def line_points(p0, d0, length):
    d0 = d0 / np.linalg.norm(d0)
    n = max(1, int(round(length / STRAIGHT_STEP)))
    t = np.arange(1, n + 1) * (length / n)
    return p0 + np.outer(t, d0)


def build_centerline():
    """Continuous path from the free end of arm A to the free end of arm B."""
    sections = []

    # 1) tip curl of arm A, traversed backwards from the free tip
    tip_tangent = rot(EX, -EY, TIP_ANGLE)
    p_tip = np.array([ARM_LEN + TIP_R * math.sin(TIP_ANGLE), 0.0,
                      TIP_R * (1.0 - math.cos(TIP_ANGLE))])
    pts, d = arc_points(p_tip, -tip_tangent, -EY, TIP_R, TIP_ANGLE, -1)
    assert np.allclose(d, -EX, atol=1e-9), d
    sections.append(pts)

    # 2) arm A: from the curl start back behind the panel face
    p = sections[-1][-1]
    assert np.allclose(p, np.array([ARM_LEN, 0.0, 0.0]), atol=1e-9), p
    sections.append(line_points(p, -EX, ARM_LEN + BACK_LEN))

    # 3) rear 180 deg loop behind the panel (horizontal plane), -X -> +X
    p = sections[-1][-1]
    assert np.allclose(p, np.array([-BACK_LEN, 0.0, 0.0]), atol=1e-9), p
    pts, d = arc_points(p, -EX, -EZ, LOOP_R, math.pi, +1)
    assert np.allclose(d, EX, atol=1e-9), d
    sections.append(pts)

    # 4) arm B: forward through the panel
    p = sections[-1][-1]
    assert np.allclose(p, np.array([-BACK_LEN, PRONG_SPACING, 0.0]), atol=1e-9), p
    sections.append(line_points(p, EX, ARM_LEN + BACK_LEN))

    # 5) tip curl of arm B, traversed forwards to the free tip
    p = sections[-1][-1]
    assert np.allclose(p, np.array([ARM_LEN, PRONG_SPACING, 0.0]), atol=1e-9), p
    pts, _ = arc_points(p, EX, -EY, TIP_R, TIP_ANGLE, +1)
    sections.append(pts)

    centerline = np.vstack(sections)
    gaps = np.linalg.norm(np.diff(centerline, axis=0), axis=1)
    assert gaps.max() < STRAIGHT_STEP * 1.5, gaps.max()
    return centerline


def sweep(centerline, radius, n_seg):
    """Sweep a circle along a polyline using parallel-transport frames."""
    tangent = np.gradient(centerline, axis=0)
    tangent /= np.linalg.norm(tangent, axis=1)[:, None]

    ref = np.array([0.0, 0.0, 1.0])
    if abs(np.dot(tangent[0], ref)) > 0.9:
        ref = np.array([0.0, 1.0, 0.0])
    normal = ref - np.dot(ref, tangent[0]) * tangent[0]
    normal /= np.linalg.norm(normal)

    theta = np.linspace(0.0, 2.0 * math.pi, n_seg, endpoint=False)
    cos_t, sin_t = np.cos(theta), np.sin(theta)
    verts = np.empty((len(centerline), n_seg, 3))
    normals = np.empty_like(verts)
    for i, (p, t) in enumerate(zip(centerline, tangent)):
        normal = normal - np.dot(normal, t) * t
        normal /= np.linalg.norm(normal)
        binormal = np.cross(t, normal)
        ring = np.outer(cos_t, normal) + np.outer(sin_t, binormal)
        verts[i] = p + radius * ring
        normals[i] = ring
    return verts, normals, tangent


def write_obj(path, verts, normals, tangents):
    n_ring, n_prof = verts.shape[1], verts.shape[0]
    lines = [
        "# Euro hook (pegboard hook) - looped euro hook, steel wire",
        "# Units: 1 unit = 1 mm. Panel face = plane x=0, arms point +X, +Z up.",
        "# Wire dia 4 mm, arms 200 mm, prong spacing 25.4 mm,",
        "# 180 deg rear loop, upturned tips 130 deg / R10 mm.",
        "o euro_hook_200mm",
    ]
    for p in verts.reshape(-1, 3):
        lines.append(f"v {p[0]:.4f} {p[1]:.4f} {p[2]:.4f}")
    for p in tangents:
        lines.append(f"v {p[0]:.4f} {p[1]:.4f} {p[2]:.4f}")  # 2 cap centers
    for n in normals.reshape(-1, 3):
        lines.append(f"vn {n[0]:.5f} {n[1]:.5f} {n[2]:.5f}")
    for s, t in zip((-1.0, 1.0), (tangents[0], tangents[-1])):
        lines.append(f"vn {s * t[0]:.5f} {s * t[1]:.5f} {s * t[2]:.5f}")

    v_cap_a = n_prof * n_ring + 1  # cap center at profile 0 (start of path)
    v_cap_b = n_prof * n_ring + 2  # cap center at last profile
    n_cap_a = n_prof * n_ring + 1
    n_cap_b = n_prof * n_ring + 2
    for i in range(n_prof - 1):
        for j in range(n_ring):
            j2 = (j + 1) % n_ring
            a = i * n_ring + j + 1
            b = i * n_ring + j2 + 1
            c = (i + 1) * n_ring + j2 + 1
            e = (i + 1) * n_ring + j + 1
            lines.append(f"f {a}//{a} {b}//{b} {c}//{c} {e}//{e}")
    for ring0, cap_v, cap_n in ((1, v_cap_a, n_cap_a),
                                ((n_prof - 1) * n_ring + 1, v_cap_b, n_cap_b)):
        for j in range(n_ring):
            a = ring0 + j
            b = ring0 + (j + 1) % n_ring
            lines.append(f"f {a}//{cap_n} {b}//{cap_n} {cap_v}//{cap_n}")
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


def main():
    center = build_centerline()
    verts, normals, tangents = sweep(center, WIRE_DIA / 2.0, RADIAL_SEGMENTS)

    lo = verts.reshape(-1, 3).min(axis=0)
    hi = verts.reshape(-1, 3).max(axis=0)
    print(f"centerline points : {len(center)}")
    print(f"bbox (mm)         : x[{lo[0]:.1f}, {hi[0]:.1f}] "
          f"y[{lo[1]:.1f}, {hi[1]:.1f}] z[{lo[2]:.1f}, {hi[2]:.1f}]")
    print(f"total length      : {np.linalg.norm(np.diff(center, axis=0), axis=1).sum():.0f} mm")

    write_obj(OUT_OBJ, verts, normals, tangents)
    np.save("/tmp/centerline.npy", center)
    print(f"written           : {OUT_OBJ} "
          f"({verts.size // 3 + 2} verts, {normals.size // 3 + 2} normals)")


if __name__ == "__main__":
    main()
