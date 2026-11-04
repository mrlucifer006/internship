-- SSBS Visitor & Logistics Management System
-- MySQL / MariaDB Production Schema

CREATE DATABASE IF NOT EXISTS ssbs_vms CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ssbs_vms;

-- Employees Table
CREATE TABLE IF NOT EXISTS employee (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(30) NOT NULL,
    login_id VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    auth_level INT NOT NULL DEFAULT 3,
    status INT DEFAULT 0,
    department VARCHAR(150) DEFAULT 'Operations',
    ip_address VARCHAR(45) NULL,
    last_seen TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Visitors Table
CREATE TABLE IF NOT EXISTS visitors (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(30) NOT NULL,
    person_to_visit VARCHAR(255) NOT NULL,
    reason TEXT NOT NULL,
    has_vehicle TINYINT(1) DEFAULT 0,
    vehicle_number VARCHAR(50) NULL,
    entry_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    exit_time TIMESTAMP NULL,
    status INT DEFAULT 1 COMMENT '0: Pending, 1: Approved/Inside, 2: Exited, 3: Denied',
    denial_reason TEXT NULL,
    id_type VARCHAR(50) NOT NULL,
    id_number VARCHAR(100) NOT NULL,
    badge_number VARCHAR(50) NULL,
    added_by VARCHAR(100) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Vehicles & Logistics Table
CREATE TABLE IF NOT EXISTS vehicle (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    driver_name VARCHAR(255) NOT NULL,
    driver_phone VARCHAR(30) NOT NULL,
    driver_id_type VARCHAR(50) NOT NULL,
    driver_id_number VARCHAR(100) NOT NULL,
    veh_reg_no VARCHAR(50) NOT NULL,
    vehicle_img TEXT NULL,
    origin VARCHAR(255) NOT NULL,
    destination VARCHAR(255) NOT NULL,
    purchase_no VARCHAR(100) NOT NULL,
    entry_type VARCHAR(50) DEFAULT 'Entry',
    gross_weight DECIMAL(10,2) NOT NULL,
    tare_weight DECIMAL(10,2) NULL,
    material_type VARCHAR(255) NOT NULL,
    is_returnable TINYINT(1) DEFAULT 0,
    return_reason TEXT NULL,
    vehicle_length VARCHAR(100) DEFAULT 'Heavy 10-Wheeler',
    time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    exit_time TIMESTAMP NULL,
    status VARCHAR(50) DEFAULT 'Inside',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- WhatsApp Broadcast Queue Table
CREATE TABLE IF NOT EXISTS whatsapp_queue (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    phone VARCHAR(30) NOT NULL,
    recipient VARCHAR(255) NULL,
    message TEXT NOT NULL,
    message_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    attempts INT DEFAULT 0,
    time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Default Users Seed
INSERT INTO employee (name, phone, login_id, password, auth_level, status, department) VALUES
('Sanjai M S (Developer)', '9876543210', 'super', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 5, 1, 'R&D / Systems'),
('Rajesh Sharma', '9845123456', 'admin', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 4, 1, 'Administration'),
('Vikram Singh', '9811223344', 'supervisor1', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 2, 1, 'Security Gate'),
('Dr. Anita Desai', '9633445566', 'emp1', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 3, 1, 'Human Resources')
ON DUPLICATE KEY UPDATE id=id;
