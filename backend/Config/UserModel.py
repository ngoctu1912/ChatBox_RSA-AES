# from backend.Config.ConnectDB import connect_to_database
# import bcrypt
# from datetime import datetime
# from cryptography.hazmat.primitives.asymmetric import rsa
# from cryptography.hazmat.primitives import serialization


# class UserModel:
#     @staticmethod
#     def get_user_by_email(email):
#         try:
#             conn, cursor = connect_to_database()
#             query = "SELECT * FROM users WHERE email = %s"
#             cursor.execute(query, (email,))
#             user = cursor.fetchone()
#             cursor.close()
#             conn.close()
#             return user
#         except Exception as e:
#             print(f"Error get_user_by_email: {e}")
#             return None

#     @staticmethod
#     def get_user_by_id(user_id):
#         try:
#             conn, cursor = connect_to_database()
#             query = "SELECT * FROM users WHERE user_id = %s"
#             cursor.execute(query, (user_id,))
#             user = cursor.fetchone()
#             cursor.close()
#             conn.close()
#             return user
#         except Exception as e:
#             print(f"Error get_user_by_id: {e}")
#             return None

#     @staticmethod
#     def get_all_users_except(user_id):
#         try:
#             conn, cursor = connect_to_database()
#             query = """
#                 SELECT user_id, email, full_name, is_online, last_seen
#                 FROM users WHERE user_id != %s ORDER BY full_name ASC
#             """
#             cursor.execute(query, (user_id,))
#             users = cursor.fetchall()
#             cursor.close()
#             conn.close()
#             return users
#         except Exception as e:
#             print(f"Error get_all_users_except: {e}")
#             return []

#     @staticmethod
#     def create_user(email, full_name, password):
#         try:
#             conn, cursor = connect_to_database()

#             # Kiểm tra email trùng
#             if UserModel.get_user_by_email(email):
#                 return False, "Email đã được sử dụng", None

#             # Mã hóa mật khẩu
#             password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

#             # Thêm người dùng mới
#             query = """
#                 INSERT INTO users (email, full_name, password_hash, is_online, created_at)
#                 VALUES (%s, %s, %s, %s, %s)
#             """
#             cursor.execute(query, (email, full_name, password_hash, False, datetime.now()))
#             conn.commit()
#             user_id = cursor.lastrowid
#             cursor.close()
#             conn.close()
#             return True, "Đăng ký thành công", user_id

#         except Exception as e:
#             print(f"Error create_user: {e}")
#             return False, f"Lỗi tạo tài khoản: {str(e)}", None

#     @staticmethod
#     def verify_password(email, password):
#         try:
#             user = UserModel.get_user_by_email(email)
#             if not user:
#                 return False, "Email không tồn tại", None
#             if bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
#                 user_data = {k: v for k, v in user.items() if k != 'password_hash'}
#                 return True, "Đăng nhập thành công", user_data
#             return False, "Mật khẩu không chính xác", None
#         except Exception as e:
#             print(f"Error verify_password: {e}")
#             return False, f"Lỗi xác thực: {str(e)}", None

#     @staticmethod
#     def update_online_status(user_id, is_online):
#         try:
#             conn, cursor = connect_to_database()
#             query = "UPDATE users SET is_online = %s, last_seen = %s WHERE user_id = %s"
#             cursor.execute(query, (is_online, datetime.now(), user_id))
#             conn.commit()
#             cursor.close()
#             conn.close()
#             return True
#         except Exception as e:
#             print(f"Error update_online_status: {e}")
#             return False

#     @staticmethod
#     def update_password(email, new_password):
#         try:
#             conn, cursor = connect_to_database()
#             user = UserModel.get_user_by_email(email)
#             if not user:
#                 return False, "Email không tồn tại"
#             password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
#             query = "UPDATE users SET password_hash = %s, updated_at = %s WHERE email = %s"
#             cursor.execute(query, (password_hash, datetime.now(), email))
#             conn.commit()
#             cursor.close()
#             conn.close()
#             return True, "Đổi mật khẩu thành công"
#         except Exception as e:
#             print(f"Error update_password: {e}")
#             return False, f"Lỗi đổi mật khẩu: {str(e)}"

#     @staticmethod
#     def get_public_key(user_id):
#         """
#         Lấy khóa công khai RSA mới nhất của user
#         """
#         try:
#             conn, cursor = connect_to_database()
#             query = """
#                 SELECT public_key FROM rsa_keys 
#                 WHERE user_id = %s 
#                 ORDER BY created_at DESC 
#                 LIMIT 1
#             """
#             cursor.execute(query, (user_id,))
#             key = cursor.fetchone()
#             cursor.close()
#             conn.close()
#             return key['public_key'] if key else None
#         except Exception as e:
#             print(f"Error get_public_key: {e}")
#             return None

#     @staticmethod
#     def create_rsa_key(user_id):
#         """
#         Sinh cặp khóa RSA và lưu vào rsa_keys
#         """
#         try:
#             private_key = rsa.generate_private_key(
#                 public_exponent=65537,
#                 key_size=2048
#             )
#             public_key = private_key.public_key()

#             pem_private = private_key.private_bytes(
#                 encoding=serialization.Encoding.PEM,
#                 format=serialization.PrivateFormat.PKCS8,
#                 encryption_algorithm=serialization.NoEncryption()
#             ).decode('utf-8')

#             pem_public = public_key.public_bytes(
#                 encoding=serialization.Encoding.PEM,
#                 format=serialization.PublicFormat.SubjectPublicKeyInfo
#             ).decode('utf-8')

#             conn, cursor = connect_to_database()
#             query = """
#                 INSERT INTO rsa_keys (user_id, public_key, private_key_encrypted, key_size)
#                 VALUES (%s, %s, %s, %s)
#             """
#             cursor.execute(query, (user_id, pem_public, pem_private, 2048))
#             conn.commit()
#             cursor.close()
#             conn.close()
#             return True
#         except Exception as e:
#             print(f"Error create_rsa_key: {e}")
#             return False


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

            # Kiểm tra email trùng
            if UserModel.get_user_by_email(email):
                return False, "Email đã được sử dụng", None

            # Mã hóa mật khẩu
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            # Thêm người dùng mới
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
        try:
            conn, cursor = connect_to_database()
            query = "UPDATE users SET is_online = %s, last_seen = %s WHERE user_id = %s"
            cursor.execute(query, (is_online, datetime.now(), user_id))
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