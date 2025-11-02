import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import tkinter as tk
from screens.Home import HomePage
from screens.Login import LoginPage 
from screens.Register import RegisterPage
from frontend.components.Chat import Chat

class App(tk.Tk):  
    def __init__(self):
        super().__init__()
        self.title("Mã hóa tin nhắn")
        self.geometry("1200x650")
        self.configure(bg='white')

        # === Lưu thông tin user hiện tại ===
        self.current_user = None

        # === Container để chứa các trang ===
        container = tk.Frame(self)
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # === Lưu các trang trong dictionary ===
        self.frames = {}
        for F in (HomePage, LoginPage, RegisterPage):
            page_name = F.__name__
            frame = F(parent=container, controller=self) 
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")  

        # === Hiển thị trang Home đầu tiên ===
        self.show_frame("HomePage")

    def show_frame(self, page_name):
        """Hiển thị trang được chỉ định"""
        # Nếu là ChatPage, cần tạo mới với current_user
        if page_name == "ChatPage":
            if not self.current_user:
                print("Chưa đăng nhập!")
                return
            
            # Xóa ChatPage cũ nếu có
            if "ChatPage" in self.frames:
                self.frames["ChatPage"].destroy()
            
            # Tạo ChatPage mới với user hiện tại
            container = self.frames[list(self.frames.keys())[0]].master
            chat_frame = Chat(parent=container, controller=self, user_data=self.current_user)
            self.frames["ChatPage"] = chat_frame
            chat_frame.grid(row=0, column=0, sticky="nsew")
        
        frame = self.frames[page_name]
        frame.tkraise()

if __name__ == "__main__":
    app = App()
    app.mainloop()