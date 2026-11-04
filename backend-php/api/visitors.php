<?php
/**
 * SSBS PHP API - Visitor Management Endpoints
 */

require_once __DIR__ . '/../config/db.php';

$method = $_SERVER['REQUEST_METHOD'];
$action = $_GET['action'] ?? '';

// GET: Retrieve visitors with filter & search
if ($method === 'GET') {
    $search = $_GET['search'] ?? '';
    $status = $_GET['status'] ?? '';

    $sql = "SELECT * FROM visitors WHERE 1=1";
    $params = [];

    if ($search !== '') {
        $sql .= " AND (name LIKE ? OR phone LIKE ? OR badge_number LIKE ? OR person_to_visit LIKE ?)";
        $term = "%{$search}%";
        $params = array_merge($params, [$term, $term, $term, $term]);
    }

    if ($status !== '') {
        $sql .= " AND status = ?";
        $params[] = (int)$status;
    }

    $sql .= " ORDER BY id DESC LIMIT 100";
    $stmt = $pdo->prepare($sql);
    $stmt->execute($params);
    $visitors = $stmt->fetchAll();

    jsonResponse(['success' => true, 'count' => count($visitors), 'data' => $visitors]);
}

// POST: Actions (Check-in, Check-out, Approval)
if ($method === 'POST') {
    $input = getJsonInput();

    // Check-out Visitor
    if ($action === 'checkout') {
        $id = $input['id'] ?? $_GET['id'] ?? null;
        if (!$id) jsonResponse(['success' => false, 'message' => 'Visitor ID is required'], 400);

        $now = date('Y-m-d H:i:s');
        $stmt = $pdo->prepare("UPDATE visitors SET status = 2, exit_time = ? WHERE id = ?");
        $stmt->execute([$now, $id]);

        jsonResponse(['success' => true, 'message' => 'Visitor marked as checked out']);
    }

    // Approve / Reject Visitor
    if ($action === 'approval') {
        $id = $input['id'] ?? null;
        $status = $input['status'] ?? 1;
        $reason = $input['reason'] ?? null;

        $stmt = $pdo->prepare("UPDATE visitors SET status = ?, denial_reason = ? WHERE id = ?");
        $stmt->execute([(int)$status, $reason, $id]);

        jsonResponse(['success' => true, 'message' => 'Visitor approval status updated']);
    }

    // Create New Visitor Check-In
    $name = trim($input['name'] ?? '');
    $phone = trim($input['phone'] ?? '');
    $person = trim($input['person_to_visit'] ?? '');
    $reason = trim($input['reason'] ?? '');
    $hasVehicle = !empty($input['has_vehicle']) ? 1 : 0;
    $vehicleNum = trim($input['vehicle_number'] ?? '');
    $idType = trim($input['id_type'] ?? 'Aadhar');
    $idNum = trim($input['id_number'] ?? '');
    $badgeNumber = 'V-' . date('Y') . '-' . rand(1000, 9999);

    if (empty($name) || empty($phone) || empty($person)) {
        jsonResponse(['success' => false, 'message' => 'Missing required visitor fields'], 400);
    }

    $stmt = $pdo->prepare("
        INSERT INTO visitors (name, phone, person_to_visit, reason, has_vehicle, vehicle_number, id_type, id_number, badge_number, status, entry_time)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
    ");
    $stmt->execute([$name, $phone, $person, $reason, $hasVehicle, $vehicleNum, $idType, $idNum, $badgeNumber]);
    $newId = $pdo->lastInsertId();

    // Add notification to whatsapp_queue
    $q = $pdo->prepare("INSERT INTO whatsapp_queue (phone, recipient, message, message_type) VALUES (?, ?, ?, 'visitor_arrival')");
    $q->execute([$phone, $person, "SSBS Alert: Visitor {$name} has checked in to meet you."]);

    jsonResponse([
        'success' => true,
        'message' => 'Visitor registered successfully',
        'data' => [
            'id' => $newId,
            'name' => $name,
            'badge_number' => $badgeNumber
        ]
    ], 201);
}

jsonResponse(['error' => 'Method not allowed'], 405);
