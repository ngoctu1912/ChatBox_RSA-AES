# backend/Core/ChatManager.py

from backend.Config.MessageModel import MessageModel
from backend.Config.ConversationModel import ConversationModel
from backend.Services.SessionService import SessionService
from backend.Core.Encryption import EncryptionService 
from backend.Services.KeyManagementService import KeyManagementService 
from backend.Services.RSAService import RSAService
from backend.Services.PendingMessageService import PendingMessageService
from datetime import datetime

class ChatManager:
    @staticmethod
    def send_encrypted_message(sender_id: int, partner_id: int, plain_text_message: str):
        """
        Xử lý toàn bộ luồng gửi tin nhắn đã mã hóa.
        - Nếu receiver chưa có public key → Lưu vào pending_messages
        - Nếu receiver đã có public key → Mã hóa và gửi bình thường
        
        Returns: (success: bool, result_data: dict | str(error))
        """
        try:
            # 1. Lấy hoặc Tạo Conversation
            conversation_id = ConversationModel.get_or_create_conversation(sender_id, partner_id)
            if not conversation_id:
                return False, "Không thể tạo hoặc lấy Conversation ID."

            #  KIỂM TRA PUBLIC KEY CỦA NGƯỜI NHẬN (THÊM MỚI)
            # Trong ChatManager.send_encrypted_message
            print(f" Checking public key for user {partner_id}...")
            receiver_pubkey = RSAService.get_public_key(partner_id)
            

            if not receiver_pubkey:
                # NGƯỜI NHẬN CHƯA ĐĂNG NHẬP → LƯU VÀO PENDING QUEUE
                print(f"  User {partner_id} has no public key. Queueing message...")
                
                pending_id = PendingMessageService.save_pending_message(
                    sender_id=sender_id,
                    receiver_id=partner_id,
                    conversation_id=conversation_id,
                    plain_text=plain_text_message
                )
                
                if not pending_id:
                    return False, "Failed to queue message"
                
                return True, {
                    'status': 'pending',
                    'pending_id': pending_id,
                    'conversation_id': conversation_id,
                    'message': f'Message queued for user {partner_id}'
                }

# NGƯỜI NHẬN ĐÃ CÓ PUBLIC KEY → MÃ HÓA VÀ GỬI BÌNH THƯỜNG
# (code cũ tiếp tục...)
            
            # 3. NGƯỜI NHẬN ĐÃ CÓ PUBLIC KEY → MÃ HÓA VÀ GỬI BÌNH THƯỜNG
            
            # Kiểm tra/Tạo Session Key
            session_data = SessionService.get_session_key(conversation_id)
            aes_key_encrypted_for_db = None 

            is_key_exchange_needed = not SessionService.is_key_exchanged(conversation_id)
            
            if is_key_exchange_needed or not session_data:
                # KEY EXCHANGE
                init_result = KeyManagementService.initiate_key_exchange(
                    conversation_id, sender_id, partner_id)

                if not init_result:
                    return False, "Key Exchange thất bại. Không thể gửi tin nhắn."

                aes_key_encrypted_for_db = init_result['encrypted_aes_key']
                session_data = SessionService.get_session_key(conversation_id)
            
            aes_key_plain_b64 = session_data['aes_key']

            # 4. Mã hóa nội dung bằng AES-GCM
            aes_result = EncryptionService.encrypt_message(plain_text_message, aes_key_plain_b64)
            if not aes_result:
                return False, "Lỗi mã hóa AES."
            
            encrypted_content = aes_result['encrypted_content']
            nonce = aes_result['nonce']
            tag = aes_result['tag']
            
            # 5. Tạo HMAC
            hmac_value = EncryptionService.generate_hmac(encrypted_content, aes_key_plain_b64)
            if not hmac_value:
                return False, "Lỗi tạo HMAC."
            
            # 6. LƯU VÀO DATABASE
            nonce_tag_data_value = f"{nonce}:{tag}"
            
            success, message_id = MessageModel.create_message(
                conversation_id, 
                sender_id, 
                partner_id, 
                message_encrypted=encrypted_content, 
                nonce=nonce, tag=tag, hmac_value=hmac_value,
                aes_key_encrypted=aes_key_encrypted_for_db 
            )
            
            if success:
                # 7. Trả về dữ liệu đã mã hóa để gửi qua WebSocket
                return True, {
                    'status': 'sent',
                    'message_id': message_id,
                    'conversation_id': conversation_id,
                    'sender_id': sender_id,
                    'receiver_id': partner_id,
                    'encrypted_content': encrypted_content,
                    'nonce_tag_data': nonce_tag_data_value,
                    'message_hash': hmac_value,
                    'sent_at': datetime.now().isoformat()
                }
            
            return False, "Lỗi khi lưu tin nhắn vào Database."
            
        except Exception as e:
            print(f" Error send_encrypted_message: {e}")
            return False, f"Lỗi không xác định: {e}"
        
    @staticmethod
    def decrypt_received_message(message_data: dict, current_user_id: int):
        """
        Xử lý giải mã tin nhắn nhận được (Linh hoạt cho cả WS và DB).
        """
        conversation_id = message_data['conversation_id']
        
        # 1. Lấy AES key plain từ Session Service
        session_data = SessionService.get_session_key(conversation_id)
        if not session_data:
            return "[Error: Missing Session Key. Cannot Decrypt]", False
            
        aes_key_plain_b64 = session_data['aes_key']
        
        # 2. LẤY DỮ LIỆU ĐÃ MÃ HÓA VÀ HASH
        encrypted_content = message_data.get('encrypted_content') or message_data.get('message_encrypted')
        hmac_value = message_data.get('message_hash') or message_data.get('hmac')
        
        nonce_tag_data_full = message_data.get('nonce_tag_data') or f"{message_data.get('nonce')}:{message_data.get('tag')}"
        
        if not encrypted_content or not hmac_value:
             return "[Error: Missing encrypted content or hash]", False
        
        # 3. Verify HMAC
        if not EncryptionService.verify_hmac(encrypted_content, aes_key_plain_b64, hmac_value):
            return "[Error: Integrity Check Failed - Message Tampered]", False
        
        # 4. Tách Nonce và Tag
        try:
            nonce_b64, tag_b64 = nonce_tag_data_full.split(':', 1)
        except ValueError:
            return "[Error: Malformed Nonce/Tag Data]", False
        
        # 5. Giải mã nội dung
        decrypted_message = EncryptionService.decrypt_message(
            encrypted_content_b64=encrypted_content,
            nonce_b64=nonce_b64,
            tag_b64=tag_b64,
            aes_key_b64=aes_key_plain_b64
        )
        
        if decrypted_message.startswith("[Error:"):
            return decrypted_message, False

        return decrypted_message, True