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

# Database files and executables
db_files = [
    ('schema.sql', '.'),
    ('cloudflared-windows-amd64.exe', '.'),
    ('start_background.vbs', '.'),
    ('stop_background.bat', '.'),
    ('.env', '.') # [FIX] Include .env file for configuration settings
]

# [FIX] Flatten neonize.proto submodules to root for imports
import neonize
import neonize.proto
import os
proto_dir = os.path.dirname(neonize.proto.__file__)
for name in os.listdir(proto_dir):
    path = os.path.join(proto_dir, name)
    if os.path.isdir(path) and name.startswith("wa"):
        db_files.append((path, name))

# [FIX] Include neonize binary DLL explicitly
neonize_dir = os.path.dirname(neonize.__file__)
dll_name = 'neonize-windows-amd64.dll'
dll_path = os.path.join(neonize_dir, dll_name)
if os.path.exists(dll_path):
    print(f"Adding binary: {dll_path}")
    db_files.append((dll_path, 'neonize'))
else:
    print(f"WARNING: Could not find {dll_name} at {dll_path}")

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
        'supabase',
        'postgrest',
        'gotrue',
        'realtime',
        'storage3',
        'supafunc',
        'watchdog',
        'employee_db',
        'visitor_service',
        'vehicle_db',
        'db',
        'Logistics_message',
        'Whatsapp_message',
        'seo_routes',
        'pagination',
        'logging_config',
        'config',
        'waitress',
        'cryptography',
        'cache_manager',
        'db_supabase',
        'neonize.proto',
        'neonize.proto.waAICommon',
        'whatsapp_service',
        'server_discovery',
        'pkg_resources',
        'updater',
        'packaging',
        'requests',
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
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='favicon.ico',
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
