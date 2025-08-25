#!/usr/bin/env python3
"""
Enterprise Load Balancer Monitor and Management Tool
Features:
- Real-time monitoring of load balancer and servers
- Health check automation
- Performance metrics collection
- Configuration management
- Alert system
- Web dashboard (basic)
"""

import socket
import json
import time
import threading
import logging
import argparse
import sys
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import statistics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class SystemHealth:
    """System health status"""
    timestamp: float
    load_balancer_healthy: bool = True
    servers_healthy: List[bool] = field(default_factory=list)
    overall_health: str = "healthy"
    alerts: List[str] = field(default_factory=list)

class LoadBalancerMonitor:
    """Monitors the entire load balancer system"""
    
    def __init__(self, lb_host: str = "127.0.0.1", lb_port: int = 8888):
        self.lb_host = lb_host
        self.lb_port = lb_port
        self.running = False
        self.health_history: List[SystemHealth] = []
        self.alert_history: List[Dict[str, Any]] = []
        self.monitoring_thread = None
        
        # Configuration
        self.health_check_interval = 30  # seconds
        self.alert_thresholds = {
            'error_rate': 0.1,  # 10% error rate
            'response_time': 2.0,  # 2 seconds
            'connection_utilization': 0.8  # 80% connection usage
        }
    
    def start_monitoring(self):
        """Start the monitoring system"""
        if self.running:
            logger.warning("Monitoring is already running")
            return
        
        self.running = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info("Started load balancer monitoring")
    
    def stop_monitoring(self):
        """Stop the monitoring system"""
        self.running = False
        if self.monitoring_thread:
            self.monitoring_thread.join()
        logger.info("Stopped load balancer monitoring")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                health_status = self._check_system_health()
                self.health_history.append(health_status)
                
                # Keep only last 100 health checks
                if len(self.health_history) > 100:
                    self.health_history.pop(0)
                
                # Check for alerts
                alerts = self._check_alerts(health_status)
                if alerts:
                    self._trigger_alerts(alerts)
                
                # Log health status
                logger.info(f"System Health: {health_status.overall_health}")
                if health_status.alerts:
                    logger.warning(f"Active Alerts: {', '.join(health_status.alerts)}")
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
            
            time.sleep(self.health_check_interval)
    
    def _check_system_health(self) -> SystemHealth:
        """Check the health of the entire system"""
        health = SystemHealth(timestamp=time.time())
        
        try:
            # Check load balancer health
            lb_health = self._check_load_balancer_health()
            health.load_balancer_healthy = lb_health
            
            # Check server health
            server_healths = self._check_server_health()
            health.servers_healthy = server_healths
            
            # Determine overall health
            if not health.load_balancer_healthy:
                health.overall_health = "critical"
                health.alerts.append("Load balancer is down")
            elif not all(health.servers_healthy):
                health.overall_health = "warning"
                health.alerts.append("Some servers are unhealthy")
            else:
                health.overall_health = "healthy"
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            health.overall_health = "unknown"
            health.alerts.append(f"Health check failed: {e}")
        
        return health
    
    def _check_load_balancer_health(self) -> bool:
        """Check if load balancer is responding"""
        try:
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((self.lb_host, self.lb_port))
            return True
        except:
            return False
    
    def _check_server_health(self) -> List[bool]:
        """Check health of all backend servers"""
        server_healths = []
        
        # Check default server ports
        for port in [12345, 12346]:
            try:
                # Try to connect and send health check
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                sock.connect(('127.0.0.1', port))
                
                # Send health check request
                sock.send(b"HEALTH\n")
                response = sock.recv(1024).decode().strip()
                sock.close()
                
                # Parse health response
                try:
                    health_data = json.loads(response)
                    server_healths.append(health_data.get('status') == 'healthy')
                except:
                    server_healths.append(True)  # Assume healthy if response is not JSON
                    
            except Exception as e:
                logger.warning(f"Server {port} health check failed: {e}")
                server_healths.append(False)
        
        return server_healths
    
    def _check_alerts(self, health: SystemHealth) -> List[str]:
        """Check if any alerts should be triggered"""
        alerts = []
        
        # Check recent error rates
        if len(self.health_history) >= 5:
            recent_health = self.health_history[-5:]
            error_count = sum(1 for h in recent_health if h.overall_health != "healthy")
            error_rate = error_count / len(recent_health)
            
            if error_rate > self.alert_thresholds['error_rate']:
                alerts.append(f"High error rate: {error_rate:.2%}")
        
        # Check for sustained unhealthy status
        if len(self.health_history) >= 3:
            recent_unhealthy = all(h.overall_health != "healthy" for h in self.health_history[-3:])
            if recent_unhealthy:
                alerts.append("Sustained unhealthy status")
        
        return alerts
    
    def _trigger_alerts(self, alerts: List[str]):
        """Trigger alerts (log them for now, could be extended to email/SMS)"""
        for alert in alerts:
            alert_data = {
                'timestamp': time.time(),
                'message': alert,
                'severity': 'warning'
            }
            self.alert_history.append(alert_data)
            logger.warning(f"ALERT: {alert}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        if not self.health_history:
            return {'status': 'no_data'}
        
        latest_health = self.health_history[-1]
        
        # Calculate uptime and availability
        uptime = time.time() - self.health_history[0].timestamp
        healthy_checks = sum(1 for h in self.health_history if h.overall_health == "healthy")
        availability = healthy_checks / len(self.health_history)
        
        return {
            'current_status': latest_health.overall_health,
            'load_balancer_healthy': latest_health.load_balancer_healthy,
            'servers_healthy': latest_health.servers_healthy,
            'uptime_seconds': uptime,
            'availability': availability,
            'active_alerts': latest_health.alerts,
            'last_check': latest_health.timestamp,
            'total_health_checks': len(self.health_history)
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics from servers"""
        metrics = {}
        
        for port in [12345, 12346]:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                sock.connect(('127.0.0.1', port))
                
                sock.send(b"METRICS\n")
                response = sock.recv(4096).decode().strip()
                sock.close()
                
                try:
                    server_metrics = json.loads(response)
                    metrics[f'server_{port}'] = server_metrics
                except:
                    logger.warning(f"Failed to parse metrics from server {port}")
                    
            except Exception as e:
                logger.warning(f"Failed to get metrics from server {port}: {e}")
        
        return metrics

class ConfigurationManager:
    """Manages load balancer configuration"""
    
    def __init__(self, config_file: str = "load_balancer_config.json"):
        self.config_file = config_file
    
    def load_config(self) -> Dict[str, Any]:
        """Load current configuration"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file {self.config_file} not found")
            return {}
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}
    
    def save_config(self, config: Dict[str, Any]):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def update_config(self, updates: Dict[str, Any]):
        """Update configuration with new values"""
        config = self.load_config()
        config.update(updates)
        self.save_config(config)
    
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate configuration values"""
        errors = []
        
        if 'port' in config and (not isinstance(config['port'], int) or config['port'] < 1 or config['port'] > 65535):
            errors.append("Port must be an integer between 1 and 65535")
        
        if 'algorithm' in config and config['algorithm'] not in ['round_robin', 'least_connections', 'weighted_round_robin', 'ip_hash', 'least_response_time']:
            errors.append("Invalid load balancing algorithm")
        
        if 'health_check_interval' in config and (not isinstance(config['health_check_interval'], (int, float)) or config['health_check_interval'] < 1):
            errors.append("Health check interval must be a number >= 1")
        
        return errors

class WebDashboard:
    """Simple web dashboard for monitoring"""
    
    def __init__(self, monitor: LoadBalancerMonitor, config_manager: ConfigurationManager):
        self.monitor = monitor
        self.config_manager = config_manager
        self.running = False
    
    def generate_html(self) -> str:
        """Generate HTML dashboard"""
        status = self.monitor.get_system_status()
        metrics = self.monitor.get_performance_metrics()
        config = self.config_manager.load_config()
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Enterprise Load Balancer Dashboard</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
        .status-card {{ background: white; padding: 20px; margin: 10px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .status-{status['current_status']} {{ border-left: 5px solid {'#28a745' if status['current_status'] == 'healthy' else '#ffc107' if status['current_status'] == 'warning' else '#dc3545'}; }}
        .metric {{ display: inline-block; margin: 10px; padding: 15px; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); min-width: 200px; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #667eea; }}
        .metric-label {{ color: #666; font-size: 14px; }}
        .alert {{ background: #fff3cd; border: 1px solid #ffeaa7; color: #856404; padding: 10px; border-radius: 5px; margin: 10px 0; }}
        .refresh-btn {{ background: #667eea; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin: 10px 0; }}
        .refresh-btn:hover {{ background: #5a6fd8; }}
    </style>
    <script>
        function refreshDashboard() {{
            location.reload();
        }}
        // Auto-refresh every 30 seconds
        setInterval(refreshDashboard, 30000);
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Enterprise Load Balancer Dashboard</h1>
            <p>Real-time monitoring and management</p>
        </div>
        
        <div class="status-card status-{status['current_status']}">
            <h2>System Status: {status['current_status'].upper()}</h2>
            <p>Last Updated: {datetime.fromtimestamp(status['last_check']).strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>Load Balancer: {'🟢 Healthy' if status['load_balancer_healthy'] else '🔴 Down'}</p>
            <p>Servers: {'🟢 All Healthy' if all(status['servers_healthy']) else '🟡 Some Issues'}</p>
        </div>
        
        <div class="status-card">
            <h3>Performance Metrics</h3>
            <div class="metric">
                <div class="metric-value">{status['availability']:.1%}</div>
                <div class="metric-label">Availability</div>
            </div>
            <div class="metric">
                <div class="metric-value">{status['uptime_seconds']/3600:.1f}h</div>
                <div class="metric-label">Uptime</div>
            </div>
            <div class="metric">
                <div class="metric-value">{status['total_health_checks']}</div>
                <div class="metric-label">Health Checks</div>
            </div>
        </div>
        
        <div class="status-card">
            <h3>Server Metrics</h3>
            {self._generate_server_metrics_html(metrics)}
        </div>
        
        <div class="status-card">
            <h3>Configuration</h3>
            <pre>{json.dumps(config, indent=2)}</pre>
        </div>
        
        {self._generate_alerts_html(status)}
        
        <button class="refresh-btn" onclick="refreshDashboard()">🔄 Refresh Dashboard</button>
    </div>
</body>
</html>
        """
        return html
    
    def _generate_server_metrics_html(self, metrics: Dict[str, Any]) -> str:
        """Generate HTML for server metrics"""
        if not metrics:
            return "<p>No server metrics available</p>"
        
        html = ""
        for server_id, server_metrics in metrics.items():
            if 'metrics' in server_metrics:
                m = server_metrics['metrics']
                html += f"""
                <div class="metric">
                    <h4>{server_id}</h4>
                    <div class="metric-value">{m.get('success_rate', 0):.1%}</div>
                    <div class="metric-label">Success Rate</div>
                    <div class="metric-value">{m.get('avg_response_time', 0):.3f}s</div>
                    <div class="metric-label">Avg Response Time</div>
                    <div class="metric-value">{m.get('current_connections', 0)}</div>
                    <div class="metric-label">Current Connections</div>
                </div>
                """
        
        return html
    
    def _generate_alerts_html(self, status: Dict[str, Any]) -> str:
        """Generate HTML for alerts"""
        if not status.get('active_alerts'):
            return ""
        
        alerts_html = '<div class="status-card"><h3>⚠️ Active Alerts</h3>'
        for alert in status['active_alerts']:
            alerts_html += f'<div class="alert">{alert}</div>'
        alerts_html += '</div>'
        return alerts_html

