<?php
/**
 * SSBS PHP API - Employee & Staff Management Endpoints
 */

require_once __DIR__ . '/../config/db.php';

$method = $_SERVER['REQUEST_METHOD'];
$action = $_GET['action'] ?? '';

// GET: List employees
if ($method === 'GET') {
    $search = $_GET['search'] ?? '';
    $role = $_GET['role'] ?? '';
    $status = $_GET['status'] ?? '';

    $sql = "SELECT id, name, login_id, phone, auth_level, status, department, created_at FROM employee WHERE 1=1";
    $params = [];

    if ($search !== '') {
        $sql .= " AND (name LIKE ? OR login_id LIKE ? OR phone LIKE ?)";
        $term = "%{$search}%";
        $params = array_merge($params, [$term, $term, $term]);
    }

    if ($role !== '') {
        $sql .= " AND auth_level = ?";
        $params[] = (int)$role;
    }

    if ($status !== '') {
        $sql .= " AND status = ?";
        $params[] = (int)$status;
    }

    $sql .= " ORDER BY auth_level DESC, name ASC";
    $stmt = $pdo->prepare($sql);
    $stmt->execute($params);
    $employees = $stmt->fetchAll();

    $roles = [1 => 'Foreman', 2 => 'Supervisor', 3 => 'Employee', 4 => 'Admin', 5 => 'Developer'];
    foreach ($employees as &$emp) {
        $emp['role_name'] = $roles[$emp['auth_level']] ?? 'User';
    }

    jsonResponse(['success' => true, 'count' => count($employees), 'data' => $employees]);
}

// POST: Add, toggle, delete
if ($method === 'POST') {
    $input = getJsonInput();

    // Toggle Online/Offline
    if ($action === 'toggle') {
        $loginId = $input['login_id'] ?? $_GET['login_id'] ?? null;
        if (!$loginId) jsonResponse(['success' => false, 'message' => 'Login ID required'], 400);

        $stmt = $pdo->prepare("UPDATE employee SET status = CASE WHEN status = 1 THEN 0 ELSE 1 END WHERE login_id = ?");
        $stmt->execute([$loginId]);

        jsonResponse(['success' => true, 'message' => 'Status toggled']);
    }

    // Delete Employee
    if ($action === 'delete') {
        $loginId = $input['login_id'] ?? $_GET['login_id'] ?? null;
        if ($loginId === 'super') jsonResponse(['success' => false, 'message' => 'Cannot delete root super developer'], 403);

        $stmt = $pdo->prepare("DELETE FROM employee WHERE login_id = ?");
        $stmt->execute([$loginId]);

        jsonResponse(['success' => true, 'message' => 'Employee deleted']);
    }

    // Add New Employee
    $name = trim($input['name'] ?? '');
    $loginId = trim($input['login_id'] ?? '');
    $phone = trim($input['phone'] ?? '');
    $password = trim($input['password'] ?? 'password123');
    $authLevel = (int)($input['auth_level'] ?? 3);
    $dept = trim($input['department'] ?? 'Operations');

    if (empty($name) || empty($loginId) || empty($phone)) {
        jsonResponse(['success' => false, 'message' => 'All employee fields required'], 400);
    }

    // Check duplicate
    $check = $pdo->prepare("SELECT id FROM employee WHERE login_id = ?");
    $check->execute([$loginId]);
    if ($check->fetch()) {
        jsonResponse(['success' => false, 'message' => "Login ID {$loginId} already exists"], 409);
    }

    $hash = password_hash($password, PASSWORD_DEFAULT);
    $stmt = $pdo->prepare("INSERT INTO employee (name, login_id, phone, password, auth_level, department, status) VALUES (?, ?, ?, ?, ?, ?, 0)");
    $stmt->execute([$name, $loginId, $phone, $hash, $authLevel, $dept]);

    jsonResponse(['success' => true, 'message' => 'Employee added successfully', 'id' => $pdo->lastInsertId()], 201);
}

jsonResponse(['error' => 'Method not allowed'], 405);
