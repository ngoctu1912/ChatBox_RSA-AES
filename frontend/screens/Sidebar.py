import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from components.ContactItem import ContactItem
import os


class Sidebar(tk.Frame):
    def __init__(self, parent, controller=None, user_info=None, contacts=None, on_contact_click=None):
        super().__init__(parent, bg="#ffffff", width=280)
        self.pack_propagate(False)

        self.controller = controller              
        self.on_contact_click = on_contact_click  # callback khi chọn 1 liên hệ
        self.all_contacts = contacts or []        # danh sách tất cả liên hệ
        self.contact_items = []                   # các widget ContactItem đang hiển thị

        # ================== HEADER NGƯỜI DÙNG ==================
        header = tk.Frame(self, bg="#EEEEEE", height=60)
        header.pack(fill="x", pady=0)
        header.pack_propagate(False)

        # Ảnh đại diện user
        self.avatar_icon = self._load_image("assets/icons/avatar.png", (45, 45))
        avatar_label = tk.Label(header, image=self.avatar_icon, bg="#EEEEEE")
        avatar_label.pack(side="left", padx=10)

        # Thông tin người dùng
        name = user_info.get("name", "Người dùng") if user_info else "Người dùng"
        status_text = user_info.get("status", "Đang hoạt động") if user_info else "Đang hoạt động"

        info_frame = tk.Frame(header, bg="#EEEEEE")
        info_frame.pack(side="left", fill="y", padx=(0, 5))
        tk.Label(info_frame, text=name, font=("Inter", 14), bg="#EEEEEE").pack(anchor="w", pady=(7, 0))

        # Trạng thái
        status_icon = self._load_image("assets/icons/button.png", (12, 12))
        if status_icon:
            tk.Label(info_frame, image=status_icon, bg="#EEEEEE").pack(side="left", padx=(0, 3))
            self.status_icon = status_icon
        else:
            tk.Label(info_frame, text="🟢", bg="#EEEEEE").pack(side="left")

        tk.Label(info_frame, text=status_text, font=("Inter", 9), fg="green", bg="#EEEEEE").pack(side="left")

        # Icon cài đặt (trang trí)
        settings_icon = self._load_image("assets/icons/settings.png", (18, 18))
        if settings_icon:
            self.settings_icon = settings_icon
            tk.Label(header, image=self.settings_icon, bg="#EEEEEE", cursor="hand2").pack(side="right", padx=10)
        else:
            tk.Label(header, text="⚙️", bg="#EEEEEE", font=("Inter", 12)).pack(side="right", padx=10)

        # ================== Ô TÌM KIẾM ==================
        search_frame = tk.Frame(self, bg="#ffffff")
        search_frame.pack(fill="x", padx=10, pady=(8, 5))

        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, font=("Inter", 11))
        search_entry.pack(fill="x", ipady=4)
        search_entry.insert(0, "Tìm kiếm cuộc trò chuyện")

        def clear_placeholder(event):
            if search_entry.get() == "Tìm kiếm cuộc trò chuyện":
                search_entry.delete(0, tk.END)

        def restore_placeholder(event):
            if not search_entry.get():
                search_entry.insert(0, "Tìm kiếm cuộc trò chuyện")

        search_entry.bind("<FocusIn>", clear_placeholder)
        search_entry.bind("<FocusOut>", restore_placeholder)
        self.search_var.trace_add("write", lambda *args: self.filter_contacts())

        # ================== STYLE SCROLLBAR ==================
        self.setup_custom_scrollbar_style()

        # ================== DANH SÁCH LIÊN HỆ (có scrollbar) ==================
        contacts_container = tk.Frame(self, bg="#ffffff")
        contacts_container.pack(fill="both", expand=True, pady=(5, 0))

        self.canvas = tk.Canvas(contacts_container, bg="#ffffff", highlightthickness=0)
        self.contacts_frame = tk.Frame(self.canvas, bg="#ffffff")

        self.scrollbar = ttk.Scrollbar(
            contacts_container,
            orient="vertical",
            command=self.canvas.yview,
            style="Custom.Vertical.TScrollbar"
        )
        self.scrollbar_is_visible = False
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Tạo window có width cố định để layout ổn định
        self.canvas_window = self.canvas.create_window((0, 0), window=self.contacts_frame, anchor="nw", width=270)

        # Bind cuộn chuột mượt
        self._bind_mousewheel(self)
        self._bind_mousewheel(self.canvas)
        self._bind_mousewheel(self.contacts_frame)

        # Update width window khi canvas resize
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))
        self.contacts_frame.bind("<Configure>", lambda e: self.update_scrollbar_visibility())

        self.canvas.pack(side="left", fill="both", expand=True)
        self.after(100, self.update_scrollbar_visibility)

        # Hiển thị dữ liệu ban đầu
        self.display_contacts(self.all_contacts)

        # ================== NÚT ĐĂNG XUẤT ==================
        logout_frame = tk.Frame(self, bg="#ffffff")
        logout_frame.pack(side="bottom", fill="x", pady=(5, 0))

        logout_icon = self._load_image("assets/icons/logout.png", (20, 20))
        if logout_icon:
            self.logout_icon = logout_icon
        else:
            self.logout_icon = None

        logout_btn = tk.Button(
            logout_frame,
            text="  Đăng xuất",
            image=self.logout_icon,
            compound="left",
            bg="#ff3b3b",
            fg="white",
            font=("Inter", 13),
            relief="flat",
            anchor="w",
            padx=0,
            pady=10,
            cursor="hand2",
            command=self.logout_action  
        )
        logout_btn.pack(fill="x")
        logout_btn.config(anchor="center", justify="center")

        # Hover
        logout_btn.bind("<Enter>", lambda e: logout_btn.config(bg="#e53935"))
        logout_btn.bind("<Leave>", lambda e: logout_btn.config(bg="#ff3b3b"))

