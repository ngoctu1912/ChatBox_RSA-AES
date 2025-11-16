# backend_server.py
import sys, os
# Thêm thư mục gốc vào PYTHONPATH để import backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

from backend.Server.WebSocketServer import WebSocketServer

if __name__ == '__main__':
    # Khởi tạo và chạy WebSocket Server
    server = WebSocketServer()
    try:
        # Server sẽ chạy trên port 5000 (mặc định)
        server.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        print(f" Lỗi khi khởi động Backend Server: {e}")