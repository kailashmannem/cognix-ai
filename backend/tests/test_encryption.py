"""Tests for encryption utilities"""

import pytest
from unittest.mock import patch, MagicMock

from utils.encryption import EncryptionService, encryption_service, encrypt_data, decrypt_data


class TestEncryptionService:
    """Test cases for EncryptionService"""
    
    @pytest.fixture
    def encryption_service_instance(self):
        return EncryptionService()
    
    def test_encrypt_decrypt_string(self, encryption_service_instance):
        """Test basic string encryption and decryption"""
        original_text = "This is a test string"
        
        # Encrypt
        encrypted_text = encryption_service_instance.encrypt(original_text)
        assert encrypted_text != original_text
        assert len(encrypted_text) > 0
        
        # Decrypt
        decrypted_text = encryption_service_instance.decrypt(encrypted_text)
        assert decrypted_text == original_text
    
    def test_encrypt_decrypt_empty_string(self, encryption_service_instance):
        """Test encryption and decryption of empty string"""
        original_text = ""
        
        encrypted_text = encryption_service_instance.encrypt(original_text)
        assert encrypted_text == ""
        
        decrypted_text = encryption_service_instance.decrypt(encrypted_text)
        assert decrypted_text == ""
    
    def test_encrypt_decrypt_api_key(self, encryption_service_instance):
        """Test encryption and decryption of API key"""
        api_key = "sk-1234567890abcdef1234567890abcdef1234567890abcdef"
        
        encrypted_key = encryption_service_instance.encrypt(api_key)
        assert encrypted_key != api_key
        assert len(encrypted_key) > len(api_key)
        
        decrypted_key = encryption_service_instance.decrypt(encrypted_key)
        assert decrypted_key == api_key
    
    def test_encrypt_decrypt_mongodb_connection(self, encryption_service_instance):
        """Test encryption and decryption of MongoDB connection string"""
        connection_string = "mongodb://user:password@localhost:27017/database?authSource=admin"
        
        encrypted_connection = encryption_service_instance.encrypt(connection_string)
        assert encrypted_connection != connection_string
        assert len(encrypted_connection) > 0
        
        decrypted_connection = encryption_service_instance.decrypt(encrypted_connection)
        assert decrypted_connection == connection_string
    
    def test_encrypt_decrypt_dict(self, encryption_service_instance):
        """Test dictionary encryption and decryption"""
        original_dict = {
            "openai": "sk-1234567890abcdef1234567890abcdef1234567890abcdef",
            "gemini": "AIzaSyDaGmWKa4JsXZ-HjGw7_SzT1TzqK1qNiOY",
            "groq": "gsk_1234567890abcdef1234567890abcdef1234567890abcdef"
        }
        
        # Encrypt dictionary
        encrypted_dict = encryption_service_instance.encrypt_dict(original_dict)
        assert encrypted_dict != original_dict
        assert len(encrypted_dict) == len(original_dict)
        
        for key in original_dict:
            assert key in encrypted_dict
            assert encrypted_dict[key] != original_dict[key]
            assert len(encrypted_dict[key]) > 0
        
        # Decrypt dictionary
        decrypted_dict = encryption_service_instance.decrypt_dict(encrypted_dict)
        assert decrypted_dict == original_dict
    
    def test_encrypt_decrypt_special_characters(self, encryption_service_instance):
        """Test encryption and decryption of strings with special characters"""
        special_strings = [
            "password@123!",
            "mongodb://user:p@ssw0rd@host:27017/db",
            "key_with_unicode_éñ中文",
            "multi\nline\nstring",
            "tabs\tand\tspaces   "
        ]
        
        for original in special_strings:
            encrypted = encryption_service_instance.encrypt(original)
            decrypted = encryption_service_instance.decrypt(encrypted)
            assert decrypted == original
    
    def test_decrypt_invalid_data(self, encryption_service_instance):
        """Test decryption of invalid encrypted data"""
        invalid_data = [
            "invalid_base64_data",
            "dGVzdA==",  # Valid base64 but not encrypted data
            "",
            "not_encrypted_at_all"
        ]
        
        for invalid in invalid_data:
            decrypted = encryption_service_instance.decrypt(invalid)
            assert decrypted == ""  # Should return empty string on failure
    
    def test_encrypt_none_value(self, encryption_service_instance):
        """Test encryption of None value"""
        # Should handle None gracefully
        encrypted = encryption_service_instance.encrypt(None)
        assert encrypted == ""
        
        decrypted = encryption_service_instance.decrypt("")
        assert decrypted == ""
    
    def test_key_generation_with_environment_variable(self):
        """Test key generation when environment variable is set"""
        test_key = b"test_key_32_bytes_long_for_fernet"
        
        with patch('utils.encryption.settings') as mock_settings:
            mock_settings.ENCRYPTION_KEY = test_key.decode()
            
            service = EncryptionService()
            assert service.key == test_key
    
    def test_key_generation_without_environment_variable(self):
        """Test key generation when no environment variable is set"""
        with patch('utils.encryption.settings') as mock_settings:
            mock_settings.ENCRYPTION_KEY = None
            
            with patch('cryptography.fernet.Fernet.generate_key') as mock_generate:
                test_key = b"generated_key_32_bytes_for_test"
                mock_generate.return_value = test_key
                
                service = EncryptionService()
                assert service.key == test_key
                mock_generate.assert_called_once()
    
    def test_consistency_across_instances(self):
        """Test that different instances with same key produce consistent results"""
        test_key = b"consistent_key_32_bytes_for_test"
        
        with patch('utils.encryption.settings') as mock_settings:
            mock_settings.ENCRYPTION_KEY = test_key.decode()
            
            service1 = EncryptionService()
            service2 = EncryptionService()
            
            original_text = "test consistency"
            
            encrypted1 = service1.encrypt(original_text)
            decrypted2 = service2.decrypt(encrypted1)
            
            assert decrypted2 == original_text
    
    def test_large_data_encryption(self, encryption_service_instance):
        """Test encryption and decryption of large data"""
        # Create a large string (1MB)
        large_string = "A" * (1024 * 1024)
        
        encrypted = encryption_service_instance.encrypt(large_string)
        assert encrypted != large_string
        assert len(encrypted) > 0
        
        decrypted = encryption_service_instance.decrypt(encrypted)
        assert decrypted == large_string
    
    def test_multiple_encryptions_different_results(self, encryption_service_instance):
        """Test that multiple encryptions of same data produce different results"""
        original_text = "same input text"
        
        encrypted1 = encryption_service_instance.encrypt(original_text)
        encrypted2 = encryption_service_instance.encrypt(original_text)
        
        # Should be different due to random IV/nonce
        assert encrypted1 != encrypted2
        
        # But both should decrypt to same original
        decrypted1 = encryption_service_instance.decrypt(encrypted1)
        decrypted2 = encryption_service_instance.decrypt(encrypted2)
        
        assert decrypted1 == original_text
        assert decrypted2 == original_text


