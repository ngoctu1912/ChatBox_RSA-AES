from flask_socketio import emit, join_room, leave_room
from backend.Services.KeyManagementService import KeyManagementService
from backend.Services.SessionService import SessionService
from backend.Utils.RedisClient import redis_client
from backend.Config.ConnectDB import connect_to_database
from backend.Middleware.WebSocketAuth import RateLimiter
from datetime import datetime


class WebSocketHandler:
    """
    Xử lý tất cả WebSocket events
    """
    
    def __init__(self, socketio):
        self.socketio = socketio
        self.rate_limiter = RateLimiter(redis_client)
        self.register_handlers()
    
    def register_handlers(self):
        """Đăng ký tất cả event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect():
            """User kết nối WebSocket"""
            from flask import request, session
            user_id = session.get('user_id')
            
            if not user_id:
                print(" Unauthorized connection attempt")
                return False
            
            # Lưu socket ID vào Redis
            sid = request.sid
            redis_client.hset('online_users', str(user_id), sid)
            redis_client.sadd('active_sids', sid)
            
            print(f" User {user_id} connected with SID {sid}")
            
            # Thông báo online cho friends
            emit('user_online', {'user_id': user_id}, broadcast=True)
            return True
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """User ngắt kết nối"""
            from flask import request, session
            user_id = session.get('user_id')
            sid = request.sid
            
            if user_id:
                # Xóa khỏi online users
                redis_client.hdel('online_users', str(user_id))
                redis_client.srem('active_sids', sid)
                
                print(f" User {user_id} disconnected")
                
                # Thông báo offline
                emit('user_offline', {'user_id': user_id}, broadcast=True)
        
        @self.socketio.on('join_conversation')
        def handle_join_conversation(data):
            """User tham gia conversation room"""
            from flask import session
            user_id = session.get('user_id')
            conversation_id = data.get('conversation_id')
            
            if not user_id or not conversation_id:
                emit('error', {'message': 'Missing user_id or conversation_id'})
                return
            
            # Join room
            room = f"conversation_{conversation_id}"
            join_room(room)
            
            print(f"User {user_id} joined {room}")
            emit('joined_conversation', {
                'conversation_id': conversation_id,
                'user_id': user_id
            }, room=room)
        
        @self.socketio.on('leave_conversation')
        def handle_leave_conversation(data):
            """User rời conversation room"""
            from flask import session
            user_id = session.get('user_id')
            conversation_id = data.get('conversation_id')
            
            if not conversation_id:
                return
            
            room = f"conversation_{conversation_id}"
            leave_room(room)
            print(f"User {user_id} left {room}")
        
        @self.socketio.on('initiate_key_exchange')
        def handle_initiate_key_exchange(data):
            """
            User A bắt đầu key exchange
            
            Data: {
                'conversation_id': int,
                'partner_user_id': int
            }
            """
            from flask import session
            user_id = session.get('user_id')
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
                    'encrypted_aes_key': result['aes_key_encrypted'],
                    'from_user_id': user_id
                }, room=partner_sid)
            
            # Confirm cho initiator
            emit('key_exchange_initiated', {
                'conversation_id': conversation_id,
                'aes_key': result['aes_key_plain']  # Plain key cho initiator
            })
        
        @self.socketio.on('accept_encrypted_key')
        def handle_accept_encrypted_key(data):
            """
            User B nhận và giải mã AES key
            
            Data: {
                'conversation_id': int,
                'encrypted_aes_key': str
            }
            """
            from flask import session
            user_id = session.get('user_id')
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
            Gửi tin nhắn đã mã hóa
            
            Data: {
                'conversation_id': int,
                'encrypted_content': str,
                'iv': str (nếu dùng AES-CBC/GCM)
            }
            """
            from flask import session
            user_id = session.get('user_id')
            
            if not user_id:
                emit('error', {'message': 'Unauthorized'})
                return
            
            # Rate limiting
            if not self.rate_limiter.check_rate_limit(user_id, 'send_message', limit=20, window=60):
                emit('error', {'message': 'Rate limit exceeded'})
                return
            
            conversation_id = data.get('conversation_id')
            encrypted_content = data.get('encrypted_content')
            iv = data.get('iv')
            
            if not all([conversation_id, encrypted_content]):
                emit('error', {'message': 'Missing required fields'})
                return
            
            try:
                # Lưu message vào database
                conn, cursor = connect_to_database()
                query = """
                    INSERT INTO messages (conversation_id, sender_id, encrypted_content, iv, sent_at)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING message_id
                """
                cursor.execute(query, (
                    conversation_id, 
                    user_id, 
                    encrypted_content, 
                    iv,
                    datetime.now()
                ))
                message_id = cursor.fetchone()['message_id']
                conn.commit()
                cursor.close()
                conn.close()
                
                # Broadcast tin nhắn đến conversation room
                room = f"conversation_{conversation_id}"
                self.socketio.emit('new_message', {
                    'message_id': message_id,
                    'conversation_id': conversation_id,
                    'sender_id': user_id,
                    'encrypted_content': encrypted_content,
                    'iv': iv,
                    'sent_at': datetime.now().isoformat()
                }, room=room)
                
            except Exception as e:
                print(f"Error sending message: {e}")
                emit('error', {'message': 'Failed to send message'})
        
        @self.socketio.on('typing')
        def handle_typing(data):
            """User đang gõ"""
            from flask import session
            user_id = session.get('user_id')
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
            user_ids = data.get('user_ids', [])
            
            online_status = {}
            for uid in user_ids:
                is_online = redis_client.hexists('online_users', str(uid))
                online_status[uid] = is_online
            
            emit('online_status', online_status)