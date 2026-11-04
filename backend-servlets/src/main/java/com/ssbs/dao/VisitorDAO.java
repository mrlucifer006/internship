package com.ssbs.dao;

import com.ssbs.model.Visitor;
import java.sql.*;
import java.util.ArrayList;
import java.util.List;

public class VisitorDAO {

    public List<Visitor> getVisitors(String search, Integer status) throws SQLException {
        List<Visitor> list = new ArrayList<>();
        StringBuilder sql = new StringBuilder("SELECT * FROM visitors WHERE 1=1");
        List<Object> params = new ArrayList<>();

        if (search != null && !search.trim().isEmpty()) {
            sql.append(" AND (name LIKE ? OR phone LIKE ? OR badge_number LIKE ? OR person_to_visit LIKE ?)");
            String term = "%" + search.trim() + "%";
            params.add(term);
            params.add(term);
            params.add(term);
            params.add(term);
        }

        if (status != null) {
            sql.append(" AND status = ?");
            params.add(status);
        }

        sql.append(" ORDER BY id DESC LIMIT 100");

        try (Connection conn = DBUtil.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql.toString())) {
            for (int i = 0; i < params.size(); i++) {
                ps.setObject(i + 1, params.get(i));
            }
            try (ResultSet rs = ps.executeQuery()) {
                while (rs.next()) {
                    Visitor v = new Visitor();
                    v.setId(rs.getLong("id"));
                    v.setName(rs.getString("name"));
                    v.setPhone(rs.getString("phone"));
                    v.setPersonToVisit(rs.getString("person_to_visit"));
                    v.setReason(rs.getString("reason"));
                    v.setHasVehicle(rs.getInt("has_vehicle") == 1);
                    v.setVehicleNumber(rs.getString("vehicle_number"));
                    v.setEntryTime(rs.getTimestamp("entry_time"));
                    v.setExitTime(rs.getTimestamp("exit_time"));
                    v.setStatus(rs.getInt("status"));
                    v.setDenialReason(rs.getString("denial_reason"));
                    v.setIdType(rs.getString("id_type"));
                    v.setIdNumber(rs.getString("id_number"));
                    v.setBadgeNumber(rs.getString("badge_number"));
                    v.setDepartment(rs.getString("department"));
                    list.add(v);
                }
            }
        }
        return list;
    }

    public boolean addVisitor(Visitor v) throws SQLException {
        String sql = "INSERT INTO visitors (name, phone, person_to_visit, reason, has_vehicle, vehicle_number, id_type, id_number, badge_number, status, entry_time) " +
                     "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)";
        try (Connection conn = DBUtil.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql, Statement.RETURN_GENERATED_KEYS)) {
            ps.setString(1, v.getName());
            ps.setString(2, v.getPhone());
            ps.setString(3, v.getPersonToVisit());
            ps.setString(4, v.getReason());
            ps.setInt(5, v.isHasVehicle() ? 1 : 0);
            ps.setString(6, v.getVehicleNumber());
            ps.setString(7, v.getIdType());
            ps.setString(8, v.getIdNumber());
            ps.setString(9, v.getBadgeNumber());
            int affected = ps.executeUpdate();
            if (affected > 0) {
                try (ResultSet keys = ps.getGeneratedKeys()) {
                    if (keys.next()) v.setId(keys.getLong(1));
                }
                return true;
            }
        }
        return false;
    }

    public boolean checkOutVisitor(long visitorId) throws SQLException {
        String sql = "UPDATE visitors SET status = 2, exit_time = CURRENT_TIMESTAMP WHERE id = ?";
        try (Connection conn = DBUtil.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setLong(1, visitorId);
            return ps.executeUpdate() > 0;
        }
    }
}
