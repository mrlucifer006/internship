# SSBS Visitor & Logistics Management System - Java Servlets Backend

This is the Java Servlets Enterprise implementation for the SSBS Visitor & Logistics Management System. It uses standard Java EE / Jakarta Servlet specifications, JDBC DAO design patterns, Gson serialization, and CORS filters.

## Project Structure
```
backend-servlets/
  ├── pom.xml
  ├── README.md
  └── src/main/
      ├── java/com/ssbs/
      │   ├── model/ (Employee, Visitor, Vehicle)
      │   ├── dao/   (DBUtil, EmployeeDAO, VisitorDAO, VehicleDAO)
      │   ├── servlet/ (AuthServlet, VisitorServlet, LogisticsServlet, EmployeeServlet)
      │   └── filter/  (CorsFilter)
      └── webapp/
          └── WEB-INF/
              └── web.xml
```

## Requirements
- Java Development Kit (JDK) 11 or higher
- Apache Maven 3.6+
- Apache Tomcat 9 or 10

## Build & Deployment

### 1. Build WAR Package with Maven
```bash
cd backend-servlets
mvn clean package
```
This generates `target/ssbs-vms.war`.

### 2. Run on Apache Tomcat
Copy `target/ssbs-vms.war` to your Tomcat `webapps/` folder:
```bash
cp target/ssbs-vms.war /path/to/apache-tomcat/webapps/
```
Start Tomcat (`./bin/startup.sh` or `startup.bat`).
The Servlets will be accessible at:
`http://localhost:8080/ssbs-vms/api/...`

### Database Configuration
By default, the Servlets connect to MySQL if available, or automatically fall back to an embedded SQLite database (`ssbs_database.sqlite`).
To specify custom database credentials, configure environment variables:
- `DB_HOST`: Hostname (default: `localhost`)
- `DB_PORT`: Port (default: `3306`)
- `DB_NAME`: Database name (default: `ssbs_vms`)
- `DB_USER`: User (default: `root`)
- `DB_PASS`: Password (default: empty)
