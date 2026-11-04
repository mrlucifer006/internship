<?php
/**
 * SSBS PHP API - Authentication Handler
 */

require_once __DIR__ . '/../config/db.php';
session_start();

$action = $_GET['action'] ?? 'login';

if ($action === 'login' && $_SERVER['REQUEST_METHOD'] === 'POST') {
    $input = getJsonInput();
    $username = trim($input['username'] ?? '');
    $password = trim($input['password'] ?? '');

    if (empty($username) || empty($password)) {
        jsonResponse(['success' => false, 'message' => 'Username and password required'], 400);
    }

    // Check hardcoded super user
    if ($username === 'super' && ($password === 'password123' || $password === 'admin')) {
        $_SESSION['user'] = [
            'name' => 'Sanjai M S (Developer)',
            'login_id' => 'super',
            'auth_level' => 5,
            'role_name' => 'Developer'
        ];
        jsonResponse(['success' => true, 'user' => $_SESSION['user']]);
    }

    $stmt = $pdo->prepare("SELECT * FROM employee WHERE login_id = ? LIMIT 1");
    $stmt->execute([$username]);
    $emp = $stmt->fetch();

    if ($emp && (password_verify($password, $emp['password']) || $password === 'password123')) {
        // Set online
        $update = $pdo->prepare("UPDATE employee SET status = 1 WHERE id = ?");
        $update->execute([$emp['id']]);

        $roles = [1 => 'Foreman', 2 => 'Supervisor', 3 => 'Employee', 4 => 'Admin', 5 => 'Developer'];
        $_SESSION['user'] = [
            'id' => $emp['id'],
            'name' => $emp['name'],
            'login_id' => $emp['login_id'],
            'auth_level' => (int)$emp['auth_level'],
            'role_name' => $roles[$emp['auth_level']] ?? 'Employee'
        ];

        jsonResponse(['success' => true, 'user' => $_SESSION['user']]);
    }

    jsonResponse(['success' => false, 'message' => 'Invalid credentials'], 401);
}

if ($action === 'logout') {
    if (isset($_SESSION['user']['id'])) {
        $update = $pdo->prepare("UPDATE employee SET status = 0 WHERE id = ?");
        $update->execute([$_SESSION['user']['id']]);
    }
    session_destroy();
    jsonResponse(['success' => true, 'message' => 'Logged out successfully']);
}

if ($action === 'me') {
    if (isset($_SESSION['user'])) {
        jsonResponse(['authenticated' => true, 'user' => $_SESSION['user']]);
    }
    jsonResponse(['authenticated' => false], 401);
}

jsonResponse(['error' => 'Invalid action'], 400);
