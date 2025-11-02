CREATE DATABASE chatbox CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE chatbox;

-- =============================================
-- 1. NGƯỜI DÙNG (USERS)
-- =============================================
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,      -- bcrypt
    department VARCHAR(100) DEFAULT 'IT',     -- luôn là IT
    role ENUM('admin','staff','manager') DEFAULT 'staff',
    avatar_url VARCHAR(255) DEFAULT NULL,
    is_online BOOLEAN DEFAULT FALSE,
    last_seen TIMESTAMP NULL DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =============================================
-- 2. KHÓA RSA (1 user = 1 cặp)
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
-- 3. CUỘC TRÒ CHUYỆN 1-1
-- =============================================
CREATE TABLE conversations (
    conversation_id INT AUTO_INCREMENT PRIMARY KEY,
    user1_id INT NOT NULL,
    user2_id INT NOT NULL,
    aes_key_encrypted TEXT NOT NULL, 
    iv VARCHAR(32) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user1_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (user2_id) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE KEY unique_pair (user1_id, user2_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =============================================
-- 4. TIN NHẮN
-- =============================================
CREATE TABLE messages (
    message_id INT AUTO_INCREMENT PRIMARY KEY,
    conversation_id INT NOT NULL,
    sender_id INT NOT NULL,
    receiver_id INT NOT NULL,
    message_encrypted TEXT NOT NULL,
    message_hash VARCHAR(64) NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =============================================
-- 5. TRẠNG THÁI TIN NHẮN
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
-- DỮ LIỆU MẪU (bcrypt của "123456")
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
-- KHÓA RSA MẪU
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
-- CUỘC TRÒ CHUYỆN MẪU
-- =============================================
INSERT INTO conversations (user1_id, user2_id, aes_key_encrypted, iv)
VALUES
(1, 2, 'RSA_ENC_AES_ADMIN_LAN', 'iv0001'),
(1, 3, 'RSA_ENC_AES_ADMIN_MINH', 'iv0002'),
(2, 3, 'RSA_ENC_AES_LAN_MINH', 'iv0003'),
(3, 5, 'RSA_ENC_AES_MINH_DUNG', 'iv0004'),
(1, 5, 'RSA_ENC_AES_ADMIN_DUNG', 'iv0005');

-- =============================================
-- TIN NHẮN MẪU
-- =============================================
INSERT INTO messages (conversation_id, sender_id, receiver_id, message_encrypted, message_hash)
VALUES
(1, 1, 2, 'Lan, kiểm tra lại module login nhé.', 'HASH_001'),
(1, 2, 1, 'Ok admin, em đã sửa lỗi xác thực.', 'HASH_002'),
(2, 1, 3, 'Minh, tiến độ phần mã hóa tới đâu?', 'HASH_003'),
(2, 3, 1, 'Em đang test RSA-AES, tầm 70% rồi.', 'HASH_004'),
(3, 2, 3, 'Minh, gửi bản mới của UI cho chị.', 'HASH_005'),
(3, 3, 2, 'Dạ chị Lan, em vừa commit lên repo rồi ạ.', 'HASH_006'),
(4, 3, 5, 'Anh Dũng, server IT đã restart xong.', 'HASH_007'),
(4, 5, 3, 'Tốt, kiểm tra lại log giúp anh.', 'HASH_008'),
(5, 1, 5, 'Dũng, tuần sau họp tiến độ nha.', 'HASH_009'),
(5, 5, 1, 'Ok Admin, em note lại rồi.', 'HASH_010');

-- =============================================
-- TRẠNG THÁI TIN NHẮN
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
