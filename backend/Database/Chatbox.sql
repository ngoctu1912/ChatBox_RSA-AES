CREATE DATABASE chatbox CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE chatbox;

-- =============================================
-- 1. NGƯỜI DÙNG (USERS)
-- =============================================
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    department VARCHAR(100) DEFAULT 'IT',
    role ENUM('admin','staff','manager') DEFAULT 'staff',
    avatar_url VARCHAR(255) DEFAULT NULL,
    is_online BOOLEAN DEFAULT FALSE,
    last_seen TIMESTAMP NULL DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =============================================
-- 2. KHÓA RSA (rsa_keys)
-- =============================================
CREATE TABLE rsa_keys (
    key_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    public_key TEXT NOT NULL,
    private_key_encrypted TEXT NOT NULL,
    key_size INT DEFAULT 2048,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =============================================
-- 3. CUỘC TRÒ CHUYỆN 1-1 (conversations)
-- ĐÃ LOẠI BỎ aes_key_encrypted và iv
-- =============================================
CREATE TABLE conversations (
    conversation_id INT AUTO_INCREMENT PRIMARY KEY,
    user1_id INT NOT NULL,
    user2_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user1_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (user2_id) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE KEY unique_pair (user1_id, user2_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =============================================
-- 4. TIN NHẮN (messages)
-- ĐÃ BỔ SUNG nonce_tag_data và aes_key_encrypted
-- =============================================
CREATE TABLE messages (
    message_id INT AUTO_INCREMENT PRIMARY KEY,
    conversation_id INT NOT NULL,
    sender_id INT NOT NULL,
    receiver_id INT NOT NULL,
    
    message_encrypted TEXT NOT NULL,
    nonce_tag_data TEXT NOT NULL,           -- Nonce + Tag cho AES-GCM
    aes_key_encrypted TEXT NULL,            -- Key AES đã mã hóa RSA (cho Key Rotation)
    
    message_hash VARCHAR(64) NULL,          -- HMAC (hoặc hash khác)
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =============================================
-- 5. TRẠNG THÁI TIN NHẮN (message_status)
-- =============================================
CREATE TABLE message_status (
    status_id INT AUTO_INCREMENT PRIMARY KEY,
    message_id INT NOT NULL,
    user_id INT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP NULL DEFAULT NULL,
    FOREIGN KEY (message_id) REFERENCES messages(message_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =============================================
-- 6. SESSION KEYS (session_keys)
-- Dùng để backup AES session keys từ Redis
-- =============================================
CREATE TABLE session_keys (
    session_id INT AUTO_INCREMENT PRIMARY KEY,
    conversation_id INT NOT NULL,
    aes_key_encrypted TEXT NOT NULL,
    created_by INT NOT NULL,
    expires_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =============================================
-- DỮ LIỆU MẪU (USERS)
-- =============================================
INSERT INTO users (full_name, email, password_hash, role, is_online)
VALUES
('Admin', 'admin@company.com', '$2b$12$3y.nTqG3Pg/fq8WusYZ5duyL1gHmjxwV8ByPgjm.LdpE9GRzP50eC', 'admin', TRUE),
('Lan', 'lan@company.com', '$2b$12$3y.nTqG3Pg/fq8WusYZ5duyL1gHmjxwV8ByPgjm.LdpE9GRzP50eC', 'staff', TRUE),
('Minh', 'minh@company.com', '$2b$12$3y.nTqG3Pg/fq8WusYZ5duyL1gHmjxwV8ByPgjm.LdpE9GRzP50eC', 'staff', TRUE),
('Hương', 'huong@company.com', '$2b$12$3y.nTqG3Pg/fq8WusYZ5duyL1gHmjxwV8ByPgjm.LdpE9GRzP50eC', 'staff', FALSE),
('Dũng', 'dung@company.com', '$2b$12$3y.nTqG3Pg/fq8WusYZ5duyL1gHmjxwV8ByPgjm.LdpE9GRzP50eC', 'manager', TRUE),
('Bình', 'binh@company.com', '$2b$12$3y.nTqG3Pg/fq8WusYZ5duyL1gHmjxwV8ByPgjm.LdpE9GRzP50eC', 'staff', FALSE),
('Trang', 'trang@company.com', '$2b$12$3y.nTqG3Pg/fq8WusYZ5duyL1gHmjxwV8ByPgjm.LdpE9GRzP50eC', 'staff', FALSE),
('Phúc', 'phuc@company.com', '$2b$12$3y.nTqG3Pg/fq8WusYZ5duyL1gHmjxwV8ByPgjm.LdpE9GRzP50eC', 'staff', FALSE),
('Hải', 'hai@company.com', '$2b$12$3y.nTqG3Pg/fq8WusYZ5duyL1gHmjxwV8ByPgjm.LdpE9GRzP50eC', 'staff', TRUE),
('Lộc', 'loc@company.com', '$2b$12$3y.nTqG3Pg/fq8WusYZ5duyL1gHmjxwV8ByPgjm.LdpE9GRzP50eC', 'staff', TRUE);

-- =============================================
-- DỮ LIỆU MẪU (RSA KEYS)
-- =============================================
INSERT INTO rsa_keys (user_id, public_key, private_key_encrypted)
VALUES
(1, 'PUBLIC_KEY_ADMIN', 'PRIVATE_KEY_ADMIN'),
(2, 'PUBLIC_KEY_LAN', 'PRIVATE_KEY_LAN'),
(3, 'PUBLIC_KEY_MINH', 'PRIVATE_KEY_MINH'),
(4, 'PUBLIC_KEY_HUONG', 'PRIVATE_KEY_HUONG'),
(5, 'PUBLIC_KEY_DUNG', 'PRIVATE_KEY_DUNG'),
(6, 'PUBLIC_KEY_BINH', 'PRIVATE_KEY_BINH'),
(7, 'PUBLIC_KEY_TRANG', 'PRIVATE_KEY_TRANG'),
(8, 'PUBLIC_KEY_PHUC', 'PRIVATE_KEY_PHUC'),
(9, 'PUBLIC_KEY_HAI', 'PRIVATE_KEY_HAI'),
(10, 'PUBLIC_KEY_LOC', 'PRIVATE_KEY_LOC');

-- =============================================
-- DỮ LIỆU MẪU (CONVERSATIONS)
-- Giữ nguyên ID, loại bỏ AES key/IV
-- =============================================
INSERT INTO conversations (user1_id, user2_id)
VALUES
(1, 2), -- Admin và Lan
(1, 3), -- Admin và Minh
(2, 3), -- Lan và Minh
(3, 5), -- Minh và Dũng
(1, 5); -- Admin và Dũng

-- =============================================
-- DỮ LIỆU MẪU (MESSAGES)
-- SỬ DỤNG DỮ LIỆU MÃ HÓA GIẢ LẬP
-- (nonce_tag_data = nonce:tag, aes_key_encrypted = NULL vì dùng Session Key)
-- =============================================
INSERT INTO messages (conversation_id, sender_id, receiver_id, message_encrypted, nonce_tag_data, message_hash, aes_key_encrypted)
VALUES
(1, 1, 2, 'Lan, kiểm tra lại module login nhé.', 'NONCE01:TAG01', 'HASH_001', NULL),
(1, 2, 1, 'Ok admin, em đã sửa lỗi xác thực.', 'NONCE02:TAG02', 'HASH_002', NULL),
(2, 1, 3, 'Minh, tiến độ phần mã hóa tới đâu?', 'NONCE03:TAG03', 'HASH_003', NULL),
(2, 3, 1, 'Em đang test RSA-AES, tầm 70% rồi.', 'NONCE04:TAG04', 'HASH_004', NULL),
(3, 2, 3, 'Minh, gửi bản mới của UI cho chị.', 'NONCE05:TAG05', 'HASH_005', NULL),
(3, 3, 2, 'Dạ chị Lan, em vừa commit lên repo rồi ạ.', 'NONCE06:TAG06', 'HASH_006', NULL),
(4, 3, 5, 'Anh Dũng, server IT đã restart xong.', 'NONCE07:TAG07', 'HASH_007', NULL),
(4, 5, 3, 'Tốt, kiểm tra lại log giúp anh.', 'NONCE08:TAG08', 'HASH_008', NULL),
(5, 1, 5, 'Dũng, tuần sau họp tiến độ nha.', 'NONCE09:TAG09', 'HASH_009', NULL),
(5, 5, 1, 'Ok Admin, em note lại rồi.', 'NONCE10:TAG10', 'HASH_010', NULL);

-- =============================================
-- DỮ LIỆU MẪU (MESSAGE STATUS)
-- =============================================
INSERT INTO message_status (message_id, user_id, is_read)
VALUES
(1, 2, TRUE),
(2, 1, TRUE),
(3, 3, TRUE),
(4, 1, TRUE),
(5, 3, TRUE),
(6, 2, TRUE),
(7, 5, TRUE),
(8, 3, TRUE),
(9, 5, FALSE),
(10, 1, TRUE);


-- Đảm bảo bạn đang sử dụng kiểu TEXT hoặc LONGTEXT
ALTER TABLE rsa_keys 
MODIFY public_key TEXT NOT NULL,
MODIFY private_key_encrypted TEXT NOT NULL;

CREATE TABLE IF NOT EXISTS pending_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sender_id INT NOT NULL,
    receiver_id INT NOT NULL,
    conversation_id INT NOT NULL,
    plain_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (sender_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (receiver_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    
    INDEX idx_receiver (receiver_id),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
