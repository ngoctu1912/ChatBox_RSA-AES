import tkinter as tk
from screens.Home import HomePage
from screens.Login import LoginPage 
from screens.Register import RegisterPage

class App(tk.Tk):  
    def __init__(self):
        super().__init__()
        self.title("Mã hóa tin nhắn")
        self.geometry("1200x700")
        self.configure(bg='white')

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
        frame = self.frames[page_name]
        frame.tkraise() 

if __name__ == "__main__":
    app = App()
    app.mainloop()