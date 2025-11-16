from backend.Config.ConnectDB import connect_to_database
import bcrypt
from datetime import datetime


class UserModel:
    @staticmethod
    def get_user_by_email(email):
        try:
            conn, cursor = connect_to_database()
            query = "SELECT * FROM users WHERE email = %s"
            cursor.execute(query, (email,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            return user
        except Exception as e:
            print(f"Error get_user_by_email: {e}")
            return None

    @staticmethod
    def get_user_by_id(user_id):
        try:
            conn, cursor = connect_to_database()
            query = "SELECT * FROM users WHERE user_id = %s"
            cursor.execute(query, (user_id,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            return user
        except Exception as e:
            print(f"Error get_user_by_id: {e}")
            return None

    @staticmethod
    def get_all_users_except(user_id):
        try:
            conn, cursor = connect_to_database()
            query = """
                SELECT user_id, email, full_name, is_online, last_seen
                FROM users WHERE user_id != %s ORDER BY full_name ASC
            """
            cursor.execute(query, (user_id,))
            users = cursor.fetchall()
            cursor.close()
            conn.close()
            return users
        except Exception as e:
            print(f"Error get_all_users_except: {e}")
            return []

    @staticmethod
    def create_user(email, full_name, password):
        try:
            conn, cursor = connect_to_database()

            if UserModel.get_user_by_email(email):
                return False, "Email đã được sử dụng", None

            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            query = """
                INSERT INTO users (email, full_name, password_hash, is_online, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(query, (email, full_name, password_hash, False, datetime.now()))
            conn.commit()
            user_id = cursor.lastrowid
            cursor.close()
            conn.close()
            return True, "Đăng ký thành công", user_id

        except Exception as e:
            print(f"Error create_user: {e}")
            return False, f"Lỗi tạo tài khoản: {str(e)}", None

    @staticmethod
    def verify_password(email, password):
        try:
            user = UserModel.get_user_by_email(email)
            if not user:
                return False, "Email không tồn tại", None
            if bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                user_data = {k: v for k, v in user.items() if k != 'password_hash'}
                return True, "Đăng nhập thành công", user_data
            return False, "Mật khẩu không chính xác", None
        except Exception as e:
            print(f"Error verify_password: {e}")
            return False, f"Lỗi xác thực: {str(e)}", None

    @staticmethod
    def update_online_status(user_id, is_online):
        """Cập nhật trạng thái online. Chỉ cập nhật last_seen khi OFFLINE."""
        try:
            conn, cursor = connect_to_database()
            
            if is_online:
                # Chỉ cập nhật is_online khi user online
                query = "UPDATE users SET is_online = %s WHERE user_id = %s"
                cursor.execute(query, (True, user_id))
            else:
                # Cập nhật is_online và last_seen khi user offline
                query = "UPDATE users SET is_online = %s, last_seen = %s WHERE user_id = %s"
                cursor.execute(query, (False, datetime.now(), user_id))
                
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Error update_online_status: {e}")
            return False

    @staticmethod
    def update_password(email, new_password):
        try:
            conn, cursor = connect_to_database()
            user = UserModel.get_user_by_email(email)
            if not user:
                return False, "Email không tồn tại"
            password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            query = "UPDATE users SET password_hash = %s, updated_at = %s WHERE email = %s"
            cursor.execute(query, (password_hash, datetime.now(), email))
            conn.commit()
            cursor.close()
            conn.close()
            return True, "Đổi mật khẩu thành công"
        except Exception as e:
            print(f"Error update_password: {e}")
            return False, f"Lỗi đổi mật khẩu: {str(e)}"
    
    @staticmethod
    def update_password_by_id(user_id, new_password):
        """Cập nhật mật khẩu theo user_id"""
        try:
            conn, cursor = connect_to_database()
            password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            query = "UPDATE users SET password_hash = %s, updated_at = %s WHERE user_id = %s"
            cursor.execute(query, (password_hash, datetime.now(), user_id))
            conn.commit()
            affected_rows = cursor.rowcount
            cursor.close()
            conn.close()
            return affected_rows > 0
        except Exception as e:
            print(f"Error update_password_by_id: {e}")
            return False
    
    @staticmethod
    def update_profile(user_id, full_name, email):
        """Cập nhật thông tin cá nhân (full_name, email)"""
        try:
            conn, cursor = connect_to_database()
            query = "UPDATE users SET full_name = %s, email = %s, updated_at = %s WHERE user_id = %s"
            cursor.execute(query, (full_name, email, datetime.now(), user_id))
            conn.commit()
            affected_rows = cursor.rowcount
            cursor.close()
            conn.close()
            return affected_rows > 0
        except Exception as e:
            print(f"Error update_profile: {e}")
            return False