import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import os, re

class ForgotPasswordWindow(tk.Toplevel):
    def __init__(self, parent, load_icon_func):
        super().__init__(parent)
        self.title("Quên Mật Khẩu")
        self.geometry("500x480")
        self.configure(bg='white')
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # Căn giữa cửa sổ
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.winfo_screenheight() // 2) - (480 // 2)
        self.geometry(f"500x480+{x}+{y}")

        self.load_icon = load_icon_func

        # ==== Tiêu đề ====
        tk.Label(
            self, text="QUÊN MẬT KHẨU",
            font=('Arial', 22),
            bg='white', fg='#000'
        ).pack(pady=(40, 25))

        # ==== Form ====
        form_container = tk.Frame(self, bg='white')
        form_container.pack(expand=True)

        form_frame = tk.Frame(form_container, bg='white', width=380)
        form_frame.pack(pady=(10, 20))
        form_frame.pack_propagate(False)

        form_container.pack_configure(anchor='center')

        # Các input field
        email_field = self.create_input(form_frame, 'user.png', 'Email', 0, False)
        pass_field = self.create_input(form_frame, 'lock.png', 'Mật khẩu mới', 1, True)
        confirm_field = self.create_input(form_frame, 'lock.png', 'Xác nhận mật khẩu', 2, True)

        self.email_entry = email_field
        self.pass_entry = pass_field
        self.confirm_entry = confirm_field

        # Nút xác nhận
        tk.Button(
            self, text="ĐẶT LẠI MẬT KHẨU",
            font=('Arial', 13),
            bg='#0099FF', fg='white',
            relief='flat', padx=90, pady=10,
            cursor='hand2', command=self.validate_inputs
        ).pack(pady=(25, 20))

    # ======== Tạo input field ========
    def create_input(self, parent, icon_name, placeholder, row, is_password):
        wrapper = tk.Frame(parent, bg='white')
        wrapper.grid(row=row, column=0, sticky='ew', pady=(0, 22))
        wrapper.grid_columnconfigure(1, weight=1)

        icon_img = self.load_icon(icon_name, size=(22, 22))
        icon_label = tk.Label(wrapper, image=icon_img, bg='white')
        icon_label.image = icon_img
        icon_label.grid(row=0, column=0, padx=(0, 12))

        entry = tk.Entry(
            wrapper, font=('Arial', 13),
            bg='white', fg='gray', relief='flat',
            width=30, show='•' if is_password else ''
        )
        entry.grid(row=0, column=1, sticky='ew', ipady=6)
        entry.insert(0, placeholder)

        def on_focus_in(e):
            if entry.get() == placeholder:
                entry.delete(0, tk.END)
                entry.config(fg='black')
                separator.config(bg='#0099FF')

        def on_focus_out(e):
            if entry.get() == '':
                entry.insert(0, placeholder)
                entry.config(fg='gray')
            separator.config(bg='#CCCCCC')

        entry.bind('<FocusIn>', on_focus_in)
        entry.bind('<FocusOut>', on_focus_out)

        # ======== Hiển thị / ẩn mật khẩu ==========
        if is_password:
            eye_open = self.load_icon('openeye.png', (22, 22))
            eye_close = self.load_icon('closeeye.png', (22, 22))
            visible = False

            eye_btn = tk.Button(
                wrapper, image=eye_close, bg='white',
                relief='flat', borderwidth=0, cursor='hand2'
            )
            eye_btn.image = eye_close
            eye_btn.grid(row=0, column=2, padx=(8, 0))

            def toggle():
                nonlocal visible
                if visible:
                    entry.config(show='•')
                    eye_btn.config(image=eye_close)
                else:
                    entry.config(show='')
                    eye_btn.config(image=eye_open)
                visible = not visible

            eye_btn.config(command=toggle)

        separator = tk.Frame(wrapper, bg='#CCCCCC', height=1)
        separator.grid(row=1, column=0, columnspan=3, sticky='ew', pady=(5, 0))

        return entry

    # ======== Validate inputs và xử lý ========
    def validate_inputs(self):
        email = self.email_entry.get().strip()
        new_pass = self.pass_entry.get().strip()
        confirm = self.confirm_entry.get().strip()

        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if email in ['', 'Email']:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập email!")
            return
        if not re.match(email_pattern, email):
            messagebox.showerror("Lỗi", "Email không đúng định dạng!")
            return
        if new_pass in ['', 'Mật khẩu mới']:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập mật khẩu mới!")
            return
        if len(new_pass) < 6:
            messagebox.showerror("Lỗi", "Mật khẩu phải có ít nhất 6 ký tự!")
            return
        if confirm in ['', 'Xác nhận mật khẩu']:
            messagebox.showwarning("Cảnh báo", "Vui lòng xác nhận mật khẩu!")
            return
        if new_pass != confirm:
            messagebox.showerror("Lỗi", "Mật khẩu xác nhận không khớp!")
            return

        messagebox.showinfo("Thành công", "Mật khẩu đã được đặt lại thành công!")
        self.destroy()
