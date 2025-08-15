"""Encryption utilities for sensitive data like API keys"""

from cryptography.fernet import Fernet
import base64
import os
from typing import Optional

from utils.config import settings


class EncryptionService:
    def __init__(self):
        # In production, this should be stored securely (e.g., environment variable)
        self.key = self._get_or_create_key()
        self.cipher_suite = Fernet(self.key)

    def _get_or_create_key(self) -> bytes:
        """Get encryption key from environment or generate a new one"""
        key_str = getattr(settings, 'ENCRYPTION_KEY', None)
        if key_str:
            return key_str.encode()
        else:
            # Generate a new key (in production, this should be stored securely)
            return Fernet.generate_key()

    def encrypt(self, data: str) -> str:
        """Encrypt a string and return base64 encoded result"""
        if not data:
            return ""
        
        encrypted_data = self.cipher_suite.encrypt(data.encode())
        return base64.b64encode(encrypted_data).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt base64 encoded data and return original string"""
        if not encrypted_data:
            return ""
        
        try:
            decoded_data = base64.b64decode(encrypted_data.encode())
            decrypted_data = self.cipher_suite.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception:
            # Return empty string if decryption fails
            return ""

    def encrypt_dict(self, data: dict) -> dict:
        """Encrypt all values in a dictionary"""
        return {key: self.encrypt(value) for key, value in data.items()}

    def decrypt_dict(self, encrypted_data: dict) -> dict:
        """Decrypt all values in a dictionary"""
        return {key: self.decrypt(value) for key, value in encrypted_data.items()}


# Global encryption service instance
encryption_service = EncryptionService()