from pathlib import Path
from typing import Iterable, Union
import os
def load_alpha_expressions(filepath: Union[str, Path],  encoding: str = "utf-8") -> None:
    # Path to the alpha file
    alpha_file_path = Path(filepath)
    # Read the file and create the list
    alpha_expressions = []
    if os.path.exists(alpha_file_path):
        with open(alpha_file_path, 'r', encoding='utf-8') as f:
            # Read lines, strip whitespace, and filter out empty lines
            alpha_expressions = [line.strip() for line in f if line.strip()]
    
    return alpha_expressions

if __name__ == "__main__":
    alpha_expressions = load_alpha_expressions(r'C:\Users\nay\Desktop\qr\qr\worldquant\ready_to_test_alpha_list\unknow_alpha.txt')
    print('total alpha expressions:', len(alpha_expressions))