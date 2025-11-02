from backend.Config.UserModel import UserModel
from backend.Utils.Validators import (
    validate_email,
    validate_password,
    validate_fullname
)


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

        # ---- Gọi Model ----
        success, message, user_id = UserModel.create_user(
            email=email,
            full_name=full_name,
            password=password
        )

        if success:
            # Sinh cặp khóa RSA tự động
            rsa_success = UserModel.create_rsa_key(user_id)
            if not rsa_success:
                # Nếu lỗi sinh khóa, vẫn đăng ký thành công nhưng log cảnh báo
                print(f"Warning: Lỗi sinh RSA cho user {user_id}")

        return success, message, user_id

    # ------------------------------------------------------------------ #
    # ĐĂNG NHẬP
    # ------------------------------------------------------------------ #
    @staticmethod
    def login(email, password):
        """
        Returns: (success: bool, message: str, user_data: dict|None)
        """
        if not email or not password:
            return False, "Vui lòng nhập email và mật khẩu", None

        return UserModel.verify_password(email, password)

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
