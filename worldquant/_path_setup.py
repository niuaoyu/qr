# c:\qr\qr\worldquant\_path_setup.py
import os
import sys

_ROOT_DIRNAME = "qr"
_ROOT_MARKERS = ("AGENTS.md", "config.yaml", ".git")


def _is_project_root(candidate_dir):
    qr_dir = os.path.join(candidate_dir, _ROOT_DIRNAME)
    if not os.path.isdir(qr_dir):
        return False
    for marker in _ROOT_MARKERS:
        if os.path.exists(os.path.join(qr_dir, marker)):
            return True
    return os.path.isdir(os.path.join(qr_dir, "worldquant"))


def ensure_project_root(start_path=None):
    env_root = os.environ.get("QR_PROJECT_ROOT")
    if env_root and os.path.isdir(env_root):
        if env_root not in sys.path:
            sys.path.append(env_root)
        return env_root

    current_path = os.path.abspath(start_path or __file__)
    if os.path.isfile(current_path):
        current_path = os.path.dirname(current_path)

    project_root = None
    d = current_path
    while d != os.path.dirname(d):
        if _is_project_root(d):
            project_root = d
            break
        d = os.path.dirname(d)

    if project_root and project_root not in sys.path:
        sys.path.append(project_root)
        os.environ["QR_PROJECT_ROOT"] = project_root
    return project_root


ensure_project_root()
