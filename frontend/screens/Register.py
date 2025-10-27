import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import os, re

class RegisterPage(tk.Frame):
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
        
        # Khung trái: Hình ảnh
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

        # Khung phải: Form đăng ký
        # ==== Container chính căn giữa ====
        self.main_container = tk.Frame(self, bg='white')  
        self.main_container.place(x=600, y=120, width=600)

        # ==== Tiêu đề "Đăng Ký" ====
        self.title_label = tk.Label(
            self.main_container,
            text="Đăng Ký",
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
            placeholder='Email',
            row=0,
            show_char='',
            is_password=False,
            field_name='email'
        )

        # ==== Full name field ====
        self.create_input_field(
            self.form_frame,
            icon_name='user.png',
            placeholder='Tên đầy đủ',
            row=1,
            show_char='',
            is_password=False,
            field_name='fullname'
        )

        # ==== Password field ====
        self.password_frame = self.create_input_field(
            self.form_frame,
            icon_name='lock.png',
            placeholder='Mật khẩu',
            row=2,
            show_char='•',
            is_password=True,
            field_name='password'
        )

        # ==== Confirm Password field ====
        self.confirm_password_frame = self.create_input_field(
            self.form_frame,
            icon_name='lock.png',
            placeholder='Xác nhận mật khẩu',
            row=3,
            show_char='•',
            is_password=True,
            field_name='confirm_password'
        )

        # ==== Nút Đăng Ký ====
        self.register_btn = tk.Button(
            self.form_frame,
            text="ĐĂNG KÝ",
            font=('Arial', 14),
            bg='#47B821',
            fg='white',
            relief='flat',
            padx=160,
            pady=8,
            cursor='hand2',
            borderwidth=0,
            command=self.on_register
        )
        self.register_btn.grid(row=4, column=0, pady=(40, 25))

        # ==== Bạn đã có tài khoản? Đăng nhập ====
        self.login_link_frame = tk.Frame(self.form_frame, bg='white')
        self.login_link_frame.grid(row=5, column=0, pady=10)

        self.login_text = tk.Label(
            self.login_link_frame,
            text="Bạn đã có tài khoản? ",
            font=('Arial', 11),
            bg='white',
            fg='black'
        )
        self.login_text.pack(side='left')

        self.login_link = tk.Label(
            self.login_link_frame,
            text="Đăng nhập",
            font=('Arial', 11),
            bg='white',
            fg='#0D99FF',
            cursor='hand2'
        )
        self.login_link.pack(side='left')
        self.login_link.bind('<Button-1>', lambda e: controller.show_frame("LoginPage"))

    # ======== Tải icon ========
    def load_icon(self, name, size=(22, 22)):
        path = os.path.join(os.path.dirname(__file__), "..", "assets", "icons", name)
        if os.path.exists(path):
            img = Image.open(path).resize(size, Image.LANCZOS)
            return ImageTk.PhotoImage(img)
        else:
            return None

    def create_input_field(self, parent, icon_name, placeholder, row, show_char=None, is_password=False, field_name=''):
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

        # Lưu entry vào attribute tương ứng
        if field_name == 'email':
            self.email_entry = entry
        elif field_name == 'fullname':
            self.fullname_entry = entry
        elif field_name == 'password':
            self.password_entry = entry
            self.password_visible = False
        elif field_name == 'confirm_password':
            self.confirm_password_entry = entry
            self.confirm_password_visible = False

        # Nếu là mật khẩu → thêm nút mắt
        if is_password:
            eye_open = self.load_icon('openeye.png', (20, 20))
            eye_close = self.load_icon('closeeye.png', (20, 20))

            if field_name == 'password':
                self.eye_open_pass = eye_open
                self.eye_close_pass = eye_close

                self.eye_btn_pass = tk.Button(
                    input_container,
                    image=eye_close,
                    bg='white',
                    relief='flat',
                    cursor='hand2',
                    borderwidth=0,
                    command=lambda: self.toggle_password_visibility('password')
                )
                self.eye_btn_pass.image = eye_close
                self.eye_btn_pass.pack(side='left', padx=(5, 0))
            elif field_name == 'confirm_password':
                self.eye_open_confirm = eye_open
                self.eye_close_confirm = eye_close

                self.eye_btn_confirm = tk.Button(
                    input_container,
                    image=eye_close,
                    bg='white',
                    relief='flat',
                    cursor='hand2',
                    borderwidth=0,
                    command=lambda: self.toggle_password_visibility('confirm_password')
                )
                self.eye_btn_confirm.image = eye_close
                self.eye_btn_confirm.pack(side='left', padx=(5, 0))

        # Đường kẻ dưới input
        separator = tk.Frame(wrapper, bg='#CCCCCC', height=1)
        separator.pack(fill='x', pady=(2, 0))

        return wrapper

    # =========== Hiển thị / ẩn mật khẩu ==========
    def toggle_password_visibility(self, field_type):
        if field_type == 'password':
            if self.password_visible:
                self.password_entry.config(show='•')
                self.eye_btn_pass.config(image=self.eye_close_pass)
                self.password_visible = False
            else:
                self.password_entry.config(show='')
                self.eye_btn_pass.config(image=self.eye_open_pass)
                self.password_visible = True
        elif field_type == 'confirm_password':
            if self.confirm_password_visible:
                self.confirm_password_entry.config(show='•')
                self.eye_btn_confirm.config(image=self.eye_close_confirm)
                self.confirm_password_visible = False
            else:
                self.confirm_password_entry.config(show='')
                self.eye_btn_confirm.config(image=self.eye_open_confirm)
                self.confirm_password_visible = True

    # ============ Xử lý sự kiện đăng ký ============
    def on_register(self):
        email = self.email_entry.get()
        fullname = self.fullname_entry.get()
        password = self.password_entry.get()
        confirm_password = self.confirm_password_entry.get()

        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if email == '' or email == 'Email':
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập email!")
            return
        if not re.match(email_pattern, email):
            messagebox.showerror("Lỗi", "Email không đúng định dạng!")
            return
        if fullname == '' or fullname == 'Tên đầy đủ':
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập tên đầy đủ!")
            return
        if password == '' or password == 'Mật khẩu':
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập mật khẩu!")
            return
        if len(password) < 6:
            messagebox.showerror("Lỗi", "Mật khẩu phải có ít nhất 6 ký tự!")
            return
        if confirm_password == '' or confirm_password == 'Xác nhận mật khẩu':
            messagebox.showwarning("Cảnh báo", "Vui lòng xác nhận mật khẩu!")
            return
        if password != confirm_password:
            messagebox.showwarning("Cảnh báo", "Mật khẩu xác nhận không khớp!")
            return

        messagebox.showinfo("Thành công", "Đăng ký thành công!")
        self.controller.show_frame("LoginPage")