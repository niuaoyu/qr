"""
左心室心底开口检测器 (LV Base Opening Detector)
------------------------------------------------
基于内部射线探测法判断 LV 双层薄壳网格在心底方向是否存在非法开口。

流程概述：
1) 姿态归一化：PCA 对齐长轴到 +Z，并将较宽一端视为基底，置于 Z+。
2) 取探测点：在高度 50% 处切片，取最大闭合轮廓质心（若失败退化为质心）。
3) 射线探测：从探测点沿 +Z 的小锥体发射多条射线；
   - 所有射线命中网格 -> 封闭 (NO)
   - 任意射线逃逸 -> 存在开口 (YES)

依赖：
    pip install trimesh numpy
"""

from __future__ import annotations

import argparse
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple, Union

import numpy as np

try:
    import trimesh
except ImportError as e:  # pragma: no cover
    raise ImportError("请先安装 trimesh：pip install trimesh") from e


# ---------- 数据类 ----------
@dataclass
class DetectionResult:
    has_opening: bool           # 是否存在开口 (True=YES)
    result: str                 # "YES" 或 "NO"
    confidence: float           # 置信度 (0-1，命中率或逃逸率)
    probe_point: np.ndarray     # 探测点
    hit_count: int              # 射线命中数量
    total_rays: int             # 射线总数
    message: str                # 说明


