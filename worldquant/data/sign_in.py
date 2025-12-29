import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import requests
from requests.auth import HTTPBasicAuth
from global_config import USER

def sign_in(choice='lab'):
    if choice not in USER:
        raise ValueError(f"Invalid choice: '{choice}'. Valid choices are: {list(USER.keys())}")
    username, password = USER[choice]['name'], USER[choice]['password']
    sess = requests.Session()
    sess.auth = HTTPBasicAuth(username, password)
    response = sess.post('https://api.worldquantbrain.com/authentication')
    response.raise_for_status()  # Raise an exception for bad status codes (e.g., 401 Unauthorized)
    return sess

if __name__ == "__main__":
    try:
        # Attempt to sign in with the default user 'lab'
        session = sign_in()
        print("Sign-in successful!")
        # To sign in as another user, pass the key, e.g., session = sign_in('mylab')
    except (ValueError, requests.exceptions.RequestException) as e:
        print(f"Sign-in failed: {e}")
