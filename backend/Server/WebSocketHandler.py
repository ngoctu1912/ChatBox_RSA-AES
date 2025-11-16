# backend/Server/WebSocketHandler.py

from flask_socketio import emit, join_room, leave_room
from backend.Services.KeyManagementService import KeyManagementService
from backend.Services.SessionService import SessionService
from backend.Utils.RedisClient import redis_client
from backend.Config.ConnectDB import connect_to_database
from backend.Middleware.WebSocketAuth import RateLimiter
from backend.Core.ChatManager import ChatManager
from backend.Services.RSAService import RSAService
from backend.Services.PendingMessageService import PendingMessageService
from backend.Core.Authentication import AuthenticationService
from backend.Config.UserModel import UserModel 
from datetime import datetime


class WebSocketHandler:
    """
    Xử lý tất cả WebSocket events
    """
    
    def __init__(self, socketio):
        self.socketio = socketio
        self.redis_client = redis_client
        self.rate_limiter = RateLimiter(redis_client)
        self.register_handlers()
    
    def register_handlers(self):
        """Đăng ký tất cả event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect():
            from flask import request, session
            user_id = session.get('user_id')
            sid = request.sid
            
            if not user_id:
                print(f"  Client connected with SID {sid}. Session is empty.")
                return True 
            
            # 1. CẬP NHẬT TRẠNG THÁI ONLINE TRONG DB
            UserModel.update_online_status(user_id, True)
            
            # 2. Lưu socket ID vào Redis 
            redis_client.hset('online_users', str(user_id), sid)
            redis_client.sadd('active_sids', sid)
            
            # Join room cá nhân
            join_room(f"user_{user_id}")
            
            print(f" User {user_id} connected with SID {sid}")
            
            # 3. Thông báo online cho TẤT CẢ clients (bao gồm cả chính mình để debug)
            # Sử dụng broadcast=True và include_self=True để đảm bảo mọi client nhận được
            self.socketio.emit('user_online', {
                'user_id': user_id,
                'is_online': True
            }, broadcast=True, include_self=True)
            
            print(f" Broadcasting user_online event for user {user_id}")
            
            # 4. KIỂM TRA PENDING MESSAGES VÀ THÔNG BÁO 
            pending_count = PendingMessageService.get_pending_count(user_id)
            if pending_count > 0:
                # Gửi thông báo đến room cá nhân
                emit('pending_messages_notification', {
                    'count': pending_count,
                    'message': f'You have {pending_count} pending message(s)'
                }, room=f"user_{user_id}")
            
            # 5. XỬ LÝ PENDING MESSAGES KHI KẾT NỐI (CỐT LÕI)
            AuthenticationService.process_pending_messages_on_login(user_id, self.socketio) 
            
            return True
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            from flask import request, session
            user_id = session.get('user_id')
            sid = request.sid
            
            if user_id:
                # 1. CẬP NHẬT TRẠNG THÁI OFFLINE TRONG DB
                UserModel.update_online_status(user_id, False)
                
                # 2. Xóa khỏi Redis 
                redis_client.hdel('online_users', str(user_id))
                redis_client.srem('active_sids', sid)
                
                print(f" User {user_id} disconnected")
                
                # Thông báo offline cho TẤT CẢ clients
                self.socketio.emit('user_offline', {
                    'user_id': user_id,
                    'is_online': False
                }, namespace='/')
                
                print(f" Broadcasting user_offline event for user {user_id}")

        @self.socketio.on('login_event')
        def handle_login_event(data):
            """
            User login thành công qua API HTTP, emit event này để SocketIO cập nhật
            session và xử lý pending messages (chỉ nếu cần).
            """
            from flask import request, session
            
            user_id = data.get('user_id')
            sid = request.sid
            
            if not user_id:
                emit('error', {'message': 'Missing user_id'})
                return
            
            # Lưu user_id vào session 
            session['user_id'] = user_id
            
            # Join vào room cá nhân 
            room_name = f"user_{user_id}"
            join_room(room_name)
            
            # Ghi đè SID trong Redis
            redis_client.hset('online_users', str(user_id), sid)
            
            print(f" [LOGIN] User {user_id} joined personal room: {room_name}")
            
            # Xử lý pending messages đã được chuyển sang handle_connect
            # Tuy nhiên, vẫn cần kích hoạt cập nhật trạng thái online và emit
            
            # Cập nhật trạng thái (nếu connect/login_event bị gọi độc lập)
            UserModel.update_online_status(user_id, True)
            
            print(f" [LOGIN_EVENT] Preparing to broadcast user_online for user {user_id}")
            
            #  BROADCAST USER ONLINE SAU 300ms (ĐỂ FRONTEND ĐĂNG KÝ LISTENER)
            def delayed_broadcast():
                self.socketio.sleep(0.3)
                self.socketio.emit('user_online', {
                    'user_id': user_id,
                    'is_online': True
                }, namespace='/')
                print(f" [LOGIN_EVENT] Broadcasted user_online for user {user_id}")
            
            self.socketio.start_background_task(delayed_broadcast)
            
            # Xác nhận login thành công
            emit('login_success', {
                'message': 'Login successful',
                'user_id': user_id,
                'room': room_name
            }, room=request.sid)
        
        @self.socketio.on('join_conversation')
        def handle_join_conversation(data):
            """User tham gia conversation room"""
            from flask import session
            user_id = session.get('user_id') or data.get('user_id') 
            conversation_id = data.get('conversation_id')
            
            if not user_id or not conversation_id:
                emit('error', {'message': 'Missing user_id or conversation_id'})
                return
            
            room = f"conversation_{conversation_id}"
            join_room(room)
            
            print(f" [JOIN] User {user_id} joined {room}")
            emit('joined_conversation', {
                'conversation_id': conversation_id,
                'user_id': user_id
            }, room=room)
        
        @self.socketio.on('leave_conversation')
        def handle_leave_conversation(data):
            """User rời conversation room"""
            from flask import session
            user_id = session.get('user_id') or data.get('user_id')
            conversation_id = data.get('conversation_id')
            
            if not conversation_id:
                return
            
            room = f"conversation_{conversation_id}"
            leave_room(room)
            print(f" User {user_id} left {room}")
        
        @self.socketio.on('initiate_key_exchange')
        def handle_initiate_key_exchange(data):
            from flask import session
            user_id = session.get('user_id') or data.get('user_id')
            
            if not user_id:
                 emit('error', {'message': 'Missing user_id'})
                 return
            
            conversation_id = data.get('conversation_id')
            partner_user_id = data.get('partner_user_id')
            
            if not all([user_id, conversation_id, partner_user_id]):
                emit('error', {'message': 'Missing required fields'})
                return
            
            # Tạo và mã hóa AES key
            result = KeyManagementService.initiate_key_exchange(
                conversation_id, 
                user_id, 
                partner_user_id
            )
            
            if not result:
                emit('error', {'message': 'Failed to create session key'})
                return
            
            # Gửi encrypted key cho partner qua WebSocket
            partner_sid = redis_client.hget('online_users', str(partner_user_id))
            
            if partner_sid:
                self.socketio.emit('receive_encrypted_key', {
                    'conversation_id': conversation_id,
                    'encrypted_aes_key': result['encrypted_aes_key'],
                    'from_user_id': user_id
                }, room=partner_sid)
            
            # Confirm cho initiator
            emit('key_exchange_initiated', {
                'conversation_id': conversation_id,
                'aes_key': result['aes_key_plain']
            })
        
        @self.socketio.on('accept_encrypted_key')
        def handle_accept_encrypted_key(data):
            from flask import session
            user_id = session.get('user_id') or data.get('user_id')

            if not user_id:
                 emit('error', {'message': 'Missing user_id'})
                 return
            
            conversation_id = data.get('conversation_id')
            encrypted_key = data.get('encrypted_aes_key')
            
            if not all([user_id, conversation_id, encrypted_key]):
                emit('error', {'message': 'Missing required fields'})
                return
            
            # Giải mã AES key
            aes_key = KeyManagementService.accept_key_exchange(
                encrypted_key, 
                user_id, 
                conversation_id
            )
            
            if not aes_key:
                emit('error', {'message': 'Failed to decrypt AES key'})
                return
            
            # Trả AES key về cho user
            emit('key_exchange_completed', {
                'conversation_id': conversation_id,
                'aes_key': aes_key
            })
            
            # Thông báo cho partner
            room = f"conversation_{conversation_id}"
            emit('partner_key_accepted', {
                'conversation_id': conversation_id,
                'user_id': user_id
            }, room=room, include_self=False)

        
        @self.socketio.on('send_message')
        def handle_send_message(data):
            """
            User gửi tin nhắn (dạng plaintext)
            Tự động xử lý pending nếu receiver chưa có public key
            """
            from flask import session
            from flask import request
            
            sender_id = session.get('user_id') or data.get('user_id') 
            plain_text = data.get('plain_text', '').strip()
            partner_id = data.get('partner_id')
            
            if not all([sender_id, partner_id, plain_text]):
                emit('error', {'message': 'Thiếu thông tin người gửi/nhận/nội dung.'})
                return

            # Xử lý logic mã hóa/pending queue
            success, result_data = ChatManager.send_encrypted_message(
                sender_id=sender_id,
                partner_id=partner_id,
                plain_text_message=plain_text
            )

            if not success:
                emit('error', {'message': result_data}) 
                return

            # KIỂM TRA TRẠNG THÁI: PENDING HAY SENT
            status = result_data.get('status', 'sent')
            
            if status == 'pending':
                # TIN NHẮN ĐANG CHỜ → Chỉ thông báo cho sender
                emit('message_queued', {
                    'pending_id': result_data['pending_id'],
                    'conversation_id': result_data['conversation_id'],
                    'message': result_data['message'],
                    'plain_text': plain_text
                }, room=request.sid)
                print(f" [PENDING] Message queued from {sender_id} to {partner_id}")
                return
            
            # TIN NHẮN ĐÃ GỬI THÀNH CÔNG → Emit qua WebSocket
            final_conversation_id = result_data['conversation_id']
            room = f"conversation_{final_conversation_id}"
            
            message_to_emit = {
                'conversation_id': final_conversation_id,
                'sender_id': sender_id,
                'message_id': result_data.get('message_id'),  #  Thêm message_id
                'encrypted_content': result_data['encrypted_content'],
                'nonce_tag_data': result_data['nonce_tag_data'],
                'message_hash': result_data['message_hash'],
                'sent_at': datetime.now().isoformat()
            }
            
            #  Emit cho toàn bộ room (bao gồm cả sender để đồng bộ nhiều tab)
            self.socketio.emit('new_message', message_to_emit, room=room) 
            print(f" [SENT] Message from {sender_id} to {partner_id} in room {room}")
        
        #  THÊM HANDLER CHO MARK AS READ
        @self.socketio.on('mark_as_read')
        def handle_mark_as_read(data):
            """Đánh dấu tin nhắn là đã đọc"""
            from flask import session
            from backend.Config.MessageModel import MessageModel
            from backend.Config.ConversationModel import ConversationModel
            from flask import request
            
            user_id = session.get('user_id') or data.get('user_id')
            conversation_id = data.get('conversation_id')
            
            if not user_id or not conversation_id:
                return
            
            try:
                # Cập nhật database
                MessageModel.mark_conversation_as_read(conversation_id, user_id)
                
                print(f" [READ] User {user_id} marked conv {conversation_id} as read")
                
                # Lấy thông tin conversation để tìm partner
                conv = ConversationModel.get_conversation_by_id(conversation_id)
                if conv:
                    partner_id = conv['user1_id'] if conv['user2_id'] == user_id else conv['user2_id']
                    print(f" [READ] Partner is user {partner_id}")
                    
                    # Emit cho partner (người gửi tin nhắn) để cập nhật ✓✓
                    partner_socket = self.redis_client.hget('online_users', str(partner_id))
                    print(f" [READ] Partner socket: {partner_socket}")
                    
                    if partner_socket:
                        emit('marked_as_read', {
                            'conversation_id': conversation_id,
                            'reader_id': user_id
                        }, room=partner_socket)
                        print(f" Sent marked_as_read to user {partner_id} (socket {partner_socket})")
                    else:
                        print(f" Partner {partner_id} is OFFLINE or no socket found")
                
                # Emit xác nhận cho chính người đọc
                emit('marked_as_read', {
                    'conversation_id': conversation_id,
                    'reader_id': user_id
                }, room=request.sid)
                
            except Exception as e:
                print(f" [ERROR] mark_as_read: {e}")
        
        @self.socketio.on('message_recalled')
        def handle_message_recalled(data):
            """Xử lý thu hồi tin nhắn"""
            from flask import session
            from backend.Config.ConversationModel import ConversationModel
            from flask import request
            
            message_id = data.get('message_id')
            conversation_id = data.get('conversation_id')
            user_id = session.get('user_id')
            
            if not all([message_id, conversation_id, user_id]):
                return
            
            try:
                # Lấy thông tin conversation để tìm partner
                conv = ConversationModel.get_conversation_by_id(conversation_id)
                if conv:
                    partner_id = conv['user1_id'] if conv['user2_id'] == user_id else conv['user2_id']
                    
                    # Emit cho partner để xóa tin nhắn
                    partner_socket = self.redis_client.get_socket_id(partner_id)
                    if partner_socket:
                        emit('message_recalled', {
                            'message_id': message_id,
                            'conversation_id': conversation_id
                        }, room=partner_socket)
                        print(f"↩ Sent message_recalled to user {partner_id}")
                
            except Exception as e:
                print(f" [ERROR] handle_message_recalled: {e}")
        
        @self.socketio.on('typing')
        def handle_typing(data):
            from flask import session
            user_id = session.get('user_id') or data.get('user_id')
            
            if not user_id:
                return
            
            conversation_id = data.get('conversation_id')
            is_typing = data.get('is_typing', True)
            
            if not all([user_id, conversation_id]):
                return
            
            room = f"conversation_{conversation_id}"
            emit('user_typing', {
                'user_id': user_id,
                'is_typing': is_typing
            }, room=room, include_self=False)
        
        @self.socketio.on('get_online_status')
        def handle_get_online_status(data):
            """Kiểm tra user có online không"""
            from flask import request
            user_ids = data.get('user_ids', [])
            
            online_status = {}
            for uid in user_ids:
                is_online = redis_client.hexists('online_users', str(uid))
                online_status[uid] = is_online
            
            print(f"📡 Sending online status for {len(user_ids)} users: {online_status}")
            
            emit('online_status_response', {'online_status': online_status}, room=request.sid)