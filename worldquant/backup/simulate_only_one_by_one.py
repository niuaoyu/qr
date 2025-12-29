import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# sys.path.append(r"C:\Users\nay\Desktop\qr\qr\worldquant")

from qr.worldquant.io.sign_in import sign_in
from qr.worldquant.io.load_alpha_expressions import load_alpha_expressions
from qr.worldquant.backup.compositional_expression import create_alpha_list
from qr.worldquant.backup.send import send_alpha_list


sess = sign_in()
alpha_expressions = load_alpha_expressions()
print('total alpha expressions:', len(alpha_expressions))
# for expr in alpha_expressions:
#     print(expr)
alpha_list = create_alpha_list(alpha_expressions)
send_alpha_list(sess, alpha_list)
