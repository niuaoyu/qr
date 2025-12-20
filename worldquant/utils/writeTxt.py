from pathlib import Path
from typing import Iterable, Union

def write_lines(filepath: Union[str, Path], lines: Union[str, Iterable[str]], encoding: str = "utf-8") -> None:
    """
    将字符串写入 txt，每个字符串占一行。默认追加写入。
    lines 可以是单个字符串或可迭代的字符串序列。
    """
    path = Path(filepath)
    if isinstance(lines, str):
        lines_to_write = [lines]
    else:
        lines_to_write = list(lines)

    with path.open("a", encoding=encoding) as f:
        for line in lines_to_write:
            f.write(f"{line}\n")

write_lines(r"C:\Users\nay\Desktop\qr\qr\worldquant\utils\alphalist.txt", "First line")