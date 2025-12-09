import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or os.urandom(24).hex()
    # остальные конфиги (если понадобятся)