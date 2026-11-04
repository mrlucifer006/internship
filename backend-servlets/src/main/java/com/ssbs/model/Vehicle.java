package com.ssbs.model;

import java.io.Serializable;
import java.sql.Timestamp;

public class Vehicle implements Serializable {
    private static final long serialVersionUID = 1L;

    private Long id;
    private String driverName;
    private String driverPhone;
    private String driverIdType;
    private String driverIdNumber;
    private String vehRegNo;
    private String vehicleImg;
    private String origin;
    private String destination;
    private String purchaseNo;
    private String entryType;
    private double grossWeight;
    private Double tareWeight;
    private Double netWeight;
    private String materialType;
    private int isReturnable;
    private String returnReason;
    private String vehicleLength;
    private Timestamp time;
    private Timestamp exitTime;
    private String status;

    public Vehicle() {}

    // Getters and Setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getDriverName() { return driverName; }
    public void setDriverName(String driverName) { this.driverName = driverName; }

    public String getDriverPhone() { return driverPhone; }
    public void setDriverPhone(String driverPhone) { this.driverPhone = driverPhone; }

    public String getDriverIdType() { return driverIdType; }
    public void setDriverIdType(String driverIdType) { this.driverIdType = driverIdType; }

    public String getDriverIdNumber() { return driverIdNumber; }
    public void setDriverIdNumber(String driverIdNumber) { this.driverIdNumber = driverIdNumber; }

    public String getVehRegNo() { return vehRegNo; }
    public void setVehRegNo(String vehRegNo) { this.vehRegNo = vehRegNo; }

    public String getVehicleImg() { return vehicleImg; }
    public void setVehicleImg(String vehicleImg) { this.vehicleImg = vehicleImg; }

    public String getOrigin() { return origin; }
    public void setOrigin(String origin) { this.origin = origin; }

    public String getDestination() { return destination; }
    public void setDestination(String destination) { this.destination = destination; }

    public String getPurchaseNo() { return purchaseNo; }
    public void setPurchaseNo(String purchaseNo) { this.purchaseNo = purchaseNo; }

    public String getEntryType() { return entryType; }
    public void setEntryType(String entryType) { this.entryType = entryType; }

    public double getGrossWeight() { return grossWeight; }
    public void setGrossWeight(double grossWeight) { this.grossWeight = grossWeight; }

    public Double getTareWeight() { return tareWeight; }
    public void setTareWeight(Double tareWeight) { 
        this.tareWeight = tareWeight; 
        if (tareWeight != null) {
            this.netWeight = Math.max(0, this.grossWeight - tareWeight);
        }
    }

    public Double getNetWeight() { return netWeight; }
    public void setNetWeight(Double netWeight) { this.netWeight = netWeight; }

    public String getMaterialType() { return materialType; }
    public void setMaterialType(String materialType) { this.materialType = materialType; }

    public int getIsReturnable() { return isReturnable; }
    public void setIsReturnable(int isReturnable) { this.isReturnable = isReturnable; }

    public String getReturnReason() { return returnReason; }
    public void setReturnReason(String returnReason) { this.returnReason = returnReason; }

    public String getVehicleLength() { return vehicleLength; }
    public void setVehicleLength(String vehicleLength) { this.vehicleLength = vehicleLength; }

    public Timestamp getTime() { return time; }
    public void setTime(Timestamp time) { this.time = time; }

    public Timestamp getExitTime() { return exitTime; }
    public void setExitTime(Timestamp exitTime) { this.exitTime = exitTime; }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
}
