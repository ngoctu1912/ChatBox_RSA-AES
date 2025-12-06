import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from components.ContactItem import ContactItem
from datetime import datetime
import os


class Sidebar(tk.Frame):
    def __init__(self, parent, controller=None, user_info=None, contacts=None, on_contact_click=None, sio_client=None, user_id=None):
        super().__init__(parent, bg="#ffffff", width=280)
        self.pack_propagate(False)

        self.controller = controller              
        self.on_contact_click = on_contact_click
        self.all_contacts = contacts or []        
        self.contact_items = []
        self.contact_widgets = {} # FIX MỚI: Dictionary lưu trữ widget theo tên để cập nhật nhanh
        self.sio_client = sio_client  #  Lưu socket client
        self.user_id = user_id  #  Lưu user_id
        self.user_info = user_info  #  Lưu user_info để truyền cho SettingsDialog

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

        # Icon cài đặt (có thể click)
        settings_icon = self._load_image("assets/icons/settings.png", (18, 18))
        if settings_icon:
            self.settings_icon = settings_icon
            settings_label = tk.Label(header, image=self.settings_icon, bg="#EEEEEE", cursor="hand2")
            settings_label.pack(side="right", padx=10)
            settings_label.bind("<Button-1>", lambda e: self.open_settings())
        else:
            settings_label = tk.Label(header, text="⚙️", bg="#EEEEEE", font=("Inter", 12), cursor="hand2")
            settings_label.pack(side="right", padx=10)
            settings_label.bind("<Button-1>", lambda e: self.open_settings())

        # ================== Ô TÌM KIẾM ==================
        search_frame = tk.Frame(self, bg="#ffffff")
        search_frame.pack(fill="x", padx=10, pady=(8, 5))

        self.search_var = tk.StringVar()
        
        # Frame chứa Entry và nút X
        search_input_frame = tk.Frame(search_frame, bg="#f0f0f0", relief="solid", borderwidth=1)
        search_input_frame.pack(fill="x")
        
        self.search_entry = ttk.Entry(search_input_frame, textvariable=self.search_var, font=("Inter", 11))
        self.search_entry.pack(side="left", fill="both", expand=True, ipady=4, padx=(5, 0))
        self.search_entry.insert(0, "Tìm kiếm cuộc trò chuyện")
        
        # Nút X để xóa tìm kiếm
        self.clear_button = tk.Button(
            search_input_frame,
            text="✕",
            font=("Inter", 12),
            bg="#f0f0f0",
            fg="#999999",
            relief="flat",
            cursor="hand2",
            command=self.clear_search,
            width=2
        )
        self.clear_button.pack(side="right", padx=(0, 5))
        self.clear_button.pack_forget()  # Ẩn ban đầu

        def clear_placeholder(event):
            if self.search_entry.get() == "Tìm kiếm cuộc trò chuyện":
                self.search_entry.delete(0, tk.END)
                self.clear_button.pack(side="right", padx=(0, 5))  # Hiện nút X

        def restore_placeholder(event):
            if not self.search_entry.get():
                self.search_entry.insert(0, "Tìm kiếm cuộc trò chuyện")
                self.clear_button.pack_forget()  # Ẩn nút X

        self.search_entry.bind("<FocusIn>", clear_placeholder)
        self.search_entry.bind("<FocusOut>", restore_placeholder)
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
        #  Tăng tốc độ cuộn từ 1 lên 3 units
        if event.num == 4 or event.delta > 0:
            self.canvas.yview_scroll(-3, "units")
        elif event.num == 5 or event.delta < 0:
            self.canvas.yview_scroll(3, "units")
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
        self.contact_widgets.clear() # Clear dictionary

        # 
        if contact_list:
            for c in contact_list:
                name = c.get("name", "Người dùng")
                message = c.get("message", "")
                unread_count = c.get("unread_count", 0) 
                time_obj = c.get("latest_message_time", datetime.min)
                is_online = c.get("is_online", False) # <--- LẤY TRẠNG THÁI ONLINE
                
                # Định dạng thời gian
                time_str = ""
                if time_obj != datetime.min:
                    time_str = time_obj.strftime("%H:%M") 

                item = ContactItem(
                    self.contacts_frame,
                    self.avatar_icon,
                    name,
                    message,
                    latest_time=time_str,
                    unread_count=unread_count,
                    on_select=self.handle_contact_select,
                    is_online=is_online # <--- TRUYỀN VÀO ContactItem
                )
                item.pack(fill="x", pady=(0, 3))
                self.contact_items.append(item)
                self.contact_widgets[name] = item # Lưu widget theo tên

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
            # Lưu ý: Việc gọi mark_as_read đã được chuyển sang ChatScreen.py (tự động gọi khi mở chat)
            
            # Cập nhật số lượng tin chưa đọc thành 0 trên UI (Client-side)
            if selected_item.unread_count > 0:
                 selected_item.update_unread_count(0)
                 # Cập nhật lại dữ liệu trong self.all_contacts (in-memory)
                 # Logic này được xử lý trong Chat.py. Sidebar chỉ tập trung hiển thị
            
            #  XÓA KEYWORD TÌM KIẾM VÀ HIỆN LẠI DANH SÁCH ĐẦY ĐỦ
            self.clear_search()
            
            # Trả về (tên, avatar_icon) để mở ChatScreen bên phải
            self.on_contact_click(selected_item.name, self.avatar_icon)
    
    def clear_search(self):
        """Xóa keyword tìm kiếm và hiện lại danh sách đầy đủ"""
        self.search_var.set("")
        self.search_entry.delete(0, tk.END)
        self.search_entry.insert(0, "Tìm kiếm cuộc trò chuyện")
        self.clear_button.pack_forget()  # Ẩn nút X
        self.display_contacts(self.all_contacts)  # Hiện lại danh sách đầy đủ
    
    def filter_contacts(self):
        """Lọc theo keyword trong search box"""
        keyword = self.search_var.get().strip().lower()
        if not keyword or keyword == "tìm kiếm cuộc trò chuyện":
            self.display_contacts(self.all_contacts)
            self.clear_button.pack_forget()  # Ẩn nút X khi không có keyword
            return
        
        # Hiện nút X khi có keyword
        self.clear_button.pack(side="right", padx=(0, 5))
        
        # Lọc danh bạ
        filtered = [c for c in self.all_contacts if keyword in c.get("name", "").lower()]
        self.display_contacts(filtered)

    def get_avatar_for_contact(self, contact_name):
        # ... (giữ nguyên)
        for item in self.contact_items:
            if item.name == contact_name:
                return item.avatar_icon

        # Ảnh mặc định
        default_icon = self._load_image("assets/icons/avatar_default.png", (45, 45))
        return default_icon if default_icon else self.avatar_icon
    
    
    def update_contact_unread_count(self, contact_name, new_count):
        """
        Cập nhật số lượng tin nhắn chưa đọc cho một contact cụ thể.
        Phương thức này được gọi từ Chat.py (ChatManager).
        """
        item = self.contact_widgets.get(contact_name)
        if item:
            item.update_unread_count(new_count)
        else:
            print(f" Warning: Contact widget not found for {contact_name}")
    
    def update_single_contact(self, contact_name, message_preview, latest_time):
        """
         Cập nhật CHỈ MỘT contact item thay vì reload toàn bộ
        Tránh destroy ChatScreen đang active
        """
        print(f"📝 [Sidebar] update_single_contact called for {contact_name}")
        
        # Lưu lại contact đang được chọn (ưu tiên contact_name nếu không có selected nào)
        currently_selected = contact_name  # Mặc định là contact đang update
        for item in self.contact_items:
            if item.is_selected:
                currently_selected = item.name
                print(f" [Sidebar] Currently selected: {currently_selected}")
                break
        
        if not currently_selected:
            currently_selected = contact_name
            print(f" [Sidebar] No selection found, using contact_name: {contact_name}")
        
        # Cập nhật dữ liệu contact trong all_contacts
        contact_updated = False
        for contact in self.all_contacts:
            if contact.get('name') == contact_name:
                contact['message'] = message_preview
                contact['latest_message_time'] = latest_time
                contact_updated = True
                break
        
        if not contact_updated:
            print(f" [Sidebar] Contact not found in all_contacts: {contact_name}")
            return
        
        # Sort lại danh sách
        self.all_contacts.sort(key=lambda x: x.get('latest_message_time', datetime.min), reverse=True)
        
        # Reload sidebar với danh sách đã sort
        self.display_contacts(self.all_contacts)
        
        # Khôi phục trạng thái selected (với delay nhỏ để đảm bảo UI đã render)
        def restore_selection():
            try:
                for item in self.contact_items:
                    if not item.winfo_exists():
                        continue
                    if item.name == currently_selected:
                        item.set_selected(True)
                        print(f"✅ [Sidebar] Restored selection for {currently_selected}")
                        return
                print(f"❌ [Sidebar] Could not find item to restore selection: {currently_selected}")
            except Exception as e:
                print(f"⚠️ [Sidebar] Error restoring selection: {e}")
        
        self.after(10, restore_selection)
        
        print(f" [Sidebar] Reloaded and sorted contacts after update")

    # ==================  THÊM MỚI: CẬP NHẬT TRẠNG THÁI ONLINE/OFFLINE ==================
    def update_contact_status(self, contact_name, is_online):
        """
        Cập nhật trạng thái online/offline cho một contact cụ thể.
        Phương thức này được gọi từ Chat.py khi nhận event user_online/user_offline.
        
        Args:
            contact_name (str): Tên contact cần cập nhật
            is_online (bool): True nếu online, False nếu offline
        """
        item = self.contact_widgets.get(contact_name)
        if item:
            # Gọi phương thức của ContactItem để cập nhật hiển thị
            if hasattr(item, 'update_online_status'):
                item.update_online_status(is_online)
            else:
                # Fallback: Reload toàn bộ danh sách contacts
                # (Cách này chậm hơn nhưng đảm bảo cập nhật)
                for contact in self.all_contacts:
                    if contact.get('name') == contact_name:
                        contact['is_online'] = is_online
                        break
                self.display_contacts(self.all_contacts)
        else:
            print(f" Warning: Contact widget not found for {contact_name}")

    # ================== BỔ SUNG: TÁI LẬP LỰA CHỌN SAU KHI REFRESH (GIỮ NGUYÊN) ==================
    def reselect_contact(self, contact_name):
        """
        Tái lập trạng thái được chọn cho ContactItem sau khi danh sách được refresh.
        """
        for item in self.contact_items:
            if item.name == contact_name:
                item.set_selected(True)
            else:
                item.set_selected(False)


    # ================== ĐĂNG XUẤT ==================
    def logout_action(self):
        from tkinter import messagebox
        from backend.Config.UserModel import UserModel
        
        confirm = messagebox.askyesno("Xác nhận", "Bạn có chắc muốn đăng xuất?")
        if not confirm:
            return

        #  CẬP NHẬT TRẠNG THÁI OFFLINE TRONG DB
        if self.user_id:
            try:
                UserModel.update_online_status(self.user_id, False)
                print(f" [LOGOUT] Set user {self.user_id} offline in DB")
            except Exception as e:
                print(f" [LOGOUT] Failed to update DB: {e}")
        
        #  DISCONNECT SOCKET (backend sẽ tự động emit user_offline)
        if self.sio_client and self.sio_client.connected:
            try:
                self.sio_client.disconnect()
                print(f" [LOGOUT] Socket disconnected for user {self.user_id}")
            except Exception as e:
                print(f" [LOGOUT] Failed to disconnect socket: {e}")

        # Quay về trang Home
        if self.controller:
            try:
                self.controller.show_frame("HomePage")
            except Exception as e:
                print("Không thể show HomePage:", e)
    
    def open_settings(self):
        """Mở popup cài đặt"""
        from screens.SettingsDialog import SettingsDialog
        from backend.Config.UserModel import UserModel
        
        # Lấy thông tin đầy đủ từ database
        user_from_db = UserModel.get_user_by_id(self.user_id)
        
        if user_from_db:
            user_data = {
                'user_id': self.user_id,
                'full_name': user_from_db.get('full_name', ''),
                'email': user_from_db.get('email', ''),
                'department': user_from_db.get('department', 'IT'),
                'role': user_from_db.get('role', 'staff')
            }
        else:
            # Fallback nếu không tìm thấy trong DB
            user_data = {
                'user_id': self.user_id,
                'full_name': self.user_info.get('name', ''),
                'email': self.user_info.get('email', ''),
                'department': 'IT',
                'role': 'staff'
            }
        
        SettingsDialog(self, user_data)

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