# ---------- 核心检测类 ----------
class LVBaseOpeningDetector:
    def __init__(
        self,
        num_rays: int = 48,
        cone_angle_deg: float = 8.0,
        slice_height_ratio: float = 0.5,
        hit_threshold: float = 0.5,
        verbose: bool = False,
    ):
        """
        Args:
            num_rays: 锥形射线数量，越多越鲁棒（稍慢）
            cone_angle_deg: 锥半角（度），用于覆盖斜向开口
            slice_height_ratio: 切片高度比例 0~1（0=尖端，1=基底），默认腰部 0.5
            hit_threshold: 命中率阈值；低于该阈值判定为有开口
            verbose: 是否打印日志
        """
        self.num_rays = num_rays
        self.cone_angle_deg = cone_angle_deg
        self.slice_height_ratio = slice_height_ratio
        self.hit_threshold = hit_threshold
        self.verbose = verbose

        # 运行时状态
        self.mesh: Optional[trimesh.Trimesh] = None
        self.aligned_mesh: Optional[trimesh.Trimesh] = None
        self.probe_point: Optional[np.ndarray] = None
        self._rotation_matrix: Optional[np.ndarray] = None

    # ===== 公共接口 =====
    def detect(self, ply_path: Union[str, Path]) -> DetectionResult:
        """主检测入口：返回 YES/NO 及详情。"""
        self._log(f"加载网格: {ply_path}")
        self.mesh = self._load_mesh(ply_path)

        self._log("姿态归一化...")
        self.aligned_mesh = self._normalize_orientation()

        self._log("寻找探测点...")
        self.probe_point = self._find_probe_point()
        if self.probe_point is None:
            return DetectionResult(
                has_opening=True,
                result="YES",
                confidence=0.0,
                probe_point=np.zeros(3),
                hit_count=0,
                total_rays=self.num_rays,
                message="无法确定探测点，可能网格损坏",
            )

        self._log(f"射线探测（{self.num_rays} 条，锥角 {self.cone_angle_deg}°）...")
        hit_count, total_rays = self._cast_rays()
        hit_ratio = hit_count / total_rays if total_rays else 0.0
        has_opening = hit_ratio < self.hit_threshold

        message = self._build_message(hit_ratio, has_opening)
        result = DetectionResult(
            has_opening=has_opening,
            result="YES" if has_opening else "NO",
            confidence=1.0 - hit_ratio if has_opening else hit_ratio,
            probe_point=self.probe_point.copy(),
            hit_count=hit_count,
            total_rays=total_rays,
            message=message,
        )
        self._log(f"检测完成: {result.result}, 击中率 {hit_ratio:.1%}")
        return result

    # ===== 内部步骤 =====
    def _load_mesh(self, ply_path: Union[str, Path]) -> trimesh.Trimesh:
        path = Path(ply_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {path}")
        if path.suffix.lower() != ".ply":
            warnings.warn(f"文件扩展名不是 .ply: {path.suffix}")
        mesh = trimesh.load(str(path), force="mesh", skip_materials=True, process=True)
        if isinstance(mesh, trimesh.Scene):
            mesh = trimesh.util.concatenate(tuple(mesh.geometry.values()))
        mesh.remove_unreferenced_vertices()
        mesh.remove_degenerate_faces()
        self._log(f"  顶点数: {len(mesh.vertices)}, 面数: {len(mesh.faces)}")
        return mesh

    def _normalize_orientation(self) -> trimesh.Trimesh:
        mesh = self.mesh.copy()

        # 中心化
        centroid = mesh.vertices.mean(axis=0)
        mesh.vertices -= centroid

        # PCA 找长轴
        cov = np.cov(mesh.vertices.T)
        eigvals, eigvecs = np.linalg.eigh(cov)
        long_axis = eigvecs[:, np.argmax(eigvals)]
        R = trimesh.geometry.align_vectors(long_axis, np.array([0.0, 0.0, 1.0]))
        mesh.apply_transform(R)
        self._rotation_matrix = R

        # 保证基底朝上
        mesh = self._ensure_base_up(mesh)
        return mesh

    def _ensure_base_up(self, mesh: trimesh.Trimesh) -> trimesh.Trimesh:
        z = mesh.vertices[:, 2]
        z_min, z_max = float(z.min()), float(z.max())
        z_range = z_max - z_min
        if z_range <= 0:
            return mesh
        z_low = z_min + 0.1 * z_range
        z_high = z_max - 0.1 * z_range
        area_low = self._cross_section_area(mesh, z_low)
        area_high = self._cross_section_area(mesh, z_high)
        self._log(f"  Z-截面积≈{area_low:.2f}, Z+截面积≈{area_high:.2f}")
        oriented = mesh.copy()
        if area_low > area_high:
            # 上下颠倒
            flip = trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0])
            oriented.apply_transform(flip)
        return oriented

    def _cross_section_area(self, mesh: trimesh.Trimesh, z_height: float) -> float:
        try:
            sec = mesh.section(plane_origin=[0, 0, z_height], plane_normal=[0, 0, 1])
            if sec is None:
                return 0.0
            sec2d, _ = sec.to_planar()
            if sec2d is None or not hasattr(sec2d, "polygons_closed"):
                return 0.0
            return float(sum(abs(p.area) for p in sec2d.polygons_closed))
        except Exception as e:
            self._log(f"  截面积计算异常: {e}")
            return 0.0

    def _find_probe_point(self) -> Optional[np.ndarray]:
        mesh = self.aligned_mesh
        z = mesh.vertices[:, 2]
        z_min, z_max = float(z.min()), float(z.max())
        z_slice = z_min + self.slice_height_ratio * (z_max - z_min)
        try:
            sec = mesh.section(plane_origin=[0, 0, z_slice], plane_normal=[0, 0, 1])
            if sec is None:
                return self._fallback_probe()
            sec2d, transform = sec.to_planar()
            polys = list(sec2d.polygons_closed) if hasattr(sec2d, "polygons_closed") else []
            if not polys:
                return self._fallback_probe()
            largest = max(polys, key=lambda p: abs(p.area))
            centroid_2d = np.array(largest.centroid.coords[0])
            centroid_h = np.array([centroid_2d[0], centroid_2d[1], 0, 1])
            centroid_3d = (transform @ centroid_h)[:3]
            self._log(f"  探测点: {centroid_3d}")
            return centroid_3d
        except Exception as e:
            self._log(f"  探测点计算异常: {e}")
            return self._fallback_probe()

    def _fallback_probe(self) -> Optional[np.ndarray]:
        self._log("  使用备用探测点：网格质心")
        if self.aligned_mesh is None:
            return None
        return self.aligned_mesh.vertices.mean(axis=0)

    def _cast_rays(self) -> Tuple[int, int]:
        mesh = self.aligned_mesh
        origin = self.probe_point
        directions = self._cone_directions(
            main_dir=np.array([0.0, 0.0, 1.0]),
            n=self.num_rays,
            cone_angle_deg=self.cone_angle_deg,
        )
        origins = np.repeat(origin[None, :], len(directions), axis=0)
        try:
            hits_bool = mesh.ray.intersects_any(origins, directions)
            hit_count = int(np.count_nonzero(hits_bool))
        except Exception as e:
            self._log(f"  射线投射异常: {e}")
            hit_count = 0
        total = len(directions)
        self._log(f"  射线击中 {hit_count}/{total}")
        return hit_count, total

    def _cone_directions(self, main_dir: np.ndarray, n: int, cone_angle_deg: float) -> np.ndarray:
        main_dir = main_dir / np.linalg.norm(main_dir)
        if n <= 1 or cone_angle_deg <= 0:
            return np.array([main_dir])
        rng = np.random.default_rng(42)
        theta_max = np.deg2rad(cone_angle_deg)
        dirs = []
        # 基向量
        z_axis = np.array([0.0, 0.0, 1.0])
        R = trimesh.geometry.align_vectors(z_axis, main_dir)
        for _ in range(n):
            theta = theta_max * rng.random()
            phi = 2 * np.pi * rng.random()
            local = np.array([
                np.sin(theta) * np.cos(phi),
                np.sin(theta) * np.sin(phi),
                np.cos(theta),
            ])
            world = (R[:3, :3] @ local)
            dirs.append(world / np.linalg.norm(world))
        return np.vstack(dirs)

    def _build_message(self, hit_ratio: float, has_opening: bool) -> str:
        if has_opening:
            return (f"射线击中率 {hit_ratio:.1%} 低于阈值 {self.hit_threshold:.1%}，"
                    "判定心底方向存在开口 (YES)。")
        return (f"射线击中率 {hit_ratio:.1%} 高于阈值 {self.hit_threshold:.1%}，"
                "判定心底封闭正常 (NO)。")

    def _log(self, msg: str):
        if self.verbose:
            print(f"[LVDetector] {msg}")


