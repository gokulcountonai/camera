#!/usr/bin/env python3
"""
Backup and recovery script for the camera streaming system.
Provides automated backup and recovery capabilities.
"""

import os
import json
import shutil
import tarfile
import zipfile
from datetime import datetime
import argparse
import config

class BackupManager:
    """Manage system backups and recovery."""
    
    def __init__(self, backup_dir="backups"):
        self.backup_dir = backup_dir
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Ensure backup directory exists
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def create_backup(self, include_logs=True, include_images=True):
        """Create a comprehensive system backup."""
        backup_name = f"camera_system_backup_{self.timestamp}"
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        print(f"Creating backup: {backup_name}")
        
        # Files to backup
        files_to_backup = [
            'cam1_stream.py',
            'start.py',
            'client.py',
            'src/sendData.py',
            'storeimages.py',
            'config.py',
            'run.sh',
            'monitoring.py',
            'health_check.py',
            'log_analyzer.py',
            'graceful_shutdown.py',
            'test_system.py',
            'camera-streaming.service',
            'BUGFIXES.md',
            'REDIS_RECONNECTION_FIXES.md',
            'MONITORING_AND_DEBUGGING.md',
            'FINAL_SUMMARY.md'
        ]
        
        # Directories to backup
        dirs_to_backup = []
        if include_logs and os.path.exists('logs'):
            dirs_to_backup.append('logs')
        if include_images and os.path.exists('images'):
            dirs_to_backup.append('images')
        
        try:
            # Create backup archive
            with tarfile.open(f"{backup_path}.tar.gz", "w:gz") as tar:
                # Add files
                for file_path in files_to_backup:
                    if os.path.exists(file_path):
                        tar.add(file_path)
                        print(f"  ✅ Added file: {file_path}")
                    else:
                        print(f"  ⚠️  File not found: {file_path}")
                
                # Add directories
                for dir_path in dirs_to_backup:
                    if os.path.exists(dir_path):
                        tar.add(dir_path)
                        print(f"  ✅ Added directory: {dir_path}")
                    else:
                        print(f"  ⚠️  Directory not found: {dir_path}")
            
            # Create backup manifest
            manifest = {
                'backup_name': backup_name,
                'timestamp': datetime.now().isoformat(),
                'files_backed_up': [f for f in files_to_backup if os.path.exists(f)],
                'directories_backed_up': [d for d in dirs_to_backup if os.path.exists(d)],
                'backup_size_mb': round(os.path.getsize(f"{backup_path}.tar.gz") / (1024 * 1024), 2),
                'system_info': {
                    'config_redis_host': config.REDIS_HOST,
                    'config_redis_port': config.REDIS_PORT,
                    'config_camera_resolution': f"{config.CAMERA_WIDTH}x{config.CAMERA_HEIGHT}"
                }
            }
            
            with open(f"{backup_path}_manifest.json", 'w') as f:
                json.dump(manifest, f, indent=2)
            
            print(f"✅ Backup created successfully: {backup_path}.tar.gz")
            print(f"📄 Manifest saved: {backup_path}_manifest.json")
            print(f"📊 Backup size: {manifest['backup_size_mb']} MB")
            
            return f"{backup_path}.tar.gz"
            
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return None
    
    def list_backups(self):
        """List all available backups."""
        backups = []
        
        for file in os.listdir(self.backup_dir):
            if file.endswith('.tar.gz'):
                file_path = os.path.join(self.backup_dir, file)
                manifest_path = file_path.replace('.tar.gz', '_manifest.json')
                
                backup_info = {
                    'file': file,
                    'size_mb': round(os.path.getsize(file_path) / (1024 * 1024), 2),
                    'modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                }
                
                if os.path.exists(manifest_path):
                    try:
                        with open(manifest_path, 'r') as f:
                            manifest = json.load(f)
                            backup_info['manifest'] = manifest
                    except:
                        pass
                
                backups.append(backup_info)
        
        return sorted(backups, key=lambda x: x['modified'], reverse=True)
    
    def restore_backup(self, backup_file, restore_dir="restored"):
        """Restore a backup to a specified directory."""
        backup_path = os.path.join(self.backup_dir, backup_file)
        
        if not os.path.exists(backup_path):
            print(f"❌ Backup file not found: {backup_path}")
            return False
        
        print(f"Restoring backup: {backup_file}")
        
        try:
            # Create restore directory
            os.makedirs(restore_dir, exist_ok=True)
            
            # Extract backup
            with tarfile.open(backup_path, "r:gz") as tar:
                tar.extractall(restore_dir)
            
            print(f"✅ Backup restored to: {restore_dir}")
            
            # Check for manifest
            manifest_path = backup_path.replace('.tar.gz', '_manifest.json')
            if os.path.exists(manifest_path):
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
                print(f"📄 Backup manifest: {manifest.get('timestamp', 'Unknown')}")
                print(f"📊 Files restored: {len(manifest.get('files_backed_up', []))}")
                print(f"📁 Directories restored: {len(manifest.get('directories_backed_up', []))}")
            
            return True
            
        except Exception as e:
            print(f"❌ Restore failed: {e}")
            return False
    
    def cleanup_old_backups(self, keep_days=30):
        """Remove old backups to save disk space."""
        cutoff_time = datetime.now().timestamp() - (keep_days * 24 * 60 * 60)
        
        removed_count = 0
        for file in os.listdir(self.backup_dir):
            file_path = os.path.join(self.backup_dir, file)
            if os.path.getmtime(file_path) < cutoff_time:
                try:
                    os.remove(file_path)
                    print(f"🗑️  Removed old backup: {file}")
                    removed_count += 1
                except Exception as e:
                    print(f"❌ Failed to remove {file}: {e}")
        
        print(f"✅ Cleanup completed: {removed_count} old backups removed")
        return removed_count
    
    def verify_backup(self, backup_file):
        """Verify the integrity of a backup file."""
        backup_path = os.path.join(self.backup_dir, backup_file)
        
        if not os.path.exists(backup_path):
            print(f"❌ Backup file not found: {backup_path}")
            return False
        
        print(f"Verifying backup: {backup_file}")
        
        try:
            with tarfile.open(backup_path, "r:gz") as tar:
                # Test archive integrity
                tar.getmembers()
            
            print("✅ Backup integrity verified")
            return True
            
        except Exception as e:
            print(f"❌ Backup verification failed: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description='Backup and recovery for camera streaming system')
    parser.add_argument('action', choices=['backup', 'restore', 'list', 'cleanup', 'verify'],
                       help='Action to perform')
    parser.add_argument('--backup-file', help='Backup file for restore/verify actions')
    parser.add_argument('--restore-dir', default='restored', help='Directory for restore action')
    parser.add_argument('--keep-days', type=int, default=30, help='Days to keep backups (cleanup)')
    parser.add_argument('--no-logs', action='store_true', help='Exclude logs from backup')
    parser.add_argument('--no-images', action='store_true', help='Exclude images from backup')
    
    args = parser.parse_args()
    
    backup_mgr = BackupManager()
    
    if args.action == 'backup':
        include_logs = not args.no_logs
        include_images = not args.no_images
        backup_mgr.create_backup(include_logs=include_logs, include_images=include_images)
    
    elif args.action == 'list':
        backups = backup_mgr.list_backups()
        if backups:
            print("Available backups:")
            for backup in backups:
                print(f"  📦 {backup['file']} ({backup['size_mb']} MB) - {backup['modified']}")
        else:
            print("No backups found")
    
    elif args.action == 'restore':
        if not args.backup_file:
            print("❌ Please specify a backup file with --backup-file")
            return
        backup_mgr.restore_backup(args.backup_file, args.restore_dir)
    
    elif args.action == 'cleanup':
        backup_mgr.cleanup_old_backups(args.keep_days)
    
    elif args.action == 'verify':
        if not args.backup_file:
            print("❌ Please specify a backup file with --backup-file")
            return
        backup_mgr.verify_backup(args.backup_file)

if __name__ == "__main__":
    main()