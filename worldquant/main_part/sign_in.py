import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import requests
import json
from os.path import expanduser
from requests.auth import HTTPBasicAuth

def sign_in():


    with open(expanduser(r"C:\Users\nay\Desktop\qr\qr\worldquant\idcode.txt")) as f:
        credentials = json.load(f)
    username,password = credentials
    sess = requests.Session()
    sess.auth = HTTPBasicAuth(username, password)
    response = sess.post('https://api.worldquantbrain.com/authentication')
    return sess

if __name__ == "__main__":
    sess = sign_in()
