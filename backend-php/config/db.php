<?php
/**
 * SSBS Visitor & Logistics Management System - PHP Backend
 * Database Configuration & PDO Connection Handler
 */

header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

$db_host = getenv('DB_HOST') ?: 'localhost';
$db_port = getenv('DB_PORT') ?: '3306';
$db_name = getenv('DB_NAME') ?: 'ssbs_vms';
$db_user = getenv('DB_USER') ?: 'root';
$db_pass = getenv('DB_PASS') ?: '';

$pdo = null;

try {
    // Attempt MySQL connection
    $dsn = "mysql:host={$db_host};port={$db_port};dbname={$db_name};charset=utf8mb4";
    $pdo = new PDO($dsn, $db_user, $db_pass, [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        PDO::ATTR_TIMEOUT => 2
    ]);
} catch (Exception $e) {
    // Portable fallback to SQLite database file
    $sqlite_file = __DIR__ . '/../database.sqlite';
    $dsn = "sqlite:" . $sqlite_file;
    $pdo = new PDO($dsn, null, null, [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC
    ]);
    init_sqlite_schema($pdo);
}

function init_sqlite_schema($db) {
    $db->exec("
        CREATE TABLE IF NOT EXISTS employee (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT,
            login_id TEXT UNIQUE,
            password TEXT,
            auth_level INTEGER,
            status INTEGER DEFAULT 0,
            department TEXT DEFAULT 'Operations',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS visitors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT,
            person_to_visit TEXT,
            reason TEXT,
            has_vehicle INTEGER DEFAULT 0,
            vehicle_number TEXT,
            entry_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            exit_time TIMESTAMP,
            status INTEGER DEFAULT 1,
            denial_reason TEXT,
            id_type TEXT,
            id_number TEXT,
            badge_number TEXT,
            added_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS vehicle (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            driver_name TEXT,
            driver_phone TEXT,
            driver_id_type TEXT,
            driver_id_number TEXT,
            veh_reg_no TEXT,
            vehicle_img TEXT,
            origin TEXT,
            destination TEXT,
            purchase_no TEXT,
            entry_type TEXT DEFAULT 'Entry',
            gross_weight REAL,
            tare_weight REAL,
            material_type TEXT,
            is_returnable INTEGER DEFAULT 0,
            return_reason TEXT,
            vehicle_length TEXT,
            time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            exit_time TIMESTAMP,
            status TEXT DEFAULT 'Inside',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS whatsapp_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT NOT NULL,
            recipient TEXT,
            message TEXT,
            message_type TEXT NOT NULL,
            status TEXT DEFAULT 'sent',
            time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ");

    // Seed default admin if empty
    $check = $db->query("SELECT COUNT(*) as cnt FROM employee")->fetch();
    if ($check['cnt'] == 0) {
        $stmt = $db->prepare("INSERT INTO employee (name, login_id, phone, password, auth_level, status) VALUES (?, ?, ?, ?, ?, ?)");
        $stmt->execute(['Sanjai M S (Developer)', 'super', '9876543210', password_hash('password123', PASSWORD_DEFAULT), 5, 1]);
        $stmt->execute(['Rajesh Sharma', 'admin', '9845123456', password_hash('password123', PASSWORD_DEFAULT), 4, 1]);
        $stmt->execute(['Dr. Anita Desai', 'emp1', '9633445566', password_hash('password123', PASSWORD_DEFAULT), 3, 1]);
    }
}

function jsonResponse($data, $status = 200) {
    http_response_code($status);
    header('Content-Type: application/json');
    echo json_encode($data);
    exit();
}

function getJsonInput() {
    $raw = file_get_contents('php://input');
    return json_decode($raw, true) ?: $_POST;
}