def main():
    parser = argparse.ArgumentParser(description="Enterprise Load Balancer Monitor")
    parser.add_argument("--lb-host", default="127.0.0.1", help="Load balancer host")
    parser.add_argument("--lb-port", type=int, default=8888, help="Load balancer port")
    parser.add_argument("--config-file", default="load_balancer_config.json", help="Configuration file")
    parser.add_argument("--web-dashboard", action="store_true", help="Start web dashboard")
    parser.add_argument("--monitor-only", action="store_true", help="Monitor only mode")
    
    args = parser.parse_args()
    
    # Initialize components
    monitor = LoadBalancerMonitor(args.lb_host, args.lb_port)
    config_manager = ConfigurationManager(args.config_file)
    
    try:
        if args.web_dashboard:
            # Start web dashboard
            dashboard = WebDashboard(monitor, config_manager)
            print("Starting web dashboard...")
            print("Open your browser and navigate to: http://localhost:8080")
            
            # Simple HTTP server for dashboard
            import http.server
            import socketserver
            
            class DashboardHandler(http.server.SimpleHTTPRequestHandler):
                def do_GET(self):
                    if self.path == '/':
                        self.send_response(200)
                        self.send_header('Content-type', 'text/html')
                        self.end_headers()
                        self.wfile.write(dashboard.generate_html().encode())
                    else:
                        super().do_GET()
            
            with socketserver.TCPServer(("", 8080), DashboardHandler) as httpd:
                print("Dashboard server started on port 8080")
                httpd.serve_forever()
        
        elif args.monitor_only:
            # Monitor only mode
            monitor.start_monitoring()
            print("Monitoring started. Press Ctrl+C to stop.")
            
            try:
                while True:
                    status = monitor.get_system_status()
                    print(f"\n{'='*50}")
                    print(f"System Status: {status['current_status'].upper()}")
                    print(f"Load Balancer: {'Healthy' if status['load_balancer_healthy'] else 'Down'}")
                    print(f"Servers: {status['servers_healthy']}")
                    print(f"Availability: {status['availability']:.1%}")
                    print(f"Uptime: {status['uptime_seconds']/3600:.1f} hours")
                    
                    if status['active_alerts']:
                        print(f"Alerts: {', '.join(status['active_alerts'])}")
                    
                    time.sleep(10)
                    
            except KeyboardInterrupt:
                print("\nStopping monitoring...")
                monitor.stop_monitoring()
        
        else:
            # Interactive mode
            monitor.start_monitoring()
            print("Enterprise Load Balancer Monitor")
            print("Commands: status, metrics, config, alerts, quit")
            
            while True:
                try:
                    command = input("\n> ").strip().lower()
                    
                    if command == "quit":
                        break
                    elif command == "status":
                        status = monitor.get_system_status()
                        print(json.dumps(status, indent=2))
                    elif command == "metrics":
                        metrics = monitor.get_performance_metrics()
                        print(json.dumps(metrics, indent=2))
                    elif command == "config":
                        config = config_manager.load_config()
                        print(json.dumps(config, indent=2))
                    elif command == "alerts":
                        if monitor.alert_history:
                            for alert in monitor.alert_history[-5:]:  # Show last 5 alerts
                                print(f"{datetime.fromtimestamp(alert['timestamp'])}: {alert['message']}")
                        else:
                            print("No alerts")
                    else:
                        print("Unknown command. Available: status, metrics, config, alerts, quit")
                        
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"Error: {e}")
            
            monitor.stop_monitoring()
    
    except KeyboardInterrupt:
        print("\nShutting down...")
        monitor.stop_monitoring()

if __name__ == "__main__":
    main()