# ---------- 批量与便捷接口 ----------
def batch_detect(ply_files: List[Union[str, Path]], verbose: bool = False, **kwargs) -> dict:
    detector = LVBaseOpeningDetector(verbose=verbose, **kwargs)
    results = {}
    for fp in ply_files:
        try:
            res = detector.detect(fp)
            results[str(fp)] = res
        except Exception as e:
            results[str(fp)] = DetectionResult(
                has_opening=True,
                result="ERROR",
                confidence=0.0,
                probe_point=np.zeros(3),
                hit_count=0,
                total_rays=0,
                message=f"处理错误: {e}",
            )
    return results


def detect_single(ply_path: Union[str, Path], verbose: bool = False) -> str:
    detector = LVBaseOpeningDetector(verbose=verbose)
    return detector.detect(ply_path).result


# ---------- 命令行 ----------
def main():
    parser = argparse.ArgumentParser(description="左心室心底开口检测器 (YES/NO)")
    parser.add_argument("files", nargs="+", help="PLY 文件路径")
    parser.add_argument("--cone", type=float, default=8.0, help="锥半角(度)")
    parser.add_argument("--rays", type=int, default=48, help="射线数量")
    parser.add_argument("--threshold", type=float, default=0.5, help="命中率阈值")
    parser.add_argument("-v", "--verbose", action="store_true", help="显示详细日志")
    args = parser.parse_args()

    detector = LVBaseOpeningDetector(
        num_rays=args.rays,
        cone_angle_deg=args.cone,
        hit_threshold=args.threshold,
        verbose=args.verbose,
    )

    for f in args.files:
        print(f"\n处理: {f}")
        try:
            res = detector.detect(f)
            print(f"结果: {res.result} | 击中 {res.hit_count}/{res.total_rays} | 置信度 {res.confidence:.2f}")
            print(res.message)
        except Exception as e:
            print(f"错误: {e}")


if __name__ == "__main__":  # pragma: no cover
    main()
