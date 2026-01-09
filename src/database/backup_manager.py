import os
import shutil
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

class BackupManager:
    """
    Manages database backups.
    """
    
    def __init__(self, db_path: Optional[str] = None, backup_dir: Optional[str] = None):
        """
        Initialize BackupManager.
        
        Args:
            db_path: Path to the database file. If None, uses default.
            backup_dir: Path to the backup directory. If None, uses default.
        """
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        if db_path is None:
            self.db_path = os.path.join(project_root, 'data', 'investment_system.db')
        else:
            self.db_path = db_path
            
        if backup_dir is None:
            self.backup_dir = os.path.join(project_root, 'data', 'backups')
        else:
            self.backup_dir = backup_dir
            
        # Ensure backup directory exists
        os.makedirs(self.backup_dir, exist_ok=True)
        
    def create_backup(self, note: str = "") -> str:
        """
        Create a backup of the database.
        
        Args:
            note: Optional note to append to the filename.
            
        Returns:
            Path to the created backup file.
        """
        if not os.path.exists(self.db_path):
            logger.error(f"Database file not found at {self.db_path}")
            raise FileNotFoundError(f"Database file not found at {self.db_path}")
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"investment_system_backup_{timestamp}"
        if note:
            filename += f"_{note}"
        filename += ".db"
        
        backup_path = os.path.join(self.backup_dir, filename)
        
        try:
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Database backup created at {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise
            
    def list_backups(self) -> list:
        """List all backup files sorted by date (newest first)."""
        backups = []
        if not os.path.exists(self.backup_dir):
            return []
            
        for f in os.listdir(self.backup_dir):
            if f.startswith("investment_system_backup_") and f.endswith(".db"):
                path = os.path.join(self.backup_dir, f)
                try:
                    backups.append({
                        'filename': f,
                        'path': path,
                        'size': os.path.getsize(path),
                        'created': datetime.fromtimestamp(os.path.getctime(path))
                    })
                except OSError:
                    continue
        
        return sorted(backups, key=lambda x: x['created'], reverse=True)
        
    def cleanup_old_backups(self, keep_count: int = 30):
        """
        Delete old backups, keeping only the most recent ones.
        
        Args:
            keep_count: Number of recent backups to keep.
        """
        backups = self.list_backups()
        if len(backups) <= keep_count:
            return
            
        to_delete = backups[keep_count:]
        for backup in to_delete:
            try:
                os.remove(backup['path'])
                logger.info(f"Deleted old backup: {backup['filename']}")
            except Exception as e:
                logger.error(f"Failed to delete backup {backup['filename']}: {e}")