class TestGlobalEncryptionFunctions:
    """Test global encryption convenience functions"""
    
    def test_encrypt_data_function(self):
        """Test global encrypt_data function"""
        original = "test data for global function"
        encrypted = encrypt_data(original)
        
        assert encrypted != original
        assert len(encrypted) > 0
    
    def test_decrypt_data_function(self):
        """Test global decrypt_data function"""
        original = "test data for global function"
        encrypted = encrypt_data(original)
        decrypted = decrypt_data(encrypted)
        
        assert decrypted == original
    
    def test_global_functions_consistency(self):
        """Test that global functions use the same service instance"""
        original = "consistency test"
        
        encrypted = encrypt_data(original)
        decrypted = decrypt_data(encrypted)
        
        assert decrypted == original
    
    def test_global_service_instance(self):
        """Test that global encryption_service instance works correctly"""
        original = "global service test"
        
        encrypted = encryption_service.encrypt(original)
        decrypted = encryption_service.decrypt(encrypted)
        
        assert decrypted == original


class TestEncryptionEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_encryption_with_corrupted_key(self):
        """Test behavior with corrupted encryption key"""
        service = EncryptionService()
        
        # Corrupt the cipher suite
        service.cipher_suite = None
        
        # Should handle gracefully
        encrypted = service.encrypt("test")
        assert encrypted == ""  # Should return empty on error
    
    def test_decryption_with_corrupted_cipher(self):
        """Test decryption with corrupted cipher"""
        service = EncryptionService()
        original = "test data"
        encrypted = service.encrypt(original)
        
        # Corrupt the cipher suite
        service.cipher_suite = None
        
        # Should handle gracefully
        decrypted = service.decrypt(encrypted)
        assert decrypted == ""  # Should return empty on error
    
    def test_encrypt_decrypt_unicode_edge_cases(self):
        """Test encryption with various Unicode edge cases"""
        unicode_strings = [
            "🚀 Rocket emoji",
            "中文测试",
            "العربية",
            "русский",
            "🎉🎊🎈 Multiple emojis",
            "\x00\x01\x02 Control characters",
            "Mixed: English 中文 العربية 🚀"
        ]
        
        service = EncryptionService()
        
        for original in unicode_strings:
            encrypted = service.encrypt(original)
            decrypted = service.decrypt(encrypted)
            assert decrypted == original, f"Failed for: {original}"


if __name__ == "__main__":
    pytest.main([__file__])