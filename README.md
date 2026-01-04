# Visitor Management System

A comprehensive web-based visitor management system built with Flask for managing visitors, employees, and logistics operations.

## Features

- **Visitor Management**: Track visitor check-ins and check-outs with approval workflows
- **Employee Management**: User authentication with role-based access control (5 authority levels)
- **Logistics Tracking**: Vehicle entry and exit management with photo uploads
- **Real-time Notifications**: WhatsApp integration for offline hosts and logistics updates
- **Status Monitoring**: Live employee status tracking and visitor approval system
- **Secure Authentication**: Password hashing with bcrypt and session management

## Quick Start

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- WhatsApp Web logged in (for notifications)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd demo_internship
   ```

2. **Create virtual environment** (recommended)
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   # Copy the example environment file
   copy .env.example .env  # Windows
   cp .env.example .env    # Linux/Mac
   
   # Edit .env and set your configuration
   ```

   **Required Environment Variables**:
   - `SECRET_KEY`: Flask session secret (generate with `python -c "import secrets; print(secrets.token_hex(32))"`)
   - `LOGISTICS_PHONE_NUMBER`: Phone number for logistics notifications (format: +919XXXXXXXXX)

5. **Initialize the database**
   ```bash
   python app.py
   ```
   The application will automatically create required database tables on first run.

6. **Access the application**
   - Open your browser to `http://localhost:5000`
   - Default credentials:
     - **Username**: `super`
     - **Password**: `password123`
     - **Role**: Developer (Level 5)

## Configuration

All configuration is managed through environment variables in the `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key for sessions | Auto-generated (⚠️ Set for production!) |
| `FLASK_ENV` | Environment (development/production) | development |
| `HOST` | Server host | 0.0.0.0 |
| `PORT` | Server port | 5000 |
| `DEBUG` | Enable debug mode | False |
| `LOG_LEVEL` | Logging level (DEBUG/INFO/WARNING/ERROR) | INFO |
| `LOG_FILE` | Log file path | app.log |
| `SESSION_LIFETIME_HOURS` | Session timeout in hours | 24 |
| `LOGISTICS_PHONE_NUMBER` | WhatsApp number for logistics | (empty) |

## User Roles & Permissions

| Level | Role | Permissions |
|-------|------|-------------|
| 1 | Foreman | Basic visitor entry |
| 2 | Supervisor | Visitor management |
| 3 | Employee | Host capabilities, notifications |
| 4 | Admin | All features + user management + reports |
| 5 | Developer | Full system access |

## Usage

### Adding New Users

1. Log in as Admin (Level 4+)
2. Navigate to "Add New User"
3. Fill in details and set authority level
4. New users can log in immediately with hashed passwords

### Visitor Check-in

1. Enter visitor details and select host
2. If host is online → Real-time notification popup
3. If host is offline → WhatsApp notification sent
4. Host approves/denies through notification popup

### Logistics Entry

1. Navigate to "Logistics Entry"
2. Fill vehicle details (driver, plate, origin, destination)
3. Upload vehicle photo (optional)
4. WhatsApp notification sent to configured number

### Reports & Monitoring

- **View All Visitors**: Admin-only access to complete visitor history
- **View Status**: Monitor employee online/offline status
- **Check Out**: Process visitor exits or handle denied entries

## Development

### Running in Development Mode

```bash
# Set environment
set FLASK_ENV=development  # Windows
export FLASK_ENV=development  # Linux/Mac

# Run with debug mode
python app.py
```

### Code Quality

```bash
# Run linters
pylint app.py employee_db.py visitor_service.py vehicle_db.py

# Format code
black .

# Run tests
pytest tests/ -v

# Coverage report
pytest tests/ --cov=. --cov-report=html
```

### Project Structure

```
demo_internship/
├── app.py                  # Main Flask application
├── config.py               # Configuration management
├── logging_config.py       # Logging setup
├── db.py                   # Visitors database module
├── employee_db.py          # Employee database module
├── vehicle_db.py           # Vehicle database module
├── visitor_service.py      # Visitor business logic
├── Whatsapp_message.py     # WhatsApp notifications
├── Logistics_message.py    # Logistics notifications
├── templates/              # HTML templates
│   ├── errors/             # Error pages (404, 500, 403)
│   ├── home.html
│   ├── login.html
│   └── ...
├── static/                 # Static files (CSS, JS, images)
│   └── uploads/            # Uploaded files
├── logs/                   # Application logs
├── requirements.txt        # Dependencies
├── .env.example            # Environment template
├── Dockerfile              # Docker configuration
├── compose.yaml            # Docker Compose
└── README.md               # This file
```

## Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment guide.

## Troubleshooting

### WhatsApp Notifications Failing

- Ensure WhatsApp Web is logged in on the server
- Check `LOGISTICS_PHONE_NUMBER` is set correctly (include country code)
- Verify pywhatkit has browser access

### Port Already in Use

```bash
# Windows - Find process
netstat -ano | findstr :5000
taskkill /PID <process_id> /F

# Linux/Mac
lsof -ti:5000 | xargs kill -9
```

### Login Issues

- **Default admin not working**: Ensure `super/password123` credentials
- **New user can't login**: Check password was entered correctly (case-sensitive)
- **Session expired**: Sessions last 24 hours by default (configurable via `SESSION_LIFETIME_HOURS`)

## Security Notes

⚠️ **Production Deployment**:
- **Change default admin password** immediately
- Set strong `SECRET_KEY` in environment
- Use HTTPS in production
- Consider additional authentication (2FA, LDAP)
- Regularly backup databases
- Keep dependencies updated

## API Endpoints

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/health` | GET | Health check | No |
| `/login` | GET, POST | User login | No |
| `/logout` | GET | User logout | Yes |
| `/home` | GET | Dashboard | Yes |
| `/data` | POST | Visitor check-in | Yes |
| `/check_out_page` | GET | Check-out page | Yes |
| `/process_check_out` | POST | Process check-out | Yes |
| `/logistics` | GET | Logistics entry form | Yes |
| `/process_logistics_entry` | POST | Submit logistics entry | Yes |
| `/new_user` | GET | Add user form | Yes (Admin) |
| `/process_add_user` | POST | Create new user | Yes (Admin) |
| `/view_all` | GET | All visitors report | Yes (Admin) |
| `/view_status` | GET | Employee status | Yes (Admin) |
| `/api/visitors` | GET | Get active visitors (JSON) | Yes |
| `/api/employees` | GET | Get employees (JSON) | Yes (Admin) |
| `/api/action_visitor` | POST | Approve/deny visitor | Yes |
| `/check_notifications` | GET | Poll notifications (JSON) | Yes |

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## License

This project is proprietary software. All rights reserved.

## Support

For issues and questions:
- Check [Troubleshooting](#troubleshooting) section
- Review logs in `logs/app.log`
- Create an issue in the repository

---

**Version**: 2.0.0  
**Last Updated**: 2026-01-03
