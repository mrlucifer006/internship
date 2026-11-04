-- SSBS Visitor & Logistics Management System - SQL DDL for Java Servlets

CREATE TABLE IF NOT EXISTS employee (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(30) NOT NULL,
    login_id VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    auth_level INT NOT NULL DEFAULT 3,
    status INT DEFAULT 0,
    department VARCHAR(150) DEFAULT 'Operations',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

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
    status INT DEFAULT 1,
    denial_reason TEXT NULL,
    id_type VARCHAR(50) NOT NULL,
    id_number VARCHAR(100) NOT NULL,
    badge_number VARCHAR(50) NULL,
    added_by VARCHAR(100) NULL,
    department VARCHAR(150) NULL
);

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
    status VARCHAR(50) DEFAULT 'Inside'
);
