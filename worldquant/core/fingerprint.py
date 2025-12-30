"""
指纹生成模块 - 用于 Alpha 表达式去重
"""
import hashlib
import re


def make_fingerprint(expression: str, settings: dict) -> str:
    """
    生成 Alpha 唯一指纹
    """
    expr = re.sub(r"\s+", " ", (expression or "").strip())
    key_parts = [
        expr,
        str(settings.get("neutralization", "")),
        str(settings.get("delay", "")),
        str(settings.get("decay", "")),
        str(settings.get("universe", "")),
        str(settings.get("truncation", "")),
        str(settings.get("region", "")),
        str(settings.get("nanHandling", "")),
        str(settings.get("instrumentType", "")),
        str(settings.get("unitHandling", "")),
        str(settings.get("pasteurization", "")),
    ]
    key = "|".join(key_parts)
    return hashlib.sha256(key.encode("utf-8")).hexdigest()
