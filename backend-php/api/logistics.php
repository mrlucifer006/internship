<?php
/**
 * SSBS PHP API - Logistics Operations Handler
 */

require_once __DIR__ . '/../config/db.php';

$method = $_SERVER['REQUEST_METHOD'];
$action = $_GET['action'] ?? '';

// GET: Retrieve vehicles
if ($method === 'GET') {
    $search = $_GET['search'] ?? '';
    $status = $_GET['status'] ?? '';

    $sql = "SELECT * FROM vehicle WHERE 1=1";
    $params = [];

    if ($search !== '') {
        $sql .= " AND (veh_reg_no LIKE ? OR driver_name LIKE ? OR origin LIKE ? OR purchase_no LIKE ?)";
        $term = "%{$search}%";
        $params = array_merge($params, [$term, $term, $term, $term]);
    }

    if ($status !== '') {
        $sql .= " AND status = ?";
        $params[] = $status;
    }

    $sql .= " ORDER BY id DESC LIMIT 100";
    $stmt = $pdo->prepare($sql);
    $stmt->execute($params);
    $vehicles = $stmt->fetchAll();

    jsonResponse(['success' => true, 'count' => count($vehicles), 'data' => $vehicles]);
}

// POST: Actions
if ($method === 'POST') {
    $input = getJsonInput();

    // Vehicle Exit Clearance
    if ($action === 'exit') {
        $id = $input['id'] ?? null;
        $tare = (float)($input['tare_weight'] ?? 0);
        if (!$id) jsonResponse(['success' => false, 'message' => 'Vehicle ID required'], 400);

        $now = date('Y-m-d H:i:s');
        $stmt = $pdo->prepare("UPDATE vehicle SET status = 'Exited', tare_weight = ?, exit_time = ? WHERE id = ?");
        $stmt->execute([$tare, $now, $id]);

        jsonResponse(['success' => true, 'message' => 'Vehicle clearance completed and exited']);
    }

    // Vehicle Inbound Entry
    $driverName = trim($input['driver_name'] ?? '');
    $driverPhone = trim($input['driver_phone'] ?? '');
    $idType = trim($input['driver_id_type'] ?? 'Driving License');
    $idNumber = trim($input['driver_id_number'] ?? '');
    $vehRegNo = strtoupper(trim($input['veh_reg_no'] ?? ''));
    $origin = trim($input['origin'] ?? '');
    $dest = trim($input['destination'] ?? '');
    $poNo = trim($input['purchase_no'] ?? '');
    $material = trim($input['material_type'] ?? '');
    $grossWeight = (float)($input['gross_weight'] ?? 0);
    $isReturnable = !empty($input['is_returnable']) ? 1 : 0;
    $returnReason = trim($input['return_reason'] ?? '');
    $vehLength = trim($input['vehicle_length'] ?? 'Heavy 10-Wheeler');

    if (empty($driverName) || empty($vehRegNo) || empty($origin)) {
        jsonResponse(['success' => false, 'message' => 'Missing required logistics vehicle fields'], 400);
    }

    $stmt = $pdo->prepare("
        INSERT INTO vehicle (driver_name, driver_phone, driver_id_type, driver_id_number, veh_reg_no, origin, destination, purchase_no, material_type, gross_weight, is_returnable, return_reason, vehicle_length, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Inside')
    ");
    $stmt->execute([$driverName, $driverPhone, $idType, $idNumber, $vehRegNo, $origin, $dest, $poNo, $material, $grossWeight, $isReturnable, $returnReason, $vehLength]);
    $newId = $pdo->lastInsertId();

    jsonResponse(['success' => true, 'message' => 'Vehicle entry recorded', 'id' => $newId], 201);
}

jsonResponse(['error' => 'Method not allowed'], 405);
