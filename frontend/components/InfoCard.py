import tkinter as tk

class InfoCard(tk.Frame):
    def __init__(self, parent, icon, title, desc):
        super().__init__(
            parent, 
            bg="white",
            highlightbackground="#DADADA", 
            highlightthickness=1,   
            bd=0,
            padx=20, pady=15  
        )

        # Khung chứa icon
        icon_frame = tk.Frame(self, bg="white")
        icon_frame.pack(side="left", padx=(0, 15))
        tk.Label(icon_frame, image=icon, bg="white").pack()

        # Khung chứa nội dung
        text_frame = tk.Frame(self, bg="white")
        text_frame.pack(side="left", fill="both", expand=True)

        tk.Label(
            text_frame, 
            text=title, 
            font=("Inter", 14), 
            bg="white"
        ).pack(anchor="w")

        tk.Label(
            text_frame, 
            text=desc, 
            font=("Inter", 13), 
            fg="#333333", 
            bg="white"
        ).pack(anchor="w", pady=(3, 0))
