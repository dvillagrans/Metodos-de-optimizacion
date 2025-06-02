#!/usr/bin/env python3
"""
Performance monitoring utility for the mathematical optimization visualization app.
"""

import os
import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Monitor performance metrics for the optimization app."""
    
    def __init__(self, log_file: Optional[str] = None):
        """Initialize the performance monitor.
        
        Args:
            log_file: Path to log file for storing metrics. If None, uses default.
        """
        if log_file is None:
            log_file = os.path.join(os.path.dirname(__file__), 'performance_metrics.json')
        
        self.log_file = log_file
        self.metrics = []
        self._load_existing_metrics()
    
    def _load_existing_metrics(self):
        """Load existing metrics from log file."""
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    self.metrics = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load existing metrics: {e}")
                self.metrics = []
    
    def log_animation_performance(self, method: str, data_size: int, 
                                generation_time: float, file_size_mb: float,
                                cache_hit: bool = False):
        """Log performance metrics for animation generation.
        
        Args:
            method: Optimization method used (simplex, granm, dosfases)
            data_size: Size of the problem (number of variables + constraints)
            generation_time: Time taken to generate animation in seconds
            file_size_mb: Size of generated file in megabytes
            cache_hit: Whether the result was served from cache
        """
        metric = {
            'timestamp': datetime.now().isoformat(),
            'method': method,
            'data_size': data_size,
            'generation_time': generation_time,
            'file_size_mb': file_size_mb,
            'cache_hit': cache_hit
        }
        
        self.metrics.append(metric)
        self._save_metrics()
        
        logger.info(f"Performance logged: {method} method, "
                   f"{data_size} elements, {generation_time:.2f}s, "
                   f"{file_size_mb:.2f}MB, cache: {cache_hit}")
    
    def _save_metrics(self):
        """Save metrics to log file."""
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(self.metrics, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Could not save metrics: {e}")
    
    def get_performance_summary(self, last_n_days: int = 7) -> Dict:
        """Get performance summary for the last N days.
        
        Args:
            last_n_days: Number of days to include in summary
            
        Returns:
            Dictionary with performance summary
        """
        cutoff_time = datetime.now().timestamp() - (last_n_days * 24 * 3600)
        
        recent_metrics = [
            m for m in self.metrics 
            if datetime.fromisoformat(m['timestamp']).timestamp() > cutoff_time
        ]
        
        if not recent_metrics:
            return {'message': 'No recent metrics available'}
        
        # Calculate statistics
        total_requests = len(recent_metrics)
        cache_hits = sum(1 for m in recent_metrics if m['cache_hit'])
        cache_hit_rate = (cache_hits / total_requests) * 100 if total_requests > 0 else 0
        
        generation_times = [m['generation_time'] for m in recent_metrics if not m['cache_hit']]
        avg_generation_time = sum(generation_times) / len(generation_times) if generation_times else 0
        
        file_sizes = [m['file_size_mb'] for m in recent_metrics]
        avg_file_size = sum(file_sizes) / len(file_sizes) if file_sizes else 0
        
        # Method breakdown
        methods = {}
        for metric in recent_metrics:
            method = metric['method']
            if method not in methods:
                methods[method] = {'count': 0, 'avg_time': 0}
            methods[method]['count'] += 1
            methods[method]['avg_time'] += metric['generation_time']
        
        for method in methods:
            methods[method]['avg_time'] /= methods[method]['count']
        
        return {
            'period_days': last_n_days,
            'total_requests': total_requests,
            'cache_hit_rate': f"{cache_hit_rate:.1f}%",
            'avg_generation_time': f"{avg_generation_time:.2f}s",
            'avg_file_size': f"{avg_file_size:.2f}MB",
            'methods_breakdown': methods
        }
    
    def clear_old_metrics(self, older_than_days: int = 30):
        """Clear metrics older than specified days.
        
        Args:
            older_than_days: Number of days after which to clear metrics
        """
        cutoff_time = datetime.now().timestamp() - (older_than_days * 24 * 3600)
        
        original_count = len(self.metrics)
        self.metrics = [
            m for m in self.metrics 
            if datetime.fromisoformat(m['timestamp']).timestamp() > cutoff_time
        ]
        
        cleared_count = original_count - len(self.metrics)
        if cleared_count > 0:
            self._save_metrics()
            logger.info(f"Cleared {cleared_count} old metrics")

def main():
    """Main function for CLI usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Performance monitoring for optimization app')
    parser.add_argument('--summary', action='store_true', 
                       help='Show performance summary')
    parser.add_argument('--days', type=int, default=7,
                       help='Number of days for summary (default: 7)')
    parser.add_argument('--clear', type=int, metavar='DAYS',
                       help='Clear metrics older than specified days')
    
    args = parser.parse_args()
    
    monitor = PerformanceMonitor()
    
    if args.clear:
        monitor.clear_old_metrics(args.clear)
        print(f"Cleared metrics older than {args.clear} days")
    
    if args.summary:
        summary = monitor.get_performance_summary(args.days)
        print(f"\nPerformance Summary (Last {args.days} days):")
        print("=" * 40)
        
        if 'message' in summary:
            print(summary['message'])
        else:
            print(f"Total Requests: {summary['total_requests']}")
            print(f"Cache Hit Rate: {summary['cache_hit_rate']}")
            print(f"Avg Generation Time: {summary['avg_generation_time']}")
            print(f"Avg File Size: {summary['avg_file_size']}")
            print("\nMethods Breakdown:")
            for method, stats in summary['methods_breakdown'].items():
                print(f"  {method}: {stats['count']} requests, "
                      f"{stats['avg_time']:.2f}s avg")

if __name__ == '__main__':
    main()
