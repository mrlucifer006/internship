package com.ssbs.dao;

import com.ssbs.model.Vehicle;
import java.sql.*;
import java.util.ArrayList;
import java.util.List;

public class VehicleDAO {

    public List<Vehicle> getVehicles(String search, String status) throws SQLException {
        List<Vehicle> list = new ArrayList<>();
        StringBuilder sql = new StringBuilder("SELECT * FROM vehicle WHERE 1=1");
        List<Object> params = new ArrayList<>();

        if (search != null && !search.trim().isEmpty()) {
            sql.append(" AND (veh_reg_no LIKE ? OR driver_name LIKE ? OR origin LIKE ? OR purchase_no LIKE ?)");
            String term = "%" + search.trim() + "%";
            params.add(term);
            params.add(term);
            params.add(term);
            params.add(term);
        }

        if (status != null && !status.trim().isEmpty()) {
            sql.append(" AND status = ?");
            params.add(status.trim());
        }

        sql.append(" ORDER BY id DESC LIMIT 100");

        try (Connection conn = DBUtil.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql.toString())) {
            for (int i = 0; i < params.size(); i++) {
                ps.setObject(i + 1, params.get(i));
            }
            try (ResultSet rs = ps.executeQuery()) {
                while (rs.next()) {
                    Vehicle v = new Vehicle();
                    v.setId(rs.getLong("id"));
                    v.setDriverName(rs.getString("driver_name"));
                    v.setDriverPhone(rs.getString("driver_phone"));
                    v.setDriverIdType(rs.getString("driver_id_type"));
                    v.setDriverIdNumber(rs.getString("driver_id_number"));
                    v.setVehRegNo(rs.getString("veh_reg_no"));
                    v.setOrigin(rs.getString("origin"));
                    v.setDestination(rs.getString("destination"));
                    v.setPurchaseNo(rs.getString("purchase_no"));
                    v.setGrossWeight(rs.getDouble("gross_weight"));
                    double tare = rs.getDouble("tare_weight");
                    if (!rs.wasNull()) v.setTareWeight(tare);
                    v.setMaterialType(rs.getString("material_type"));
                    v.setIsReturnable(rs.getInt("is_returnable"));
                    v.setReturnReason(rs.getString("return_reason"));
                    v.setVehicleLength(rs.getString("vehicle_length"));
                    v.setTime(rs.getTimestamp("time"));
                    v.setExitTime(rs.getTimestamp("exit_time"));
                    v.setStatus(rs.getString("status"));
                    list.add(v);
                }
            }
        }
        return list;
    }

    public boolean addVehicleEntry(Vehicle v) throws SQLException {
        String sql = "INSERT INTO vehicle (driver_name, driver_phone, driver_id_type, driver_id_number, veh_reg_no, origin, destination, purchase_no, material_type, gross_weight, is_returnable, return_reason, vehicle_length, status, time) " +
                     "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Inside', CURRENT_TIMESTAMP)";
        try (Connection conn = DBUtil.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql, Statement.RETURN_GENERATED_KEYS)) {
            ps.setString(1, v.getDriverName());
            ps.setString(2, v.getDriverPhone());
            ps.setString(3, v.getDriverIdType());
            ps.setString(4, v.getDriverIdNumber());
            ps.setString(5, v.getVehRegNo().toUpperCase());
            ps.setString(6, v.getOrigin());
            ps.setString(7, v.getDestination());
            ps.setString(8, v.getPurchaseNo());
            ps.setString(9, v.getMaterialType());
            ps.setDouble(10, v.getGrossWeight());
            ps.setInt(11, v.getIsReturnable());
            ps.setString(12, v.getReturnReason());
            ps.setString(13, v.getVehicleLength());
            return ps.executeUpdate() > 0;
        }
    }

    public boolean processExit(long id, double tareWeight) throws SQLException {
        String sql = "UPDATE vehicle SET status = 'Exited', tare_weight = ?, exit_time = CURRENT_TIMESTAMP WHERE id = ?";
        try (Connection conn = DBUtil.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setDouble(1, tareWeight);
            ps.setLong(2, id);
            return ps.executeUpdate() > 0;
        }
    }
}
