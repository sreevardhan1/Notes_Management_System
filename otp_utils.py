# OTP helpers (in-memory, dev-only)
import random, time
OTPS = {}   # store: mobile -> {'otp':..., 'created_at':...}

def generate_otp():
    return f"{random.randint(1000,9999)}"

def save_otp(mobile, otp, validity_seconds=300):
    OTPS[mobile] = {'otp': otp, 'created_at': time.time(), 'validity': validity_seconds}

def verify_otp(mobile, user_otp):
    data = OTPS.get(mobile)
    if not data:
        return False
    if time.time() - data['created_at'] > data.get('validity', 300):
        del OTPS[mobile]
        return False
    if data['otp'] == user_otp:
        del OTPS[mobile]
        return True
    return False

def get_stored_otp(mobile):
    return OTPS.get(mobile, {}).get('otp')
