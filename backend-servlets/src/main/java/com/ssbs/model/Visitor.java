package com.ssbs.model;

import java.io.Serializable;
import java.sql.Timestamp;

public class Visitor implements Serializable {
    private static final long serialVersionUID = 1L;

    private Long id;
    private String name;
    private String phone;
    private String personToVisit;
    private String reason;
    private boolean hasVehicle;
    private String vehicleNumber;
    private Timestamp entryTime;
    private Timestamp exitTime;
    private int status; // 0: Pending, 1: Approved/Inside, 2: Checked Out, 3: Denied
    private String denialReason;
    private String idType;
    private String idNumber;
    private String badgeNumber;
    private String addedBy;
    private String department;

    public Visitor() {}

    // Getters and Setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public String getPhone() { return phone; }
    public void setPhone(String phone) { this.phone = phone; }

    public String getPersonToVisit() { return personToVisit; }
    public void setPersonToVisit(String personToVisit) { this.personToVisit = personToVisit; }

    public String getReason() { return reason; }
    public void setReason(String reason) { this.reason = reason; }

    public boolean isHasVehicle() { return hasVehicle; }
    public void setHasVehicle(boolean hasVehicle) { this.hasVehicle = hasVehicle; }

    public String getVehicleNumber() { return vehicleNumber; }
    public void setVehicleNumber(String vehicleNumber) { this.vehicleNumber = vehicleNumber; }

    public Timestamp getEntryTime() { return entryTime; }
    public void setEntryTime(Timestamp entryTime) { this.entryTime = entryTime; }

    public Timestamp getExitTime() { return exitTime; }
    public void setExitTime(Timestamp exitTime) { this.exitTime = exitTime; }

    public int getStatus() { return status; }
    public void setStatus(int status) { this.status = status; }

    public String getDenialReason() { return denialReason; }
    public void setDenialReason(String denialReason) { this.denialReason = denialReason; }

    public String getIdType() { return idType; }
    public void setIdType(String idType) { this.idType = idType; }

    public String getIdNumber() { return idNumber; }
    public void setIdNumber(String idNumber) { this.idNumber = idNumber; }

    public String getBadgeNumber() { return badgeNumber; }
    public void setBadgeNumber(String badgeNumber) { this.badgeNumber = badgeNumber; }

    public String getAddedBy() { return addedBy; }
    public void setAddedBy(String addedBy) { this.addedBy = addedBy; }

    public String getDepartment() { return department; }
    public void setDepartment(String department) { this.department = department; }
}
