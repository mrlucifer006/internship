# How to Run Visitor Management System

## Using the Executable (.exe)

### Quick Start
1. Navigate to the folder: `dist/VisitorManagement/`
2. Double-click **`VisitorManagement.exe`**
3. Wait 5-10 seconds for the application to start
4. Your browser will automatically open to `http://localhost:5000`
5. Login with:
   - **Username**: `super`
   - **Password**: `password123`

### Important Notes
- **First Run**: May take longer (~10 seconds) to start
- **Browser**: Will auto-open after server starts
- **Console Window**: Keep the black console window open (this is the server)
- **Stopping**: Press `Ctrl+C` in the console or close the console window
- **Antivirus**: Some antivirus may flag it (false positive) - mark as safe

### Distributing
To share with others:
1. Copy the entire `dist/VisitorManagement/` folder
2. Share the folder (not just the .exe)
3. Recipients can run `VisitorManagement.exe` directly
4. **No Python installation required!**

## Using Python (Development)

If you have Python installed:
```bash
python app.py
```
Then open browser to `http://localhost:5000`

## Default Credentials

### Super Admin
- **Username**: `super`
- **Password**: `password123`
- **Role**: Developer (Level 5)

## Troubleshooting

### Port Already in Use
If you see "Address already in use":
- Another instance is running
- Stop the other instance or restart your computer

### Browser Doesn't Open
- Manually navigate to `http://localhost:5000`

### Database Errors
- Ensure `employee.db`, `visitors.db`, and `vehicle.db` are in the same folder

### Executable Won't Start
- Check antivirus hasn't blocked it
- Run as Administrator
- Check Windows Event Viewer for errors

## File Structure

```
VisitorManagement/
├── VisitorManagement.exe  ← Run this!
└── _internal/             (Supporting files - don't touch)
    ├── templates/
    ├── static/
    ├── *.db (databases)
    └── [python libraries]
```

## System Requirements
- **OS**: Windows 10/11 (64-bit)
- **RAM**: 2GB minimum
- **Disk**: 200MB free space
- **Network**: None required (runs locally)
