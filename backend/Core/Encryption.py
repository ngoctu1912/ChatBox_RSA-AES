# backend/Core/Encryption.py (ĐÃ CẬP NHẬT)

import base64
import hashlib
import hmac
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes


class EncryptionService:
    """Service mã hóa/giải mã tin nhắn bằng AES-GCM và tạo HMAC"""
    
    # ------------------------------------------------------------------ #
    # AES ENCRYPTION (Nội dung tin nhắn)
    # ------------------------------------------------------------------ #
    @staticmethod
    def encrypt_message(plain_text: str, aes_key_b64: str):
        """Mã hóa tin nhắn bằng AES-256-GCM"""
        try:
            aes_key = base64.b64decode(aes_key_b64)
            # GCM nonces thường là 12 bytes
            nonce = get_random_bytes(12) 
            
            cipher = AES.new(aes_key, AES.MODE_GCM, nonce=nonce)
            plain_bytes = plain_text.encode('utf-8')
            ciphertext, tag = cipher.encrypt_and_digest(plain_bytes)
            
            return {
                'encrypted_content': base64.b64encode(ciphertext).decode('utf-8'),
                'nonce': base64.b64encode(nonce).decode('utf-8'),
                'tag': base64.b64encode(tag).decode('utf-8')
            }
            
        except Exception as e:
            print(f"Error encrypt_message: {e}")
            return None
    
    # ------------------------------------------------------------------ #
    # AES DECRYPTION (Giải mã nội dung)
    # ------------------------------------------------------------------ #
    @staticmethod
    def decrypt_message(encrypted_content_b64: str, nonce_b64: str, 
                       tag_b64: str, aes_key_b64: str):
        """Giải mã tin nhắn bằng AES-256-GCM"""
        try:
            aes_key = base64.b64decode(aes_key_b64)
            ciphertext = base64.b64decode(encrypted_content_b64)
            nonce = base64.b64decode(nonce_b64)
            tag = base64.b64decode(tag_b64)
            
            cipher = AES.new(aes_key, AES.MODE_GCM, nonce=nonce)
            plaintext = cipher.decrypt_and_verify(ciphertext, tag)
            
            return plaintext.decode('utf-8')
            
        except ValueError as e:
            # Lỗi xác thực Tag - tin nhắn bị thay đổi
            print(f" Message authentication failed: {e}")
            return "[Error: Decryption Failed or Message Tampered]"
        except Exception as e:
            print(f"Error decrypt_message: {e}")
            return "[Error: Unknown Decryption Error]"

    # ------------------------------------------------------------------ #
    # HMAC (Hash-based Message Authentication Code)
    # ------------------------------------------------------------------ #
    @staticmethod
    def generate_hmac(message: str, secret_key: str):
        """Tạo HMAC cho message (sử dụng secret_key là AES key plain)"""
        try:
            hmac_obj = hmac.new(
                base64.b64decode(secret_key), # Secret key phải là bytes
                message.encode('utf-8'),
                hashlib.sha256
            )
            return hmac_obj.hexdigest()
        except Exception as e:
            print(f"Error generate_hmac: {e}")
            return None
            
    @staticmethod
    def verify_hmac(message: str, secret_key: str, provided_hmac: str):
        """Verify HMAC của message"""
        try:
            expected_hmac = EncryptionService.generate_hmac(message, secret_key)
            return hmac.compare_digest(expected_hmac, provided_hmac)
        except Exception as e:
            return False