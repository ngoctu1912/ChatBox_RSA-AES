import tkinter as tk
from PIL import Image, ImageTk
import os

class HomePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg='#FFFFFF')
        self.controller = controller
        
        # HEADER
        self.header = tk.Frame(self, bg='#0D99FF', height=80)
        self.header.pack(fill='x', side='top')
        self.header.pack_propagate(False)
        
        # Tiêu đề bên trái
        self.title_label = tk.Label(
            self.header, 
            text="Mã hóa tin nhắn",
            font=('Arial', 18),
            bg='#0D99FF',
            fg='#FFFFFF'
        )
        self.title_label.pack(side='left', padx=50, pady=15)
        
        # Nút bên phải
        self.button_frame = tk.Frame(self.header, bg='#0D99FF')
        self.button_frame.pack(side='right', padx=50, pady=15)
        
        # Nút Đăng nhập
        self.login_btn = tk.Button(
            self.button_frame,
            text="Đăng nhập",
            font=('Arial', 12),
            bg='#FFFFFF',
            fg='black',
            relief='flat',
            padx=20,
            pady=6,
            width=8,
            cursor='hand2',
            command=lambda: controller.show_frame("LoginPage")
        )
        self.login_btn.pack(side='left', padx=5)
        
        # Nút Đăng ký
        self.register_btn = tk.Button(
            self.button_frame,
            text="Đăng ký",
            font=('Arial', 12),
            bg='#FFFFFF',
            fg='black',
            relief='flat',
            padx=20,
            pady=6,
            width=8,
            cursor='hand2',
            command=lambda: controller.show_frame("RegisterPage")
        )
        self.register_btn.pack(side='left', padx=5)

        # Hiệu ứng hover
        def on_enter(e): e.widget.config(bg="#7BD4FD", fg="#FFFFFF")
        def on_leave(e): e.widget.config(bg='#FFFFFF', fg='#000000')

        for btn in (self.login_btn, self.register_btn):
            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)
        
        # CONTENT
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
        
        # --- Khung phải: Văn bản ---
        self.right_frame = tk.Frame(self, bg='#FFFFFF')
        self.right_frame.place(x=620, y=250, width=550, height=420)
        
        self.main_title = tk.Label(
            self.right_frame,
            text="MÃ HÓA TIN NHẮN",
            font=('Arial', 30),
            bg='#FFFFFF',
            fg='black',
        )
        self.main_title.pack(pady=(80, 30))
        
        self.description = tk.Label(
            self.right_frame,
            text="Bảo mật tin nhắn của bạn - dễ dàng và an toàn",
            font=('Arial', 18),
            bg='#FFFFFF',
            fg='#333333'
        )
        self.description.pack(pady=10)
