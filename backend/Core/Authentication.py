# backend/Core/Authentication.py

from backend.Config.UserModel import UserModel
from backend.Utils.Validators import (
    validate_email,
    validate_password,
    validate_fullname
)
from backend.Services.RSAService import RSAService
from backend.Services.PendingMessageService import PendingMessageService
from backend.Core.Encryption import EncryptionService
from backend.Config.MessageModel import MessageModel
from backend.Services.SessionService import SessionService

from datetime import datetime


class AuthenticationService:
    # ------------------------------------------------------------------ #
    # ĐĂNG KÝ
    # ------------------------------------------------------------------ #
    @staticmethod
    def register(email, full_name, password, confirm_password):
        """
        Returns: (success: bool, message: str, user_id: int|None)
        """
        # ---- Email ----
        ok, msg = validate_email(email)
        if not ok:
            return False, msg, None

        # ---- Full name ----
        ok, msg = validate_fullname(full_name)
        if not ok:
            return False, msg, None

        # ---- Password ----
        ok, msg = validate_password(password)
        if not ok:
            return False, msg, None

        if password != confirm_password:
            return False, "Mật khẩu xác nhận không khớp", None

        # ---- Gọi Model (Tạo User) ----
        success, message, user_id = UserModel.create_user(
            email=email,
            full_name=full_name,
            password=password
        )

        if success:
            # Sinh cặp khóa RSA tự động khi đăng ký
            rsa_success = RSAService.create_rsa_key_for_user(user_id)
            if not rsa_success:
                print(f"  Warning: Lỗi sinh RSA cho user {user_id}")

        return success, message, user_id

    
    @staticmethod
    def login(email, password):
        """
        Returns: (success: bool, message: str, user_data: dict|None)
        """
        if not email or not password:
            return False, "Vui lòng nhập email và mật khẩu", None

        # Xác thực user
        success, message, user_data = UserModel.verify_password(email, password)
        
        if not success or not user_data:
            return success, message, user_data
        
        user_id = user_data.get('user_id')
        
        # Tạo RSA keypair cho session này (hoặc đảm bảo nó tồn tại)
        print(f" Creating RSA keypair for user {user_id}...")
        rsa_success = RSAService.ensure_keypair_exists_or_create(user_id) # Dùng ensure để tránh tạo lại
        
        if not rsa_success:
            print(f"  Warning: Failed to create RSA keypair for user {user_id}")
        
        # XỬ LÝ PENDING MESSAGES đã được chuyển sang WebSocketHandler.handle_connect
        
        return success, message, user_data

    @staticmethod
    def process_pending_messages_on_login(user_id, socketio):
        """
        Mã hóa và lưu tất cả tin nhắn đang chờ khi user đăng nhập,
        VÀ emit event cho người gửi (sender) để họ biết tin nhắn đã được gửi.
        """
        try:
            # Lấy tất cả pending messages
            pending_msgs = PendingMessageService.get_pending_messages(user_id)
            
            if not pending_msgs or len(pending_msgs) == 0:
                print(f" No pending messages for user {user_id}")
                return
            
            print(f" Processing {len(pending_msgs)} pending message(s) for user {user_id}")
            
            # Lấy public key của user (vừa được tạo ở trên)
            receiver_pubkey = RSAService.get_public_key(user_id)
            
            if not receiver_pubkey:
                print(f" Cannot process pending: No public key for user {user_id}")
                return
            
            processed_count = 0
            failed_count = 0
            updates_to_emit = [] # Dữ liệu cần gửi cho sender
            
            for msg in pending_msgs:
                # BẮT ĐẦU LOGIC MÃ HÓA (GIỮ NGUYÊN)
                try:
                    conversation_id = msg['conversation_id']
                    sender_id = msg['sender_id']
                    plain_text = msg['plain_text']
                    
                    # Tạo hoặc lấy session key cho conversation
                    session_data = SessionService.get_session_key(conversation_id)
                    
                    if not session_data:
                        aes_key_plain = SessionService.create_session_key(conversation_id, sender_id)
                        if not aes_key_plain:
                            failed_count += 1
                            continue
                        session_data = SessionService.get_session_key(conversation_id)
                    
                    aes_key_plain_b64 = session_data['aes_key']
                    
                    # Mã hóa message với AES
                    aes_result = EncryptionService.encrypt_message(plain_text, aes_key_plain_b64)
                    if not aes_result:
                        failed_count += 1
                        continue
                    
                    encrypted_content = aes_result['encrypted_content']
                    nonce = aes_result['nonce']
                    tag = aes_result['tag']
                    hmac_value = EncryptionService.generate_hmac(encrypted_content, aes_key_plain_b64)
                    aes_key_encrypted = RSAService.encrypt_aes_key(user_id, aes_key_plain_b64)
                    
                    # Lưu vào messages table
                    success, message_id = MessageModel.create_message(
                        conversation_id=conversation_id,
                        sender_id=sender_id,
                        receiver_id=user_id,
                        message_encrypted=encrypted_content,
                        nonce=nonce, tag=tag,
                        hmac_value=hmac_value,
                        aes_key_encrypted=aes_key_encrypted
                    )
                    
                    if success:
                        processed_count += 1
                        
                        # Xóa pending message đã xử lý
                        PendingMessageService.delete_single_pending(msg['id'])
                        
                        # GỬI TIN NHẮN ĐÃ MÃ HÓA TỚI CHÍNH RECEIVER (USER ĐANG ĐĂNG NHẬP)
                        message_to_emit = {
                            'conversation_id': conversation_id,
                            'sender_id': sender_id,
                            'encrypted_content': encrypted_content,
                            'nonce_tag_data': f"{nonce}:{tag}",
                            'message_hash': hmac_value,
                            'sent_at': datetime.now().isoformat()
                        }
                        
                        # EMIT cho receiver (User vừa đăng nhập)
                        room_receiver = f"conversation_{conversation_id}"
                        socketio.emit('new_message', message_to_emit, room=room_receiver)
                        
                        # CHUẨN BỊ GỬI THÔNG BÁO CHO SENDER (CẬP NHẬT TRẠNG THÁI)
                        updates_to_emit.append({
                            'conversation_id': conversation_id,
                            'message_id': message_id,
                            'status': 'sent',
                            'sender_id': sender_id
                        })
                    else:
                        failed_count += 1
                    
                except Exception as e:
                    failed_count += 1
                    continue
            
            # GỬI THÔNG BÁO CHO TẤT CẢ SENDER (CẬP NHẬT TRẠNG THÁI UI)
            if updates_to_emit:
                # Lặp qua các updates để tìm SENDER và gửi thông báo
                sent_senders = set()
                for update in updates_to_emit:
                    sender = update['sender_id']
                    if sender and sender not in sent_senders:
                        # Gửi thông báo đến room cá nhân của SENDER
                        socketio.emit('pending_message_processed', {
                            'updates': [u for u in updates_to_emit if u['sender_id'] == sender]
                        }, room=f"user_{sender}")
                        sent_senders.add(sender)
            
            print(f" Processed {processed_count}/{len(pending_msgs)} pending messages (Failed: {failed_count})")
            
        except Exception as e:
            print(f" Error in process_pending_messages_on_login: {e}")
            import traceback
            traceback.print_exc()

    # ------------------------------------------------------------------ #
    # QUÊN MẬT KHẨU
    # ------------------------------------------------------------------ #
    @staticmethod
    def reset_password(email, new_password, confirm_password):
        """
        Returns: (success: bool, message: str)
        """
        # ---- Email ----
        ok, msg = validate_email(email)
        if not ok:
            return False, msg

        # ---- Password ----
        ok, msg = validate_password(new_password)
        if not ok:
            return False, msg

        if new_password != confirm_password:
            return False, "Mật khẩu xác nhận không khớp"

        # ---- Gọi Model ----
        success, message = UserModel.update_password(email, new_password)
        return success, message