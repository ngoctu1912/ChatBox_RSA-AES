import base64
import os
import hashlib
import hmac
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes


class EncryptionService:
    """
    Service mã hóa/giải mã tin nhắn bằng AES-GCM
    """
    
    @staticmethod
    def encrypt_message(plain_text: str, aes_key_b64: str):
        """
        Mã hóa tin nhắn bằng AES-256-GCM
        
        Args:
            plain_text: Tin nhắn gốc
            aes_key_b64: AES key (base64 encoded)
        
        Returns:
            dict: {
                'encrypted_content': str (base64),
                'nonce': str (base64),
                'tag': str (base64)
            }
        """
        try:
            # Decode AES key
            aes_key = base64.b64decode(aes_key_b64)
            
            # Generate random nonce (12 bytes cho GCM)
            nonce = get_random_bytes(12)
            
            # Tạo cipher AES-GCM
            cipher = AES.new(aes_key, AES.MODE_GCM, nonce=nonce)
            
            # Mã hóa
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
    
    @staticmethod
    def decrypt_message(encrypted_content_b64: str, nonce_b64: str, 
                       tag_b64: str, aes_key_b64: str):
        """
        Giải mã tin nhắn bằng AES-256-GCM
        
        Args:
            encrypted_content_b64: Ciphertext (base64)
            nonce_b64: Nonce (base64)
            tag_b64: Authentication tag (base64)
            aes_key_b64: AES key (base64)
        
        Returns:
            str: Plain text hoặc None nếu lỗi
        """
        try:
            # Decode từ base64
            aes_key = base64.b64decode(aes_key_b64)
            ciphertext = base64.b64decode(encrypted_content_b64)
            nonce = base64.b64decode(nonce_b64)
            tag = base64.b64decode(tag_b64)
            
            # Tạo cipher
            cipher = AES.new(aes_key, AES.MODE_GCM, nonce=nonce)
            
            # Giải mã và verify tag
            plaintext = cipher.decrypt_and_verify(ciphertext, tag)
            
            return plaintext.decode('utf-8')
            
        except ValueError as e:
            # Tag verification failed - message bị tamper
            print(f"❌ Message authentication failed: {e}")
            return None
        except Exception as e:
            print(f"Error decrypt_message: {e}")
            return None
    
    @staticmethod
    def generate_hmac(message: str, secret_key: str):
        """
        Tạo HMAC cho message (để verify integrity)
        
        Args:
            message: Message content
            secret_key: Secret key
        
        Returns:
            str: HMAC (hex)
        """
        try:
            hmac_obj = hmac.new(
                secret_key.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha256
            )
            return hmac_obj.hexdigest()
        except Exception as e:
            print(f"Error generate_hmac: {e}")
            return None
    
    @staticmethod
    def verify_hmac(message: str, secret_key: str, provided_hmac: str):
        """
        Verify HMAC của message
        
        Returns:
            bool: True nếu hợp lệ
        """
        try:
            expected_hmac = EncryptionService.generate_hmac(message, secret_key)
            return hmac.compare_digest(expected_hmac, provided_hmac)
        except Exception as e:
            print(f"Error verify_hmac: {e}")
            return False
    
    @staticmethod
    def encrypt_message_with_hmac(plain_text: str, aes_key_b64: str):
        """
        Mã hóa tin nhắn và tạo HMAC
        
        Returns:
            dict: {
                'encrypted_content': str,
                'nonce': str,
                'tag': str,
                'hmac': str
            }
        """
        try:
            # Mã hóa
            result = EncryptionService.encrypt_message(plain_text, aes_key_b64)
            if not result:
                return None
            
            # Tạo HMAC cho encrypted content
            hmac_value = EncryptionService.generate_hmac(
                result['encrypted_content'],
                aes_key_b64
            )
            
            result['hmac'] = hmac_value
            return result
            
        except Exception as e:
            print(f"Error encrypt_message_with_hmac: {e}")
            return None


class EncryptionServiceCBC:
    """
    Alternative: AES-256-CBC mode (nếu cần compatibility)
    """
    
    BLOCK_SIZE = AES.block_size
    
    @staticmethod
    def _pad(data: bytes) -> bytes:
        """PKCS7 padding"""
        padding_length = EncryptionServiceCBC.BLOCK_SIZE - len(data) % EncryptionServiceCBC.BLOCK_SIZE
        return data + bytes([padding_length] * padding_length)
    
    @staticmethod
    def _unpad(data: bytes) -> bytes:
        """Remove PKCS7 padding"""
        padding_length = data[-1]
        return data[:-padding_length]
    
    @staticmethod
    def encrypt_message_cbc(plain_text: str, aes_key_b64: str):
        """
        Mã hóa bằng AES-256-CBC
        
        Returns:
            dict: {
                'encrypted_content': str,
                'iv': str
            }
        """
        try:
            aes_key = base64.b64decode(aes_key_b64)
            iv = get_random_bytes(EncryptionServiceCBC.BLOCK_SIZE)
            
            cipher = AES.new(aes_key, AES.MODE_CBC, iv)
            
            plain_bytes = plain_text.encode('utf-8')
            padded_data = EncryptionServiceCBC._pad(plain_bytes)
            ciphertext = cipher.encrypt(padded_data)
            
            return {
                'encrypted_content': base64.b64encode(ciphertext).decode('utf-8'),
                'iv': base64.b64encode(iv).decode('utf-8')
            }
            
        except Exception as e:
            print(f"Error encrypt_message_cbc: {e}")
            return None
    
    @staticmethod
    def decrypt_message_cbc(encrypted_content_b64: str, iv_b64: str, aes_key_b64: str):
        """
        Giải mã bằng AES-256-CBC
        
        Returns:
            str: Plain text
        """
        try:
            aes_key = base64.b64decode(aes_key_b64)
            ciphertext = base64.b64decode(encrypted_content_b64)
            iv = base64.b64decode(iv_b64)
            
            cipher = AES.new(aes_key, AES.MODE_CBC, iv)
            decrypted_padded = cipher.decrypt(ciphertext)
            decrypted = EncryptionServiceCBC._unpad(decrypted_padded)
            
            return decrypted.decode('utf-8')
            
        except Exception as e:
            print(f"Error decrypt_message_cbc: {e}")
            return None