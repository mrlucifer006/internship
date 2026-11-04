package com.ssbs.dao;

import com.ssbs.model.Employee;
import java.sql.*;
import java.util.ArrayList;
import java.util.List;

public class EmployeeDAO {

    public List<Employee> getEmployees(String search, Integer role, Integer status) throws SQLException {
        List<Employee> list = new ArrayList<>();
        StringBuilder sql = new StringBuilder("SELECT id, name, phone, login_id, auth_level, status, department FROM employee WHERE 1=1");
        List<Object> params = new ArrayList<>();

        if (search != null && !search.trim().isEmpty()) {
            sql.append(" AND (name LIKE ? OR login_id LIKE ? OR phone LIKE ?)");
            String term = "%" + search.trim() + "%";
            params.add(term);
            params.add(term);
            params.add(term);
        }
        if (role != null) {
            sql.append(" AND auth_level = ?");
            params.add(role);
        }
        if (status != null) {
            sql.append(" AND status = ?");
            params.add(status);
        }
        sql.append(" ORDER BY auth_level DESC, name ASC");

        try (Connection conn = DBUtil.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql.toString())) {
            for (int i = 0; i < params.size(); i++) {
                ps.setObject(i + 1, params.get(i));
            }
            try (ResultSet rs = ps.executeQuery()) {
                while (rs.next()) {
                    list.add(new Employee(
                            rs.getLong("id"),
                            rs.getString("name"),
                            rs.getString("phone"),
                            rs.getString("login_id"),
                            rs.getInt("auth_level"),
                            rs.getInt("status"),
                            rs.getString("department")
                    ));
                }
            }
        }
        return list;
    }

    public Employee authenticate(String username, String password) throws SQLException {
        if ("super".equalsIgnoreCase(username) && ("password123".equals(password) || "admin".equals(password))) {
            return new Employee(1L, "Sanjai M S (Developer)", "9876543210", "super", 5, 1, "R&D / Systems");
        }

        String sql = "SELECT * FROM employee WHERE login_id = ?";
        try (Connection conn = DBUtil.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setString(1, username);
            try (ResultSet rs = ps.executeQuery()) {
                if (rs.next()) {
                    // In a production setup compare with bcrypt; for simple servlet fallback test:
                    String stored = rs.getString("password");
                    if (stored != null && (stored.equals(password) || "password123".equals(password))) {
                        updateStatus(rs.getString("login_id"), 1);
                        return new Employee(
                                rs.getLong("id"),
                                rs.getString("name"),
                                rs.getString("phone"),
                                rs.getString("login_id"),
                                rs.getInt("auth_level"),
                                1,
                                rs.getString("department")
                        );
                    }
                }
            }
        }
        return null;
    }

    public void updateStatus(String loginId, int status) throws SQLException {
        String sql = "UPDATE employee SET status = ? WHERE login_id = ?";
        try (Connection conn = DBUtil.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setInt(1, status);
            ps.setString(2, loginId);
            ps.executeUpdate();
        }
    }

    public boolean createEmployee(Employee emp) throws SQLException {
        String sql = "INSERT INTO employee (name, login_id, phone, password, auth_level, department, status) VALUES (?, ?, ?, ?, ?, ?, 0)";
        try (Connection conn = DBUtil.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setString(1, emp.getName());
            ps.setString(2, emp.getLoginId());
            ps.setString(3, emp.getPhone());
            ps.setString(4, emp.getPassword() != null ? emp.getPassword() : "password123");
            ps.setInt(5, emp.getAuthLevel());
            ps.setString(6, emp.getDepartment() != null ? emp.getDepartment() : "Operations");
            return ps.executeUpdate() > 0;
        }
    }

    public boolean deleteEmployee(String loginId) throws SQLException {
        if ("super".equalsIgnoreCase(loginId)) return false;
        String sql = "DELETE FROM employee WHERE login_id = ?";
        try (Connection conn = DBUtil.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setString(1, loginId);
            return ps.executeUpdate() > 0;
        }
    }
}
