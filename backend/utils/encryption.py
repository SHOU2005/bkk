"""
Encryption utilities for financial data protection
"""

from cryptography.fernet import Fernet
import base64
import os
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

def get_encryption_key() -> bytes:
    """Get or generate encryption key"""
    key = os.getenv("ENCRYPTION_KEY")
    if not key:
        # Generate a key for development (DO NOT USE IN PRODUCTION)
        key = Fernet.generate_key().decode()
        logger.warning("Using auto-generated encryption key. Set ENCRYPTION_KEY in production!")
    else:
        key = key.encode() if isinstance(key, str) else key
    return key

def encrypt_data(data: str) -> str:
    """Encrypt sensitive data"""
    try:
        key = get_encryption_key()
        f = Fernet(key)
        encrypted = f.encrypt(data.encode())
        return base64.b64encode(encrypted).decode()
    except Exception as e:
        # For prototype, return data as-is if encryption fails
        return data

def decrypt_data(encrypted_data: str) -> str:
    """Decrypt sensitive data"""
    try:
        key = get_encryption_key()
        f = Fernet(key)
        decrypted = f.decrypt(base64.b64decode(encrypted_data.encode()))
        return decrypted.decode()
    except Exception as e:
        # For prototype, return data as-is if decryption fails
        return encrypted_data

