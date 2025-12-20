import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# sys.path.append(r"C:\Users\nay\Desktop\qr\qr\worldquant")

from main_part.sign_in import sign_in
sess = sign_in()

from main_part.unknow_alpha import load_alpha_expressions
alpha_expressions = load_alpha_expressions()
print('total alpha expressions:', len(alpha_expressions))
# for expr in alpha_expressions:
#     print(expr)

from main_part.compositional_expression import create_alpha_list
alpha_list = create_alpha_list(alpha_expressions)

from main_part.send import send_alpha_list
send_alpha_list(sess, alpha_list)
