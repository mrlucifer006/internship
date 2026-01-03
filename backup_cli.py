#!/usr/bin/env python3

import sys
import argparse
import getpass
from pathlib import Path
from db_backup import DatabaseBackup


def backup_command(args):
    secret_key = None
    if args.encrypt:
        secret_key = getpass.getpass("Enter secret key for encryption: ")
        if not secret_key:
            print("✗ Encryption requires a secret key!")
            sys.exit(1)
        
        confirm_key = getpass.getpass("Confirm secret key: ")
        if secret_key != confirm_key:
            print("✗ Secret keys don't match!")
            sys.exit(1)
    
    backup_manager = DatabaseBackup(args.db_path, args.backup_dir, secret_key)
    
    print("\n📦 Creating database backup...")
    if args.encrypt:
        print("🔒 Encryption enabled")
    
    try:
        backup_path = backup_manager.create_backup(encrypt=args.encrypt)
        info = backup_manager.get_backup_info(backup_path)
        
        print(f"\n✓ Backup created successfully!")
        print(f"  File: {info['name']}")
        print(f"  Size: {info['size_mb']} MB")
        print(f"  Location: {info['path']}")
        if info['encrypted']:
            print(f"  Status: 🔒 ENCRYPTED")
        
        if args.cleanup:
            print(f"\n🧹 Cleaning up old backups (keeping last {args.keep_count})...")
            backup_manager.cleanup_old_backups(args.keep_count)
        
    except Exception as e:
        print(f"\n✗ Backup failed: {e}")
        sys.exit(1)


def list_command(args):
    backup_manager = DatabaseBackup(args.db_path, args.backup_dir)
    
    print(f"\n📋 Backups in: {args.backup_dir}")
    backups = backup_manager.list_backups()
    
    if not backups:
        print("  No backups found.")
    else:
        print(f"\nFound {len(backups)} backup(s):\n")
        for i, backup in enumerate(backups, 1):
            info = backup_manager.get_backup_info(backup)
            encrypted_tag = "🔒 ENCRYPTED" if info['encrypted'] else ""
            print(f"  {i}. {info['name']} {encrypted_tag}")
            print(f"     Size: {info['size_mb']} MB | Created: {info['created']}")
            print()


def restore_command(args):
    secret_key = None
    if args.encrypted or (args.file and Path(args.file).suffix == '.encrypted'):
        secret_key = getpass.getpass("Enter secret key for decryption: ")
        if not secret_key:
            print("✗ Decryption requires a secret key!")
            sys.exit(1)
    
    backup_manager = DatabaseBackup(args.db_path, args.backup_dir, secret_key)
    
    if args.file:
        backup_path = Path(args.file)
        if not backup_path.exists():
            print(f"✗ Backup file not found: {backup_path}")
            sys.exit(1)
    else:
        print("\n📋 Available backups:")
        backups = backup_manager.list_backups()
        
        if not backups:
            print("No backups found!")
            sys.exit(1)
        
        for i, backup in enumerate(backups, 1):
            info = backup_manager.get_backup_info(backup)
            encrypted_tag = "🔒" if info['encrypted'] else ""
            print(f"  {i}. {encrypted_tag} {info['name']} - {info['created']} ({info['size_mb']} MB)")
        
        try:
            choice = int(input("\nSelect backup number to restore: "))
            if 1 <= choice <= len(backups):
                backup_path = backups[choice - 1]
            else:
                print("Invalid selection!")
                sys.exit(1)
        except (ValueError, KeyboardInterrupt):
            print("\nOperation cancelled.")
            sys.exit(0)
    
    is_encrypted = backup_path.suffix == '.encrypted'
    
    try:
        print(f"\n🔄 Restoring from: {backup_path.name}")
        if is_encrypted:
            print("🔓 Decrypting backup...")
        
        success = backup_manager.restore_backup(
            backup_path, 
            confirm=not args.yes,
            is_encrypted=is_encrypted
        )
        
        if success:
            print("\n✓ Database restored successfully!")
    except Exception as e:
        print(f"\n✗ Restoration failed: {e}")
        sys.exit(1)


def cleanup_command(args):
    backup_manager = DatabaseBackup(args.db_path, args.backup_dir)
    
    print(f"\n🧹 Cleaning up old backups (keeping last {args.keep_count})...")
    backup_manager.cleanup_old_backups(args.keep_count)


def main():
    parser = argparse.ArgumentParser(description='Database Backup & Restore CLI with Encryption')
    
    parser.add_argument('--db-path', default='instance/visitor_management.db')
    parser.add_argument('--backup-dir', default='backups')
    
    subparsers = parser.add_subparsers(dest='command')
    
    backup_parser = subparsers.add_parser('backup')
    backup_parser.add_argument('--encrypt', action='store_true')
    backup_parser.add_argument('--cleanup', action='store_true')
    backup_parser.add_argument('--keep-count', type=int, default=30)
    
    list_parser = subparsers.add_parser('list')
    
    restore_parser = subparsers.add_parser('restore')
    restore_parser.add_argument('--file')
    restore_parser.add_argument('--encrypted', action='store_true')
    restore_parser.add_argument('--yes', '-y', action='store_true')
    
    cleanup_parser = subparsers.add_parser('cleanup')
    cleanup_parser.add_argument('--keep-count', type=int, default=30)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    commands = {
        'backup': backup_command,
        'list': list_command,
        'restore': restore_command,
        'cleanup': cleanup_command
    }
    
    commands[args.command](args)


if __name__ == '__main__':
    main()
