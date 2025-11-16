import tkinter as tk
from tkinter import ttk, messagebox
from backend.Config.UserModel import UserModel


class SettingsDialog(tk.Toplevel):
    """Popup cài đặt với các tùy chọn: Đổi mật khẩu, Thông tin cá nhân"""
    
    def __init__(self, parent, user_data):
        super().__init__(parent)
        self.user_data = user_data
        self.user_id = user_data['user_id']
        
        # Cấu hình cửa sổ
        self.title("Cài đặt")
        self.geometry("500x550")
        self.resizable(False, False)
        self.configure(bg="#F5F5F5")
        
        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.winfo_screenheight() // 2) - (550 // 2)
        self.geometry(f"500x550+{x}+{y}")
        
        # Header
        header = tk.Frame(self, bg="#4CAF50", height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text="⚙️ Cài đặt",
            font=("Inter", 18, "bold"),
            bg="#4CAF50",
            fg="white"
        ).pack(pady=15)
        
        # Notebook (Tabs)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Tab 1: Đổi mật khẩu
        self.password_frame = tk.Frame(self.notebook, bg="#FFFFFF")
        self.notebook.add(self.password_frame, text="Đổi mật khẩu")
        self.create_password_tab()
        
        # Tab 2: Thông tin cá nhân
        self.profile_frame = tk.Frame(self.notebook, bg="#FFFFFF")
        self.notebook.add(self.profile_frame, text="Thông tin cá nhân")
        self.create_profile_tab()
    
    def create_password_tab(self):
        """Tab đổi mật khẩu"""
        container = tk.Frame(self.password_frame, bg="#FFFFFF")
        container.pack(fill="both", expand=True, padx=30, pady=30)
        
        tk.Label(
            container,
            text="Đổi mật khẩu",
            font=("Inter", 14, "bold"),
            bg="#FFFFFF"
        ).pack(anchor="w", pady=(0, 20))
        
        # Mật khẩu hiện tại
        tk.Label(container, text="Mật khẩu hiện tại:", font=("Inter", 10), bg="#FFFFFF").pack(anchor="w", pady=(5, 0))
        self.current_password_entry = tk.Entry(container, show="•", font=("Inter", 11), relief="solid", borderwidth=1)
        self.current_password_entry.pack(fill="x", ipady=6, pady=(5, 15))
        
        # Mật khẩu mới
        tk.Label(container, text="Mật khẩu mới:", font=("Inter", 10), bg="#FFFFFF").pack(anchor="w", pady=(5, 0))
        self.new_password_entry = tk.Entry(container, show="•", font=("Inter", 11), relief="solid", borderwidth=1)
        self.new_password_entry.pack(fill="x", ipady=6, pady=(5, 15))
        
        # Xác nhận mật khẩu mới
        tk.Label(container, text="Xác nhận mật khẩu mới:", font=("Inter", 10), bg="#FFFFFF").pack(anchor="w", pady=(5, 0))
        self.confirm_password_entry = tk.Entry(container, show="•", font=("Inter", 11), relief="solid", borderwidth=1)
        self.confirm_password_entry.pack(fill="x", ipady=6, pady=(5, 20))
        
        # Nút Lưu
        tk.Button(
            container,
            text="Lưu thay đổi",
            font=("Inter", 11, "bold"),
            bg="#4CAF50",
            fg="white",
            relief="flat",
            cursor="hand2",
            command=self.change_password
        ).pack(fill="x", ipady=8)
    
    def create_profile_tab(self):
        """Tab thông tin cá nhân (chỉ xem)"""
        container = tk.Frame(self.profile_frame, bg="#FFFFFF")
        container.pack(fill="both", expand=True, padx=30, pady=30)
        
        tk.Label(
            container,
            text="Thông tin cá nhân",
            font=("Inter", 14, "bold"),
            bg="#FFFFFF"
        ).pack(anchor="w", pady=(0, 20))
        
        # Họ tên (read-only)
        tk.Label(container, text="Họ và tên:", font=("Inter", 10), bg="#FFFFFF").pack(anchor="w", pady=(5, 0))
        fullname_entry = tk.Entry(container, font=("Inter", 11), relief="solid", borderwidth=1, fg="#333333")
        fullname_entry.insert(0, self.user_data.get('full_name', ''))
        fullname_entry.config(state="readonly")
        fullname_entry.pack(fill="x", ipady=6, pady=(5, 12))
        
        # Email (read-only)
        tk.Label(container, text="Email:", font=("Inter", 10), bg="#FFFFFF").pack(anchor="w", pady=(5, 0))
        email_entry = tk.Entry(container, font=("Inter", 11), relief="solid", borderwidth=1, fg="#333333")
        email_entry.insert(0, self.user_data.get('email', ''))
        email_entry.config(state="readonly")
        email_entry.pack(fill="x", ipady=6, pady=(5, 12))
        
        # Phòng ban (read-only)
        tk.Label(container, text="Phòng ban:", font=("Inter", 10), bg="#FFFFFF").pack(anchor="w", pady=(5, 0))
        department_entry = tk.Entry(container, font=("Inter", 11), relief="solid", borderwidth=1, fg="#333333")
        department_entry.insert(0, self.user_data.get('department', 'IT'))
        department_entry.config(state="readonly")
        department_entry.pack(fill="x", ipady=6, pady=(5, 12))
        
        # Chức vụ/Vai trò (read-only)
        role_text = {
            'admin': 'Quản trị viên',
            'manager': 'Quản lý',
            'staff': 'Nhân viên'
        }.get(self.user_data.get('role', 'staff'), 'Nhân viên')
        
        tk.Label(container, text="Chức vụ:", font=("Inter", 10), bg="#FFFFFF").pack(anchor="w", pady=(5, 0))
        role_entry = tk.Entry(container, font=("Inter", 11), relief="solid", borderwidth=1, fg="#333333")
        role_entry.insert(0, role_text)
        role_entry.config(state="readonly")
        role_entry.pack(fill="x", ipady=6, pady=(5, 20))
    
    def change_password(self):
        """Xử lý đổi mật khẩu"""
        current_password = self.current_password_entry.get().strip()
        new_password = self.new_password_entry.get().strip()
        confirm_password = self.confirm_password_entry.get().strip()
        
        # Validation
        if not current_password or not new_password or not confirm_password:
            messagebox.showerror("Lỗi", "Vui lòng điền đầy đủ thông tin!")
            return
        
        if new_password != confirm_password:
            messagebox.showerror("Lỗi", "Mật khẩu mới và xác nhận không khớp!")
            return
        
        if len(new_password) < 6:
            messagebox.showerror("Lỗi", "Mật khẩu mới phải có ít nhất 6 ký tự!")
            return
        
        # Xác thực mật khẩu hiện tại (dùng email thay vì username)
        email = self.user_data.get('email')
        success, message, user_data = UserModel.verify_password(email, current_password)
        
        if not success:
            messagebox.showerror("Lỗi", "Mật khẩu hiện tại không đúng!")
            return
        
        # Cập nhật mật khẩu mới
        try:
            success = UserModel.update_password_by_id(self.user_id, new_password)
            if success:
                messagebox.showinfo("Thành công", "Đổi mật khẩu thành công!")
                self.current_password_entry.delete(0, tk.END)
                self.new_password_entry.delete(0, tk.END)
                self.confirm_password_entry.delete(0, tk.END)
            else:
                messagebox.showerror("Lỗi", "Không thể cập nhật mật khẩu!")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi cập nhật: {str(e)}")
    
    def update_profile(self):
        """Xử lý cập nhật thông tin cá nhân"""
        full_name = self.fullname_entry.get().strip()
        email = self.email_entry.get().strip()
        
        # Validation
        if not full_name:
            messagebox.showerror("Lỗi", "Họ tên không được để trống!")
            return
        
        if not email:
            messagebox.showerror("Lỗi", "Email không được để trống!")
            return
        
        # Validate email format
        if "@" not in email or "." not in email:
            messagebox.showerror("Lỗi", "Email không hợp lệ!")
            return
        
        # Cập nhật database
        try:
            success = UserModel.update_profile(self.user_id, full_name, email)
            if success:
                self.user_data['full_name'] = full_name
                self.user_data['email'] = email
                messagebox.showinfo("Thành công", "Cập nhật thông tin thành công!")
            else:
                messagebox.showerror("Lỗi", "Không thể cập nhật thông tin!")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi cập nhật: {str(e)}")
