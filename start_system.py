#!/usr/bin/env python3
"""
Enterprise Load Balancer System Startup Script
Launches the complete system with load balancer, servers, and monitoring
"""

import subprocess
import time
import signal
import sys
import os
import json
from typing import List, Dict, Any

class SystemManager:
    """Manages the entire load balancer system"""
    
    def __init__(self):
        self.processes = {}
        self.running = False
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\nReceived signal {signum}, shutting down system...")
        self.stop_all()
        sys.exit(0)
    
    def start_load_balancer(self):
        """Start the load balancer"""
        print("🚀 Starting Enterprise Load Balancer...")
        try:
            process = subprocess.Popen(
                [sys.executable, "load_balancer.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.processes['load_balancer'] = process
            print(f"✅ Load balancer started (PID: {process.pid})")
            
            # Wait a moment for load balancer to start
            time.sleep(2)
            return True
            
        except Exception as e:
            print(f"❌ Failed to start load balancer: {e}")
            return False
    
    def start_servers(self, num_servers: int = 2):
        """Start backend servers"""
        print(f"🖥️  Starting {num_servers} backend servers...")
        
        try:
            # Start server cluster
            process = subprocess.Popen(
                [sys.executable, "server.py", "12345", "cluster", str(num_servers)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.processes['servers'] = process
            print(f"✅ Server cluster started (PID: {process.pid})")
            
            # Wait for servers to start
            time.sleep(3)
            return True
            
        except Exception as e:
            print(f"❌ Failed to start servers: {e}")
            return False
    
    def start_monitoring(self):
        """Start the monitoring system"""
        print("📊 Starting monitoring system...")
        try:
            process = subprocess.Popen(
                [sys.executable, "monitor.py", "--monitor-only"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.processes['monitor'] = process
            print(f"✅ Monitoring started (PID: {process.pid})")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start monitoring: {e}")
            return False
    
    def start_web_dashboard(self):
        """Start the web dashboard"""
        print("🌐 Starting web dashboard...")
        try:
            process = subprocess.Popen(
                [sys.executable, "monitor.py", "--web-dashboard"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.processes['dashboard'] = process
            print(f"✅ Web dashboard started (PID: {process.pid})")
            print("🌐 Dashboard available at: http://localhost:8080")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start web dashboard: {e}")
            return False
    
    def start_all(self, num_servers: int = 2, enable_dashboard: bool = True):
        """Start the entire system"""
        if self.running:
            print("⚠️  System is already running")
            return False
        
        print("🚀 Starting Enterprise Load Balancer System...")
        print("=" * 50)
        
        # Start components in order
        if not self.start_load_balancer():
            return False
        
        if not self.start_servers(num_servers):
            return False
        
        if not self.start_monitoring():
            return False
        
        if enable_dashboard:
            if not self.start_web_dashboard():
                print("⚠️  Web dashboard failed to start, continuing without it")
        
        self.running = True
        
        print("=" * 50)
        print("🎉 System started successfully!")
        print(f"📊 Load Balancer: http://localhost:8888")
        print(f"🌐 Web Dashboard: http://localhost:8080")
        print(f"🖥️  Backend Servers: {num_servers} servers running")
        print("=" * 50)
        print("Press Ctrl+C to stop the system")
        
        return True
    
    def stop_all(self):
        """Stop all running processes"""
        if not self.running:
            return
        
        print("\n🛑 Stopping system...")
        
        # Stop processes in reverse order
        for name, process in reversed(list(self.processes.items())):
            try:
                print(f"🛑 Stopping {name}...")
                process.terminate()
                
                # Wait for graceful shutdown
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    print(f"⚠️  {name} didn't stop gracefully, forcing...")
                    process.kill()
                
                print(f"✅ {name} stopped")
                
            except Exception as e:
                print(f"❌ Error stopping {name}: {e}")
        
        self.processes.clear()
        self.running = False
        print("✅ All processes stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all processes"""
        status = {
            'running': self.running,
            'processes': {}
        }
        
        for name, process in self.processes.items():
            status['processes'][name] = {
                'pid': process.pid,
                'alive': process.poll() is None,
                'returncode': process.returncode
            }
        
        return status
    
    def check_health(self) -> bool:
        """Check if all processes are healthy"""
        if not self.running:
            return False
        
        for name, process in self.processes.items():
            if process.poll() is not None:
                print(f"⚠️  {name} process has stopped unexpectedly")
                return False
        
        return True

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enterprise Load Balancer System Manager")
    parser.add_argument("--servers", type=int, default=2, help="Number of backend servers")
    parser.add_argument("--no-dashboard", action="store_true", help="Disable web dashboard")
    parser.add_argument("--status", action="store_true", help="Show system status and exit")
    
    args = parser.parse_args()
    
    manager = SystemManager()
    
    if args.status:
        # Just show status
        status = manager.get_status()
        print(json.dumps(status, indent=2))
        return
    
    try:
        # Start the system
        success = manager.start_all(
            num_servers=args.servers,
            enable_dashboard=not args.no_dashboard
        )
        
        if not success:
            print("❌ Failed to start system")
            sys.exit(1)
        
        # Keep running and monitor health
        while manager.running:
            time.sleep(5)
            
            # Check process health
            if not manager.check_health():
                print("⚠️  Some processes are unhealthy")
                
    except KeyboardInterrupt:
        print("\n🛑 Shutdown requested by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        manager.stop_all()

if __name__ == "__main__":
    main()