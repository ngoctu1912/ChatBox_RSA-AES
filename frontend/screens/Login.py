import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from screens.ForgotPassword import ForgotPasswordWindow
import os
import re


class LoginPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg='white')
        self.controller = controller

        # ==== HEADER ====
        self.header = tk.Frame(self, bg='#0D99FF', height=80)
        self.header.pack(fill='x', side='top')
        self.header.pack_propagate(False)
        
        self.title_label_header = tk.Label(
            self.header, 
            text="Mã hóa tin nhắn",
            font=('Arial', 18),
            bg='#0D99FF',
            fg='#FFFFFF'
        )
        self.title_label_header.pack(side='left', padx=50, pady=15)

        # ==== CONTENT CHÍNH ====
        self.content = tk.Frame(self, bg='#FFFFFF')
        self.content.pack(fill='both', expand=True)
        
        self.main_content = tk.Frame(self.content, bg='#FFFFFF')
        self.main_content.pack(expand=True)
        
        # --- Khung trái: Hình ảnh ---
        self.canvas = tk.Canvas(self, bg='#FFFFFF', highlightthickness=0)
        self.canvas.place(x=50, y=150, width=500, height=420)

        image_path = os.path.join(
            os.path.dirname(__file__), "..", "assets", "images", "encryption_intro.jpg"
        )

        if os.path.exists(image_path):
            img = Image.open(image_path).resize((500, 420), Image.LANCZOS)
            self.photo = ImageTk.PhotoImage(img)
            self.canvas.create_image(0, 0, anchor='nw', image=self.photo)
        else:
            tk.Label(
                self.left_frame,
                text="[Không tìm thấy hình ảnh]",
                font=('Arial', 14),
                fg='gray',
                bg='#FFFFFF'
            ).pack(pady=180)

        # --- Khung phải: Form đăng nhập ---
        # ==== Container chính ====
        self.main_container = tk.Frame(self, bg='white')  
        self.main_container.place(x=600, y=150, width=600)

        # ==== Tiêu đề "Đăng Nhập" ====
        self.title_label = tk.Label(
            self.main_container,
            text="Đăng Nhập",
            font=('Arial', 28),
            bg='white',
            fg='black'
        )
        self.title_label.pack(pady=(0, 40))

        # ==== Frame cho form ====
        self.form_frame = tk.Frame(self.main_container, bg='white')
        self.form_frame.pack(pady=20)

        # ==== Email field ====
        self.create_input_field(
            self.form_frame,
            icon_name='user.png',
            placeholder='abc123@gmail.com',
            row=0,
            show_char='',
            is_password=False
        )

        # ==== Password field ====
        self.password_frame = self.create_input_field(
            self.form_frame,
            icon_name='lock.png',
            placeholder='Mật khẩu',
            row=1,
            show_char='•',
            is_password=True
        )
        self.password_frame.grid_configure(pady=(0, 8))

        # ==== Quên mật khẩu? ====
        self.forgot_password = tk.Label(
            self.form_frame,
            text="Quên mật khẩu?",
            font=('Arial', 11),
            bg='white',
            fg='#0D99FF',
            cursor='hand2'
        )
        self.forgot_password.grid(row=2, column=0, sticky='e', pady=(0, 2))
        self.forgot_password.bind('<Button-1>', lambda e: ForgotPasswordWindow(self, self.load_icon))

        # ==== Nút Đăng Nhập ====
        self.login_btn = tk.Button(
            self.form_frame,
            text="ĐĂNG NHẬP",
            font=('Arial', 14),
            bg='#0099FF',
            fg='white',
            relief='flat',
            padx=160,
            pady=8,
            cursor='hand2',
            borderwidth=0,
            command=self.on_login
        )
        self.login_btn.grid(row=3, column=0, pady=(40,25))

        # ==== Nút Tạo tài khoản ====
        self.register_btn = tk.Button(
            self.form_frame,
            text="Tạo tài khoản mới",
            font=('Arial', 12),
            bg='#47B821',
            fg='white',
            relief='flat',
            padx=80,
            pady=8,
            cursor='hand2',
            borderwidth=0,
            command=lambda: controller.show_frame("RegisterPage")
        )
        self.register_btn.grid(row=4, column=0, pady=10)

    # ======== Tải icon ========
    def load_icon(self, name, size=(22, 22)):
        path = os.path.join(os.path.dirname(__file__), "..", "assets", "icons", name)
        if os.path.exists(path):
            img = Image.open(path).resize(size, Image.LANCZOS)
            return ImageTk.PhotoImage(img)
        else:
            return None

    def create_input_field(self, parent, icon_name, placeholder, row, show_char=None, is_password=False):
        # Frame tổng 
        wrapper = tk.Frame(parent, bg='white')
        wrapper.grid(row=row, column=0, sticky='ew', pady=(0, 28))

        # Frame chứa icon + entry
        input_container = tk.Frame(wrapper, bg='white')
        input_container.pack(fill='x', pady=(0, 0))

        # Icon trái
        icon_img = self.load_icon(icon_name)
        if icon_img:
            icon_label = tk.Label(input_container, image=icon_img, bg='white')
            icon_label.image = icon_img
            icon_label.pack(side='left', padx=(0, 10))
        else:
            tk.Label(input_container, text='?', bg='white').pack(side='left', padx=(0, 10))

        # Entry
        entry = tk.Entry(
            input_container,
            font=('Arial', 12),
            bg='white',
            fg='gray',
            relief='flat',
            width=30,
            show=show_char if show_char else ''
        )
        entry.pack(side='left', fill='x', expand=True, ipady=5)
        entry.insert(0, placeholder)

        # Placeholder behaviour
        def on_focus_in(event):
            if entry.get() == placeholder:
                entry.delete(0, tk.END)
                entry.config(fg='black')
                separator.config(bg='#0099FF')  

        def on_focus_out(event):
            if entry.get() == '':
                entry.insert(0, placeholder)
                entry.config(fg='gray')
            separator.config(bg='#CCCCCC')  

        entry.bind('<FocusIn>', on_focus_in)
        entry.bind('<FocusOut>', on_focus_out)

        # Nếu là mật khẩu → thêm nút mắt
        if is_password:
            self.password_entry = entry
            self.password_visible = False

            self.eye_open = self.load_icon('openeye.png', (20, 20))
            self.eye_close = self.load_icon('closeeye.png', (20, 20))

            self.eye_btn = tk.Button(
                input_container,
                image=self.eye_close,
                bg='white',
                relief='flat',
                cursor='hand2',
                borderwidth=0,
                command=self.toggle_password_visibility
            )
            self.eye_btn.image = self.eye_close
            self.eye_btn.pack(side='left', padx=(5, 0))
        else:
            self.email_entry = entry

        # Đường kẻ dưới input
        separator = tk.Frame(wrapper, bg='#CCCCCC', height=1)
        separator.pack(fill='x', pady=(2, 0))

        return wrapper

    # ========= Hiển thị / ẩn mật khẩu ==========
    def toggle_password_visibility(self):
        if self.password_visible:
            self.password_entry.config(show='•')
            self.eye_btn.config(image=self.eye_close)
            self.password_visible = False
        else:
            self.password_entry.config(show='')
            self.eye_btn.config(image=self.eye_open)
            self.password_visible = True

    # ========= Xử lý sự kiện đăng nhập ==========
    def on_login(self):
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()

        # ===== Kiểm tra email =====
        if email == '' or email == 'abc123@gmail.com':
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập email!")
            return

        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_pattern, email):
            messagebox.showerror("Lỗi", "Email không đúng định dạng!")
            return

        # ===== Kiểm tra mật khẩu =====
        if password == '' or password == 'Mật khẩu':
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập mật khẩu!")
            return

        if len(password) < 6:
            messagebox.showerror("Lỗi", "Mật khẩu phải có ít nhất 6 ký tự!")
            return

        # ===== Thành công  =====
        messagebox.showinfo("Thành công", "Đăng nhập thành công!")

    