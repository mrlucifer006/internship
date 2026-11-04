package com.ssbs.dao;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;
import java.sql.Statement;

public class DBUtil {
    private static final String MYSQL_HOST = System.getenv("DB_HOST") != null ? System.getenv("DB_HOST") : "localhost";
    private static final String MYSQL_PORT = System.getenv("DB_PORT") != null ? System.getenv("DB_PORT") : "3306";
    private static final String MYSQL_DB = System.getenv("DB_NAME") != null ? System.getenv("DB_NAME") : "ssbs_vms";
    private static final String MYSQL_USER = System.getenv("DB_USER") != null ? System.getenv("DB_USER") : "root";
    private static final String MYSQL_PASS = System.getenv("DB_PASS") != null ? System.getenv("DB_PASS") : "";

    private static final String MYSQL_URL = "jdbc:mysql://" + MYSQL_HOST + ":" + MYSQL_PORT + "/" + MYSQL_DB + "?useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=UTC";
    private static final String SQLITE_URL = "jdbc:sqlite:ssbs_database.sqlite";

    private static boolean useSqliteFallback = false;

    static {
        try {
            Class.forName("com.mysql.cj.jdbc.Driver");
        } catch (ClassNotFoundException e) {
            try {
                Class.forName("org.sqlite.JDBC");
                useSqliteFallback = true;
            } catch (ClassNotFoundException ex) {
                System.err.println("No JDBC Driver found: " + ex.getMessage());
            }
        }
    }

    public static Connection getConnection() throws SQLException {
        if (!useSqliteFallback) {
            try {
                return DriverManager.getConnection(MYSQL_URL, MYSQL_USER, MYSQL_PASS);
            } catch (SQLException ex) {
                // Fallback to SQLite
                useSqliteFallback = true;
                return getSqliteConnection();
            }
        } else {
            return getSqliteConnection();
        }
    }

    private static Connection getSqliteConnection() throws SQLException {
        Connection conn = DriverManager.getConnection(SQLITE_URL);
        initSqliteSchema(conn);
        return conn;
    }

    private static void initSqliteSchema(Connection conn) {
        try (Statement stmt = conn.createStatement()) {
            stmt.executeUpdate("CREATE TABLE IF NOT EXISTS employee (" +
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, " +
                    "name TEXT, phone TEXT, login_id TEXT UNIQUE, password TEXT, " +
                    "auth_level INTEGER, status INTEGER DEFAULT 0, department TEXT, " +
                    "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)");

            stmt.executeUpdate("CREATE TABLE IF NOT EXISTS visitors (" +
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, " +
                    "name TEXT, phone TEXT, person_to_visit TEXT, reason TEXT, " +
                    "has_vehicle INTEGER DEFAULT 0, vehicle_number TEXT, " +
                    "entry_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP, exit_time TIMESTAMP, " +
                    "status INTEGER DEFAULT 1, denial_reason TEXT, id_type TEXT, " +
                    "id_number TEXT, badge_number TEXT, added_by TEXT, department TEXT)");

            stmt.executeUpdate("CREATE TABLE IF NOT EXISTS vehicle (" +
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, " +
                    "driver_name TEXT, driver_phone TEXT, driver_id_type TEXT, " +
                    "driver_id_number TEXT, veh_reg_no TEXT, vehicle_img TEXT, " +
                    "origin TEXT, destination TEXT, purchase_no TEXT, entry_type TEXT DEFAULT 'Entry', " +
                    "gross_weight REAL, tare_weight REAL, material_type TEXT, " +
                    "is_returnable INTEGER DEFAULT 0, return_reason TEXT, vehicle_length TEXT, " +
                    "time TIMESTAMP DEFAULT CURRENT_TIMESTAMP, exit_time TIMESTAMP, status TEXT DEFAULT 'Inside')");
        } catch (SQLException ignored) {}
    }
}
