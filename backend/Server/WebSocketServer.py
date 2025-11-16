from flask import Flask, session
from flask_socketio import SocketIO
from flask_cors import CORS
from backend.Server.WebSocketHandler import WebSocketHandler


class WebSocketServer:
    """
    Main WebSocket Server
    """
    
    def __init__(self, app=None):
        self.app = app or Flask(__name__)
        self.configure_app()
        self.socketio = SocketIO(
            self.app,
            cors_allowed_origins="*",  # TODO: Restrict in production
            async_mode='threading',
            logger=True,
            engineio_logger=True
        )
        
        # Initialize handlers
        self.handler = WebSocketHandler(self.socketio)
        
        print(" WebSocket Server initialized")
    
    def configure_app(self):
        """Cấu hình Flask app"""
        self.app.config['SECRET_KEY'] = 'your-secret-key-here'  # TODO: Move to config
        
        # Enable CORS
        CORS(self.app, resources={
            r"/*": {
                "origins": "*",  # TODO: Restrict in production
                "supports_credentials": True
            }
        })
        
        # Session config
        self.app.config['SESSION_TYPE'] = 'filesystem'
    
    def run(self, host='0.0.0.0', port=5000, debug=True):
        """Chạy WebSocket server với tùy chọn tắt reloader."""
        print(f" Starting WebSocket server on {host}:{port}")
        self.socketio.run(
            self.app,
            host=host,
            port=port,
            debug=debug,
            # CHỈNH SỬA TẠI ĐÂY: Thêm use_reloader=False vào socketio.run
            use_reloader=False, 
            allow_unsafe_werkzeug=True  # Chỉ cho development
        )


# Factory function để tích hợp với Flask app có sẵn
def create_socketio(app):
    """
    Tạo SocketIO instance và attach vào Flask app có sẵn
    
    Usage:
        app = Flask(__name__)
        socketio = create_socketio(app)
        socketio.run(app)
    """
    socketio = SocketIO(
        app,
        cors_allowed_origins="*",
        async_mode='threading',
        logger=True,
        engineio_logger=True
    )
    
    # Initialize handlers
    handler = WebSocketHandler(socketio)
    
    return socketio


# Standalone usage
if __name__ == '__main__':
    server = WebSocketServer()
    server.run(host='0.0.0.0', port=5000, debug=True)