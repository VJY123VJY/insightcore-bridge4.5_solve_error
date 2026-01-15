from datetime import datetime, timedelta
from jose import jwt

SECRET_KEY = "my_secret_key"
ALGORITHM = "HS256"

def generate_token():
    payload = {
        "user_id": 1,
        "exp": datetime.utcnow() + timedelta(minutes=30)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

print(generate_token())
