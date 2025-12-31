# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Collect all template files
template_files = []
import os
for root, dirs, files in os.walk('templates'):
    for file in files:
        if file.endswith('.html'):
            template_files.append((os.path.join(root, file), root))

# Collect all static files
static_files = []
for root, dirs, files in os.walk('static'):
    for file in files:
        static_files.append((os.path.join(root, file), root))

# Database files
db_files = [
    ('employee.db', '.'),
    ('visitors.db', '.'),
    ('vehicle.db', '.')
]

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=template_files + static_files + db_files,
    hiddenimports=[
        'flask',
        'flask.templating',
        'flask.sessions',
        'jinja2',
        'jinja2.ext',
        'werkzeug',
        'werkzeug.security',
        'sqlite3',
        'pywhatkit',
        'watchdog',
        'employee_db',
        'visitor_service',
        'vehicle_db',
        'db',
        'Logistics_message',
        'Whatsapp_message',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='VisitorManagement',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='VisitorManagement',
)
