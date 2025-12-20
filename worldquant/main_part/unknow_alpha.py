def load_alpha_expressions():
    # Path to the alpha file
    import os
    alpha_file_path = r'C:\Users\nay\Desktop\qr\qr\worldquant\main_part\unknow_alpha.txt'

    # Read the file and create the list
    alpha_expressions = []
    if os.path.exists(alpha_file_path):
        with open(alpha_file_path, 'r', encoding='utf-8') as f:
            # Read lines, strip whitespace, and filter out empty lines
            alpha_expressions = [line.strip() for line in f if line.strip()]
    
    return alpha_expressions

if __name__ == "__main__":
    alpha_expressions = load_alpha_expressions()
    print('total alpha expressions:', len(alpha_expressions))
    for expr in alpha_expressions:
        print(expr)