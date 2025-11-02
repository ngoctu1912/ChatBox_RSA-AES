import jwt
from functools import wraps
from flask import request
from flask_socketio import disconnect
from backend.Config.ConnectDB import connect_to_database


class WebSocketAuth:
    """
    Middleware xác thực WebSocket connections
    """
    
    # Thay bằng secret key của bạn
    SECRET_KEY = "your-secret-key-here"  # TODO: Move to config
    
    @staticmethod
    def verify_token(token: str):
        """
        Verify JWT token
        
        Returns:
            dict: User data hoặc None
        """
        try:
            # Decode JWT
            payload = jwt.decode(token, WebSocketAuth.SECRET_KEY, algorithms=['HS256'])
            user_id = payload.get('user_id')
            
            if not user_id:
                return None
            
            # Verify user exists in DB
            conn, cursor = connect_to_database()
            query = "SELECT user_id, username, email FROM users WHERE user_id = %s"
            cursor.execute(query, (user_id,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            
            return user
            
        except jwt.ExpiredSignatureError:
            print("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            print(f"Invalid token: {e}")
            return None
        except Exception as e:
            print(f"Error verifying token: {e}")
            return None
    
    @staticmethod
    def authenticate_socket():
        """
        Decorator để authenticate WebSocket connection
        
        Usage:
            @socketio.on('connect')
            @WebSocketAuth.authenticate_socket()
            def handle_connect(auth):
                pass
        """
        def decorator(f):
            @wraps(f)
            def wrapped(*args, **kwargs):
                # Lấy token từ auth data
                auth = request.args.get('token') or (
                    request.headers.get('Authorization', '').replace('Bearer ', '')
                )
                
                if not auth:
                    print("❌ No token provided")
                    disconnect()
                    return False
                
                # Verify token
                user = WebSocketAuth.verify_token(auth)
                
                if not user:
                    print("❌ Invalid token")
                    disconnect()
                    return False
                
                # Thêm user vào kwargs
                kwargs['current_user'] = user
                return f(*args, **kwargs)
            
            return wrapped
        return decorator
    
    @staticmethod
    def require_auth(f):
        """
        Decorator đơn giản hơn cho các event handlers
        
        Usage:
            @socketio.on('send_message')
            @WebSocketAuth.require_auth
            def handle_message(data, current_user):
                pass
        """
        @wraps(f)
        def wrapped(*args, **kwargs):
            # Lấy token từ session hoặc request
            from flask import session
            user_id = session.get('user_id')
            
            if not user_id:
                return {'error': 'Unauthorized'}, 401
            
            # Lấy thông tin user
            conn, cursor = connect_to_database()
            query = "SELECT user_id, username, email FROM users WHERE user_id = %s"
            cursor.execute(query, (user_id,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not user:
                return {'error': 'User not found'}, 404
            
            # Inject user vào function
            kwargs['current_user'] = user
            return f(*args, **kwargs)
        
        return wrapped


class RateLimiter:
    """
    Rate limiting cho WebSocket events
    """
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    def check_rate_limit(self, user_id: int, action: str, limit: int = 10, window: int = 60):
        """
        Kiểm tra rate limit
        
        Args:
            user_id: ID của user
            action: Tên action (vd: 'send_message')
            limit: Số lượng requests tối đa
            window: Thời gian window (seconds)
            
        Returns:
            bool: True nếu còn trong limit, False nếu vượt quá
        """
        try:
            key = f"rate_limit:{user_id}:{action}"
            
            # Tăng counter
            current = self.redis.get(key)
            if current is None:
                self.redis.set(key, 1, expire=window)
                return True
            
            if int(current) >= limit:
                return False
            
            # Increment
            self.redis.client.incr(key)
            return True
            
        except Exception as e:
            print(f"Rate limit error: {e}")
            # Nếu Redis lỗi, cho phép request
            return True