# ================== TẢI ẢNH VỚI KÍCH THƯỚC ==================
    def _load_image(self, relative_path, size):
        try:
            base_dir = os.path.dirname(__file__)
            path = os.path.join(base_dir, "..", relative_path)
            img = Image.open(path).resize(size, Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"Không tìm thấy ảnh {relative_path}: {e}")
            return None

# ================== TẠO STYLE CHO SCROLLBAR ==================
    def setup_custom_scrollbar_style(self):
        style = ttk.Style()
        style.theme_use('default')
        style.configure(
            "Custom.Vertical.TScrollbar",
            background="#E0E0E0",
            troughcolor="#ffffff",
            borderwidth=0,
            arrowsize=0,
            width=8
        )
        style.map(
            "Custom.Vertical.TScrollbar",
            background=[("active", "#B0B0B0"), ("!active", "#E0E0E0")]
        )

# ================== CUỘN CHUỘT MƯỢT ==================
    def _bind_mousewheel(self, widget):
        widget.bind("<MouseWheel>", self._on_mousewheel)  # Windows / Mac
        widget.bind("<Button-4>", self._on_mousewheel)    # Linux up
        widget.bind("<Button-5>", self._on_mousewheel)    # Linux down

# ================== XỬ LÝ CUỘN CHUỘT MƯỢT ==================
    def _on_mousewheel(self, event):
        if event.num == 4 or event.delta > 0:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:
            self.canvas.yview_scroll(1, "units")
        return "break"

# ================== HIỂN THỊ/ẨN SCROLLBAR ==================
    def update_scrollbar_visibility(self):
        self.canvas.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        canvas_height = self.canvas.winfo_height()
        content_height = self.contacts_frame.winfo_reqheight()

        if content_height > canvas_height and canvas_height > 1:
            if not self.scrollbar_is_visible:
                self.scrollbar.pack(side="right", fill="y", before=self.canvas)
                self.scrollbar_is_visible = True
        else:
            if self.scrollbar_is_visible:
                self.scrollbar.pack_forget()
                self.scrollbar_is_visible = False

    # ================== DANH BẠ ==================
    def display_contacts(self, contact_list):
        for widget in self.contacts_frame.winfo_children():
            widget.destroy()

        self.contact_items.clear()

        if contact_list:
            for c in contact_list:
                name = c.get("name", "Người dùng")
                message = c.get("message", "")
                has_unread = c.get("has_unread_messages", False)

                item = ContactItem(
                    self.contacts_frame,
                    self.avatar_icon,
                    name,
                    message,
                    has_unread_messages=has_unread,
                    on_select=self.handle_contact_select
                )
                item.pack(fill="x", pady=(0, 3))
                self.contact_items.append(item)

                # Bind cuộn cho từng item và children
                self._bind_mousewheel(item)
                for child in item.winfo_children():
                    self._bind_mousewheel(child)
        else:
            tk.Label(
                self.contacts_frame,
                text="(Không tìm thấy liên hệ phù hợp)",
                bg="#ffffff",
                fg="gray"
            ).pack(pady=20)

        self.after(50, self.update_scrollbar_visibility)

# ================== XỬ LÝ KHI CHỌN LIÊN HỆ ==================
    def handle_contact_select(self, selected_item):
        for item in self.contact_items:
            item.set_selected(item == selected_item)

        if self.on_contact_click:
            # Trả về (tên, avatar_icon) để mở ChatScreen bên phải
            self.on_contact_click(selected_item.name, self.avatar_icon)

    def filter_contacts(self):
        """Lọc theo keyword trong search box"""
        keyword = self.search_var.get().strip().lower()
        if not keyword or keyword == "tìm kiếm cuộc trò chuyện":
            self.display_contacts(self.all_contacts)
            return
        filtered = [c for c in self.all_contacts if keyword in c.get("name", "").lower()]
        self.display_contacts(filtered)

# ================== LẤY AVATAR THEO TÊN ==================
    def get_avatar_for_contact(self, contact_name):
        for item in self.contact_items:
            if item.name == contact_name:
                return item.avatar_icon

        # Ảnh mặc định
        default_icon = self._load_image("assets/icons/avatar_default.png", (45, 45))
        return default_icon if default_icon else self.avatar_icon

    # ================== ĐĂNG XUẤT ==================
    def logout_action(self):
        from tkinter import messagebox
        confirm = messagebox.askyesno("Xác nhận", "Bạn có chắc muốn đăng xuất?")
        if not confirm:
            return

        # Quay về trang Home
        if self.controller:
            try:
                self.controller.show_frame("HomePage")
            except Exception as e:
                print("Không thể show HomePage:", e)

    # ================== DỌN RÁC ==================
    def destroy(self):
        """Unbind mousewheel khi đóng frame"""
        try:
            self._unbind_mousewheel(self)
        except:
            pass
        super().destroy()

    def _unbind_mousewheel(self, widget):
        """Unbind mousewheel cho widget và tất cả con của nó"""
        try:
            widget.unbind("<MouseWheel>")
            widget.unbind("<Button-4>")
            widget.unbind("<Button-5>")
            for child in widget.winfo_children():
                self._unbind_mousewheel(child)
        except:
            pass
