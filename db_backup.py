import os
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
import logging
from cryptography.fernet import Fernet
import base64
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EncryptionManager:
    
    def __init__(self, secret_key=None):
        if secret_key:
            key = hashlib.sha256(secret_key.encode()).digest()
            self.fernet_key = base64.urlsafe_b64encode(key)
            self.cipher = Fernet(self.fernet_key)
        else:
            self.cipher = None
    
    def encrypt_file(self, file_path, output_path=None):
        if not self.cipher:
            raise ValueError("No secret key provided for encryption")
        
        file_path = Path(file_path)
        if output_path is None:
            output_path = file_path.parent / f"{file_path.name}.encrypted"
        else:
            output_path = Path(output_path)
        
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        encrypted_data = self.cipher.encrypt(file_data)
        
        with open(output_path, 'wb') as f:
            f.write(encrypted_data)
        
        logger.info(f"✓ File encrypted: {output_path.name}")
        return output_path
    
    def decrypt_file(self, encrypted_path, output_path=None):
        if not self.cipher:
            raise ValueError("No secret key provided for decryption")
        
        encrypted_path = Path(encrypted_path)
        if output_path is None:
            if encrypted_path.suffix == '.encrypted':
                output_path = encrypted_path.with_suffix('')
            else:
                output_path = encrypted_path.parent / f"{encrypted_path.stem}_decrypted{encrypted_path.suffix}"
        else:
            output_path = Path(output_path)
        
        with open(encrypted_path, 'rb') as f:
            encrypted_data = f.read()
        
        try:
            decrypted_data = self.cipher.decrypt(encrypted_data)
        except Exception as e:
            raise ValueError(f"Decryption failed. Wrong secret key? Error: {e}")
        
        with open(output_path, 'wb') as f:
            f.write(decrypted_data)
        
        logger.info(f"✓ File decrypted: {output_path.name}")
        return output_path


class DatabaseBackup:
    
    def __init__(self, db_path=None, backup_dir=None, secret_key=None):
        if db_path is None:
            # Import resolved path from db.py
            from db import DB_NAME
            self.db_path = Path(DB_NAME)
        else:
            self.db_path = Path(db_path)
            
        if backup_dir is None:
            from db import get_base_path
            # Store backups next to instance folder
            self.backup_dir = Path(get_base_path()) / 'backups'
        else:
            self.backup_dir = Path(backup_dir)
            
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        self.encryption = EncryptionManager(secret_key) if secret_key else None
        
    def create_backup(self, backup_name=None, encrypt=False):
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")
        
        if backup_name is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"visitor_db_backup_{timestamp}.db"
        
        temp_backup_path = self.backup_dir / backup_name
        
        try:
            source_conn = sqlite3.connect(str(self.db_path))
            backup_conn = sqlite3.connect(str(temp_backup_path))
            
            with backup_conn:
                source_conn.backup(backup_conn)
            
            source_conn.close()
            backup_conn.close()
            
            logger.info(f"[SUCCESS] Backup created: {temp_backup_path.name}")
            
            if encrypt:
                if not self.encryption:
                    raise ValueError("Encryption requested but no secret key provided")
                
                encrypted_path = self.encryption.encrypt_file(temp_backup_path)
                temp_backup_path.unlink()
                logger.info(f"✓ Backup encrypted and saved: {encrypted_path}")
                return encrypted_path
            
            return temp_backup_path
            
        except Exception as e:
            logger.error(f"✗ Backup failed: {e}")
            if temp_backup_path.exists():
                temp_backup_path.unlink()
            raise
    
    def restore_backup(self, backup_path, confirm=True, is_encrypted=False):
        backup_path = Path(backup_path)
        
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
        
        if is_encrypted or backup_path.suffix == '.encrypted':
            if not self.encryption:
                raise ValueError("Backup is encrypted but no secret key provided")
            
            logger.info("Decrypting backup file...")
            decrypted_path = self.encryption.decrypt_file(backup_path)
            restore_from = decrypted_path
            cleanup_decrypted = True
        else:
            restore_from = backup_path
            cleanup_decrypted = False
        
        if confirm:
            print(f"\n⚠️  WARNING: This will replace the current database!")
            print(f"   Current DB: {self.db_path}")
            print(f"   Backup: {backup_path}")
            response = input("\nAre you sure you want to continue? (yes/no): ")
            if response.lower() != 'yes':
                print("Restoration cancelled.")
                if cleanup_decrypted and restore_from.exists():
                    restore_from.unlink()
                return False
        
        try:
            safety_backup = self.backup_dir / f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            if self.db_path.exists():
                shutil.copy2(self.db_path, safety_backup)
                logger.info(f"Safety backup created: {safety_backup}")
            
            shutil.copy2(restore_from, self.db_path)
            logger.info(f"✓ Database restored successfully from: {backup_path.name}")
            
            if cleanup_decrypted and restore_from.exists():
                restore_from.unlink()
            
            return True
            
        except Exception as e:
            logger.error(f"✗ Restoration failed: {e}")
            if cleanup_decrypted and restore_from.exists():
                restore_from.unlink()
            raise
    
    def list_backups(self, include_encrypted=True):
        patterns = ['*.db']
        if include_encrypted:
            patterns.append('*.encrypted')
        
        backups = []
        for pattern in patterns:
            backups.extend(self.backup_dir.glob(pattern))
        
        backups = sorted(backups, key=lambda p: p.stat().st_mtime, reverse=True)
        return backups
    
    def cleanup_old_backups(self, keep_count=30):
        backups = self.list_backups()
        
        if len(backups) <= keep_count:
            logger.info(f"No cleanup needed. Current backups: {len(backups)}")
            return
        
        to_delete = backups[keep_count:]
        for backup in to_delete:
            try:
                backup.unlink()
                logger.info(f"Deleted old backup: {backup.name}")
            except Exception as e:
                logger.error(f"Failed to delete {backup.name}: {e}")
        
        logger.info(f"Cleanup complete. Kept {keep_count} most recent backups.")
    
    def get_backup_info(self, backup_path):
        backup_path = Path(backup_path)
        
        if not backup_path.exists():
            return None
        
        stat = backup_path.stat()
        is_encrypted = backup_path.suffix == '.encrypted'
        
        return {
            'name': backup_path.name,
            'path': str(backup_path),
            'size': stat.st_size,
            'size_mb': round(stat.st_size / (1024 * 1024), 2),
            'created': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
            'encrypted': is_encrypted
        }


if __name__ == '__main__':
    import getpass
    
    secret = getpass.getpass("Enter secret key for encryption (or press Enter to skip): ")
    
    backup_manager = DatabaseBackup(secret_key=secret if secret else None)
    
    print("\n📦 Creating encrypted database backup...")
    backup_path = backup_manager.create_backup(encrypt=bool(secret))
    print(f"✓ Backup saved to: {backup_path}")
    
    print("\n📋 Available backups:")
    for backup in backup_manager.list_backups():
        info = backup_manager.get_backup_info(backup)
        encrypted_tag = "🔒 ENCRYPTED" if info['encrypted'] else ""
        print(f"  • {info['name']} ({info['size_mb']} MB) - {info['created']} {encrypted_tag}")
