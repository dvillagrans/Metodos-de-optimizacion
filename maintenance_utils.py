#!/usr/bin/env python3
"""
Maintenance utilities for the mathematical optimization visualization app.
"""

import os
import shutil
import time
import logging
from pathlib import Path
from typing import List, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MaintenanceUtils:
    """Utilities for maintaining the optimization visualization app."""
    
    def __init__(self, project_root: str = None):
        """Initialize maintenance utilities.
        
        Args:
            project_root: Root directory of the project. If None, auto-detect.
        """
        if project_root is None:
            project_root = os.path.dirname(os.path.abspath(__file__))
        
        self.project_root = Path(project_root)
        self.media_dir = self.project_root / "app" / "static" / "media"
        self.cache_dir = self.project_root / "output" / "videos" / "cache"
        self.temp_dirs = [
            self.project_root / "manim_anim" / "media",
            self.project_root / "output" / "videos",
        ]
    
    def cleanup_old_media_files(self, older_than_hours: int = 24) -> Tuple[int, float]:
        """Clean up old media files to free disk space.
        
        Args:
            older_than_hours: Remove files older than this many hours
            
        Returns:
            Tuple of (files_removed, space_freed_mb)
        """
        cutoff_time = time.time() - (older_than_hours * 3600)
        files_removed = 0
        space_freed = 0
        
        for media_dir in [self.media_dir] + self.temp_dirs:
            if not media_dir.exists():
                continue
                
            for file_path in media_dir.glob("**/*"):
                if file_path.is_file():
                    try:
                        file_stat = file_path.stat()
                        if file_stat.st_mtime < cutoff_time:
                            file_size = file_stat.st_size
                            file_path.unlink()
                            files_removed += 1
                            space_freed += file_size
                            logger.debug(f"Removed old file: {file_path}")
                    except Exception as e:
                        logger.warning(f"Could not remove file {file_path}: {e}")
        
        space_freed_mb = space_freed / (1024 * 1024)
        logger.info(f"Cleanup completed: {files_removed} files removed, "
                   f"{space_freed_mb:.2f} MB freed")
        
        return files_removed, space_freed_mb
    
    def optimize_cache(self, max_cache_size_mb: int = 500) -> Tuple[int, float]:
        """Optimize cache by removing least recently used files if cache is too large.
        
        Args:
            max_cache_size_mb: Maximum cache size in megabytes
            
        Returns:
            Tuple of (files_removed, space_freed_mb)
        """
        if not self.cache_dir.exists():
            return 0, 0.0
        
        # Get all cache files with their stats
        cache_files = []
        total_size = 0
        
        for file_path in self.cache_dir.glob("*"):
            if file_path.is_file():
                try:
                    stat = file_path.stat()
                    cache_files.append((file_path, stat.st_atime, stat.st_size))
                    total_size += stat.st_size
                except Exception as e:
                    logger.warning(f"Could not stat cache file {file_path}: {e}")
        
        total_size_mb = total_size / (1024 * 1024)
        
        if total_size_mb <= max_cache_size_mb:
            logger.info(f"Cache size OK: {total_size_mb:.2f} MB <= {max_cache_size_mb} MB")
            return 0, 0.0
        
        # Sort by access time (oldest first)
        cache_files.sort(key=lambda x: x[1])
        
        files_removed = 0
        space_freed = 0
        
        # Remove oldest files until we're under the limit
        for file_path, _, file_size in cache_files:
            if total_size_mb <= max_cache_size_mb:
                break
                
            try:
                file_path.unlink()
                files_removed += 1
                space_freed += file_size
                total_size_mb -= file_size / (1024 * 1024)
                logger.debug(f"Removed cache file: {file_path}")
            except Exception as e:
                logger.warning(f"Could not remove cache file {file_path}: {e}")
        
        space_freed_mb = space_freed / (1024 * 1024)
        logger.info(f"Cache optimization completed: {files_removed} files removed, "
                   f"{space_freed_mb:.2f} MB freed")
        
        return files_removed, space_freed_mb
    
    def get_disk_usage_summary(self) -> dict:
        """Get disk usage summary for project directories.
        
        Returns:
            Dictionary with disk usage information
        """
        summary = {}
        
        directories = {
            'media': self.media_dir,
            'cache': self.cache_dir,
            'manim_media': self.project_root / "manim_anim" / "media",
            'output_videos': self.project_root / "output" / "videos"
        }
        
        for name, dir_path in directories.items():
            if dir_path.exists():
                total_size = 0
                file_count = 0
                
                for file_path in dir_path.glob("**/*"):
                    if file_path.is_file():
                        try:
                            total_size += file_path.stat().st_size
                            file_count += 1
                        except:
                            pass
                
                summary[name] = {
                    'size_mb': total_size / (1024 * 1024),
                    'file_count': file_count,
                    'path': str(dir_path)
                }
            else:
                summary[name] = {
                    'size_mb': 0,
                    'file_count': 0,
                    'path': str(dir_path) + ' (does not exist)'
                }
        
        return summary
    
    def fix_permissions(self) -> int:
        """Fix file permissions for media directories.
        
        Returns:
            Number of files with permissions fixed
        """
        fixed_count = 0
        
        for media_dir in [self.media_dir] + self.temp_dirs:
            if not media_dir.exists():
                continue
                
            for file_path in media_dir.glob("**/*"):
                if file_path.is_file():
                    try:
                        # Set read/write permissions for owner, read for others
                        file_path.chmod(0o644)
                        fixed_count += 1
                    except Exception as e:
                        logger.warning(f"Could not fix permissions for {file_path}: {e}")
        
        if fixed_count > 0:
            logger.info(f"Fixed permissions for {fixed_count} files")
        
        return fixed_count

def main():
    """Main function for CLI usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Maintenance utilities for optimization app')
    parser.add_argument('--cleanup', type=int, metavar='HOURS',
                       help='Clean up files older than specified hours')
    parser.add_argument('--optimize-cache', type=int, metavar='MB', default=500,
                       help='Optimize cache to specified size in MB (default: 500)')
    parser.add_argument('--disk-usage', action='store_true',
                       help='Show disk usage summary')
    parser.add_argument('--fix-permissions', action='store_true',
                       help='Fix file permissions')
    parser.add_argument('--all', action='store_true',
                       help='Run all maintenance tasks')
    
    args = parser.parse_args()
    
    utils = MaintenanceUtils()
    
    if args.all or args.cleanup:
        hours = args.cleanup if args.cleanup else 24
        files_removed, space_freed = utils.cleanup_old_media_files(hours)
        print(f"Cleanup: {files_removed} files removed, {space_freed:.2f} MB freed")
    
    if args.all or args.optimize_cache:
        files_removed, space_freed = utils.optimize_cache(args.optimize_cache)
        print(f"Cache optimization: {files_removed} files removed, {space_freed:.2f} MB freed")
    
    if args.all or args.fix_permissions:
        fixed_count = utils.fix_permissions()
        print(f"Permissions fixed: {fixed_count} files")
    
    if args.all or args.disk_usage:
        summary = utils.get_disk_usage_summary()
        print("\nDisk Usage Summary:")
        print("=" * 50)
        for name, info in summary.items():
            print(f"{name:15}: {info['size_mb']:8.2f} MB, "
                  f"{info['file_count']:4d} files")
            print(f"{'':17} {info['path']}")

if __name__ == '__main__':
    main()
