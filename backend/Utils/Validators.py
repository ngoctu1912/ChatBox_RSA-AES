import re

def validate_email(email):
    """
    Kiểm tra định dạng email hợp lệ
    Returns: (is_valid, error_message)
    """
    if not email or email.strip() == '':
        return False, "Email không được để trống"
    
    email = email.strip()
    email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    
    if not re.match(email_pattern, email):
        return False, "Email không đúng định dạng"
    
    if len(email) > 100:
        return False, "Email quá dài (tối đa 100 ký tự)"
    
    return True, ""

def validate_password(password):
    """
    Kiểm tra mật khẩu hợp lệ
    Returns: (is_valid, error_message)
    """
    if not password or password.strip() == '':
        return False, "Mật khẩu không được để trống"
    
    if len(password) < 6:
        return False, "Mật khẩu phải có ít nhất 6 ký tự"
    
    if len(password) > 255:
        return False, "Mật khẩu quá dài (tối đa 255 ký tự)"
    
    return True, ""

def validate_fullname(fullname):
    """
    Kiểm tra tên đầy đủ hợp lệ
    Returns: (is_valid, error_message)
    """
    if not fullname or fullname.strip() == '':
        return False, "Tên đầy đủ không được để trống"
    
    fullname = fullname.strip()
    
    if len(fullname) < 2:
        return False, "Tên đầy đủ phải có ít nhất 2 ký tự"
    
    if len(fullname) > 100:
        return False, "Tên đầy đủ quá dài (tối đa 100 ký tự)"
    
    return True, ""

def validate_username(username):
    """
    Kiểm tra username hợp lệ (nếu có)
    Returns: (is_valid, error_message)
    """
    if username and username.strip() != '':
        username = username.strip()
        
        if len(username) < 3:
            return False, "Username phải có ít nhất 3 ký tự"
        
        if len(username) > 50:
            return False, "Username quá dài (tối đa 50 ký tự)"
        
        # Chỉ cho phép chữ cái, số, gạch dưới
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return False, "Username chỉ được chứa chữ cái, số và gạch dưới"
    
    return True, ""