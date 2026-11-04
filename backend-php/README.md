# SSBS Visitor & Logistics Management System - PHP Backend

This is the PHP backend replica for the SSBS Visitor & Logistics Management System. It exposes RESTful API endpoints for the HTML5/CSS3/JavaScript frontend and supports database operations using PDO with MySQL/MariaDB and automatic SQLite fallback.

## Requirements
- PHP 8.0 or higher
- PDO extension (`pdo_mysql` or `pdo_sqlite`)
- MySQL 5.7+ / MariaDB 10.3+ (Optional, SQLite works out of the box)

## Setup & Running

### Option 1: Quick Built-in PHP Server (Zero Setup)
```bash
cd backend-php
php -S localhost:8000
```
This automatically initializes `database.sqlite` with the complete schema and seed credentials!

### Option 2: Apache / XAMPP / WAMP
1. Place the `backend-php` directory into your `htdocs` or `www` directory.
2. Import `sql/schema.sql` into your MySQL server via phpMyAdmin or MySQL CLI:
   ```bash
   mysql -u root -p < sql/schema.sql
   ```
3. Set your environment variables in Apache `.htaccess` or environment:
   ```env
   DB_HOST=localhost
   DB_NAME=ssbs_vms
   DB_USER=root
   DB_PASS=
   ```

## API Endpoints Reference

### Authentication
- `POST /api/auth.php?action=login` - Authenticate user credentials
- `POST /api/auth.php?action=logout` - End current session
- `GET  /api/auth.php?action=me` - Retrieve authenticated user profile

### Visitors
- `GET  /api/visitors.php?search=&status=` - List visitor entries
- `POST /api/visitors.php` - Register new visitor and dispatch WhatsApp alert
- `POST /api/visitors.php?action=checkout` - Mark visitor as checked out
- `POST /api/visitors.php?action=approval` - Host approve/decline visitor

### Logistics
- `GET  /api/logistics.php?search=&status=` - List vehicle consignments
- `POST /api/logistics.php` - Inbound vehicle registration
- `POST /api/logistics.php?action=exit` - Outbound vehicle clearance & tare weight

### Staff & Users
- `GET  /api/employees.php?search=&role=&status=` - Employee directory
- `POST /api/employees.php` - Provision new employee
- `POST /api/employees.php?action=toggle` - Toggle online/offline status
- `POST /api/employees.php?action=delete` - Delete employee record
