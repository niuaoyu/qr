"""
Detect whether an LV mesh (double-layer, water-tight) has an opening at the base.

Algorithm (internal ray casting):
1) PCA 对齐长轴到 +Z，并判断较宽一端为基底（放到 +Z）。
2) 在中部截面选一个探测点（腔内腰部），默认取 Z 轴 50% 处截面质心。
3) 从该点沿 +Z 的小锥体发射多条射线：
      - 若任意射线逃逸（无交点），判定基底存在开口 -> YES
      - 所有射线命中网格 -> NO

运行示例：
    python axis.py C:/Users/nay/Desktop/sxis/mesh/mesh/0/ED.ply --cone 8 --rays 48
依赖：trimesh（可选 rtree 加速）
"""

import argparse
import numpy as np
import trimesh


# ---------- Mesh I/O ----------
def load_mesh(path: str) -> trimesh.Trimesh:
    """Load mesh from path and做基础清理."""
    mesh = trimesh.load(path, force="mesh", skip_materials=True, process=True)
    if isinstance(mesh, trimesh.Scene):
        mesh = trimesh.util.concatenate(tuple(mesh.geometry.values()))
    mesh.remove_unreferenced_vertices()
    mesh.remove_degenerate_faces()
    return mesh


# ---------- Orientation ----------
def align_to_z(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    """PCA 将长轴对齐到 +Z。"""
    verts = mesh.vertices - mesh.vertices.mean(axis=0)
    cov = np.cov(verts.T)
    eigvals, eigvecs = np.linalg.eigh(cov)
    long_axis = eigvecs[:, np.argmax(eigvals)]
    R = trimesh.geometry.align_vectors(long_axis, np.array([0.0, 0.0, 1.0]))
    aligned = mesh.copy()
    aligned.apply_transform(R)
    return aligned


def orient_base_up(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    """
    判断宽的一端为基底，置于 +Z。
    通过比较上下半部的点云散度决定是否翻转。
    """
    z = mesh.vertices[:, 2]
    z_min, z_max = float(z.min()), float(z.max())
    z_mid = 0.5 * (z_min + z_max)
    top = mesh.vertices[z > z_mid]
    bottom = mesh.vertices[z < z_mid]
    top_spread = np.linalg.norm(np.std(top, axis=0)) if len(top) else 0.0
    bottom_spread = np.linalg.norm(np.std(bottom, axis=0)) if len(bottom) else 0.0
    oriented = mesh.copy()
    if top_spread < bottom_spread:  # 如果上面更窄，翻转到使基底朝上
        flip = trimesh.transformations.rotation_matrix(np.pi, [1.0, 0.0, 0.0])
        oriented.apply_transform(flip)
    return oriented


# ---------- Probe point ----------
def pick_probe_point(mesh: trimesh.Trimesh) -> np.ndarray:
    """
    在高度 50% 处取截面质心，作为腔内探测点。
    若截面点为空，退化为包围盒质心。
    """
    z = mesh.vertices[:, 2]
    z_min, z_max = float(z.min()), float(z.max())
    z_mid = z_min + 0.5 * (z_max - z_min)
    thickness = 0.01 * max(z_max - z_min, 1e-6)  # 薄切片
    mask = (z > z_mid - thickness) & (z < z_mid + thickness)
    if mask.any():
        centroid = mesh.vertices[mask].mean(axis=0)
    else:
        centroid = mesh.bounding_box.centroid
    return centroid


# ---------- Ray casting ----------
def build_cone_directions(cone_angle_deg: float, n_rays: int, seed: int = 42) -> np.ndarray:
    """在 +Z 附近的小锥体内均匀随机生成射线方向。"""
    rng = np.random.default_rng(seed)
    theta_max = np.deg2rad(cone_angle_deg)
    dirs = []
    for _ in range(n_rays):
        theta = theta_max * rng.random()
        phi = 2 * np.pi * rng.random()
        dx = np.sin(theta) * np.cos(phi)
        dy = np.sin(theta) * np.sin(phi)
        dz = np.cos(theta)
        d = np.array([dx, dy, dz], dtype=float)
        d /= np.linalg.norm(d)
        dirs.append(d)
    return np.vstack(dirs)


def has_base_opening(mesh: trimesh.Trimesh, probe: np.ndarray, cone_angle_deg: float = 8.0, n_rays: int = 48) -> bool:
    """
    任意射线逃逸视为存在开口。
    返回 True 表示有开口（YES），False 表示封闭（NO）。
    """
    directions = build_cone_directions(cone_angle_deg, n_rays)
    origins = np.repeat(probe.reshape(1, 3), len(directions), axis=0)
    hits = mesh.ray.intersects_first(origins, directions)
    return np.any(hits == -1)


# ---------- Main detection ----------
def detect(mesh_path: str, cone_angle_deg: float = 8.0, n_rays: int = 48) -> str:
    mesh = load_mesh(mesh_path)
    mesh = align_to_z(mesh)
    mesh = orient_base_up(mesh)
    probe = pick_probe_point(mesh)
    opening = has_base_opening(mesh, probe, cone_angle_deg, n_rays)
    return "YES" if opening else "NO"


def main():
    parser = argparse.ArgumentParser(description="Detect base opening on LV mesh (YES/NO).")
    parser.add_argument("mesh", nargs="?", default=r"C:/Users/nay/Desktop/sxis/mesh/mesh/0/ED.ply",
                        help="Path to LV mesh (.ply)")
    parser.add_argument("--cone", type=float, default=8.0, help="Cone angle in degrees for probe rays.")
    parser.add_argument("--rays", type=int, default=48, help="Number of rays in the probe cone.")
    args = parser.parse_args()
    result = detect(args.mesh, args.cone, args.rays)
    print(result)


if __name__ == "__main__":
    main()
