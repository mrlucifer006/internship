package com.ssbs.model;

import java.io.Serializable;
import java.sql.Timestamp;

public class Employee implements Serializable {
    private static final long serialVersionUID = 1L;

    private Long id;
    private String name;
    private String phone;
    private String loginId;
    private String password;
    private int authLevel;
    private int status;
    private String department;
    private String roleName;
    private Timestamp createdAt;

    public Employee() {}

    public Employee(Long id, String name, String phone, String loginId, int authLevel, int status, String department) {
        this.id = id;
        this.name = name;
        this.phone = phone;
        this.loginId = loginId;
        this.authLevel = authLevel;
        this.status = status;
        this.department = department;
        this.roleName = resolveRoleName(authLevel);
    }

    public static String resolveRoleName(int level) {
        switch (level) {
            case 5: return "Developer";
            case 4: return "Admin";
            case 3: return "Employee";
            case 2: return "Supervisor";
            case 1: return "Foreman";
            default: return "User";
        }
    }

    // Getters and Setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public String getPhone() { return phone; }
    public void setPhone(String phone) { this.phone = phone; }

    public String getLoginId() { return loginId; }
    public void setLoginId(String loginId) { this.loginId = loginId; }

    public String getPassword() { return password; }
    public void setPassword(String password) { this.password = password; }

    public int getAuthLevel() { return authLevel; }
    public void setAuthLevel(int authLevel) { 
        this.authLevel = authLevel; 
        this.roleName = resolveRoleName(authLevel);
    }

    public int getStatus() { return status; }
    public void setStatus(int status) { this.status = status; }

    public String getDepartment() { return department; }
    public void setDepartment(String department) { this.department = department; }

    public String getRoleName() { return roleName; }
    public void setRoleName(String roleName) { this.roleName = roleName; }

    public Timestamp getCreatedAt() { return createdAt; }
    public void setCreatedAt(Timestamp createdAt) { this.createdAt = createdAt; }
}
