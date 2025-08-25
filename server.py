#!/usr/bin/env python3
"""
Enhanced Server for Enterprise Load Balancer
Features:
- Health check endpoints
- Better monitoring and metrics
- Improved error handling
- Connection tracking
- Performance optimization
"""

import socket
import threading
import time
import json
import logging
import signal
import sys
from typing import Optional, List, Generic, TypeVar, Dict, Any
from dataclasses import dataclass, field
from collections import defaultdict, deque
import statistics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

K = TypeVar('K')
V = TypeVar('V')

@dataclass
class ServerMetrics:
    """Server performance metrics"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_response_time: float = 0.0
    response_times: deque = field(default_factory=lambda: deque(maxlen=1000))
    current_connections: int = 0
    max_connections: int = 0
    start_time: float = field(default_factory=time.time)
    
    def record_request(self, success: bool, response_time: float):
        self.total_requests += 1
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
        
        self.total_response_time += response_time
        self.response_times.append(response_time)
    
    def get_stats(self) -> Dict[str, Any]:
        response_times = list(self.response_times)
        return {
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'success_rate': self.successful_requests / max(self.total_requests, 1),
            'avg_response_time': self.total_response_time / max(self.total_requests, 1),
            'p95_response_time': statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else 0,
            'current_connections': self.current_connections,
            'max_connections': self.max_connections,
            'uptime': time.time() - self.start_time
        }

class KeyValuePair(Generic[K, V]):
    def __init__(self, key: K, value: V):
        self.key = key
        self.value = value

class HashMap(Generic[K, V]):
    def __init__(self, initial_capacity: int = 16):
        self.INITIAL_CAPACITY = initial_capacity
        self.buckets: List[List[KeyValuePair[K, V]]] = [[] for _ in range(self.INITIAL_CAPACITY)]
        self.size = 0
        self.lock = threading.RLock()  # Reentrant lock for better performance

    def _get_bucket_index(self, key: K) -> int:
        hash_code = hash(key)
        return abs(hash_code) % len(self.buckets)

    def put(self, key: K, value: V) -> None:
        with self.lock:
            index = self._get_bucket_index(key)
            bucket = self.buckets[index]

            # Check if key already exists
            for entry in bucket:
                if entry.key == key:
                    entry.value = value
                    return

            # Add new entry
            bucket.append(KeyValuePair(key, value))
            self.size += 1

            # Resize if load factor exceeds 0.75
            if self.size / len(self.buckets) > 0.75:
                self._resize()

    def get(self, key: K) -> Optional[V]:
        with self.lock:
            index = self._get_bucket_index(key)
            bucket = self.buckets[index]

            for entry in bucket:
                if entry.key == key:
                    return entry.value
            return None

    def get_or_default(self, key: K, default_value: V) -> V:
        value = self.get(key)
        return value if value is not None else default_value

    def remove(self, key: K) -> Optional[V]:
        with self.lock:
            index = self._get_bucket_index(key)
            bucket = self.buckets[index]

            for i, entry in enumerate(bucket):
                if entry.key == key:
                    removed_entry = bucket.pop(i)
                    self.size -= 1
                    return removed_entry.value
            return None

    def _resize(self) -> None:
        old_buckets = self.buckets
        self.buckets = [[] for _ in range(len(self.buckets) * 2)]
        old_size = self.size
        self.size = 0

        for bucket in old_buckets:
            for entry in bucket:
                self.put(entry.key, entry.value)

    def get_size(self) -> int:
        with self.lock:
            return self.size
    
    def get_all_keys(self) -> List[K]:
        with self.lock:
            keys = []
            for bucket in self.buckets:
                for entry in bucket:
                    keys.append(entry.key)
            return keys

class EnhancedServer:
    def __init__(self, port: int = 12345):
        self.PORT = port
        self.data_store = HashMap[str, str]()
        self.metrics = ServerMetrics()
        self.running = False
        self.server_socket = None
        self.active_connections = set()
        self.connection_lock = threading.Lock()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.stop()
        sys.exit(0)
    
    def _increment_connections(self):
        with self.connection_lock:
            self.metrics.current_connections += 1
            self.metrics.max_connections = max(self.metrics.max_connections, self.metrics.current_connections)
    
    def _decrement_connections(self):
        with self.connection_lock:
            self.metrics.current_connections = max(0, self.metrics.current_connections - 1)
    
    def _handle_health_check(self, client_socket: socket.socket) -> bool:
        """Handle health check requests"""
        try:
            # Send health status
            health_data = {
                "status": "healthy",
                "timestamp": time.time(),
                "port": self.PORT,
                "metrics": self.metrics.get_stats()
            }
            client_socket.send(json.dumps(health_data).encode() + b"\n")
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def _handle_metrics_request(self, client_socket: socket.socket) -> bool:
        """Handle metrics requests"""
        try:
            metrics_data = {
                "server_port": self.PORT,
                "metrics": self.metrics.get_stats(),
                "data_store_size": self.data_store.get_size(),
                "data_store_keys": self.data_store.get_all_keys()[:100]  # Limit to first 100 keys
            }
            client_socket.send(json.dumps(metrics_data).encode() + b"\n")
            return True
        except Exception as e:
            logger.error(f"Metrics request failed: {e}")
            return False
    
    def _handle_data_request(self, client_socket: socket.socket, operation: str) -> bool:
        """Handle data store operations"""
        start_time = time.time()
        success = False
        
        try:
            if operation == "GET":
                key = client_socket.recv(1024).decode().strip()
                if not key:
                    response = "Error: Empty key"
                else:
                    value = self.data_store.get_or_default(key, "Key not found")
                    response = value
                    success = True
                    
            elif operation == "PUT":
                key = client_socket.recv(1024).decode().strip()
                value = client_socket.recv(1024).decode().strip()
                if not key or not value:
                    response = "Error: Key and value required"
                else:
                    self.data_store.put(key, value)
                    response = "PUT operation successful"
                    success = True
                    
            elif operation == "REMOVE":
                key = client_socket.recv(1024).decode().strip()
                if not key:
                    response = "Error: Empty key"
                else:
                    if self.data_store.remove(key) is not None:
                        response = "REMOVE operation successful"
                        success = True
                    else:
                        response = "Key not found for REMOVE operation"
            else:
                response = "Invalid request type"
            
            # Send response
            client_socket.send(f"{response}\n".encode())
            
        except Exception as e:
            logger.error(f"Data request failed: {e}")
            response = "Internal server error"
            client_socket.send(f"{response}\n".encode())
        
        # Record metrics
        response_time = time.time() - start_time
        self.metrics.record_request(success, response_time)
        
        return success
    
    def handle_client(self, client_socket: socket.socket, client_address: tuple):
        """Handle client connection with enhanced error handling"""
        self._increment_connections()
        self.active_connections.add(client_socket)
        
        try:
            logger.info(f"Client connected: {client_address[0]}:{client_address[1]}")
            
            while True:
                # Read request type
                request_type = client_socket.recv(1024).decode().strip()
                if not request_type or request_type == "QUIT":
                    break
                
                logger.info(f"Received request: {request_type} from {client_address[0]}")
                
                # Handle different request types
                if request_type == "HEALTH":
                    self._handle_health_check(client_socket)
                elif request_type == "METRICS":
                    self._handle_metrics_request(client_socket)
                elif request_type in ["GET", "PUT", "REMOVE"]:
                    self._handle_data_request(client_socket, request_type)
                else:
                    logger.warning(f"Unknown request type: {request_type}")
                    client_socket.send("Invalid request type\n".encode())
                
        except Exception as e:
            logger.error(f"Error handling client {client_address}: {e}")
        finally:
            self._decrement_connections()
            self.active_connections.discard(client_socket)
            client_socket.close()
            logger.info(f"Client disconnected: {client_address[0]}:{client_address[1]}")

    def start(self):
        if self.running:
            logger.warning("Server is already running")
            return
        
        # Create server socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind(('0.0.0.0', self.PORT))
            self.server_socket.listen(100)
            self.running = True
            
            logger.info(f"Enhanced Server started on port {self.PORT}")
            logger.info("Available endpoints:")
            logger.info("  - GET/PUT/REMOVE: Data store operations")
            logger.info("  - HEALTH: Health check")
            logger.info("  - METRICS: Server metrics")
            logger.info("  - QUIT: Disconnect")
            
            # Start metrics logging thread
            metrics_thread = threading.Thread(target=self._metrics_logging_loop, daemon=True)
            metrics_thread.start()
            
            while self.running:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    client_thread = threading.Thread(
                        target=self.handle_client, 
                        args=(client_socket, client_address)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except socket.error:
                    if self.running:
                        raise
                    break
                    
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Gracefully stop the server"""
        self.running = False
        
        # Close all active connections
        with self.connection_lock:
            for conn in list(self.active_connections):
                try:
                    conn.close()
                except:
                    pass
            self.active_connections.clear()
        
        # Close server socket
        if self.server_socket:
            self.server_socket.close()
        
        # Log final metrics
        final_stats = self.metrics.get_stats()
        logger.info(f"Server stopped. Final stats: {json.dumps(final_stats, indent=2)}")
    
    def _metrics_logging_loop(self):
        """Periodically log server metrics"""
        while self.running:
            time.sleep(60)  # Log every minute
            stats = self.metrics.get_stats()
            logger.info(f"Server metrics: {json.dumps(stats, indent=2)}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current server status"""
        return {
            'running': self.running,
            'port': self.PORT,
            'metrics': self.metrics.get_stats(),
            'active_connections': len(self.active_connections),
            'data_store_size': self.data_store.get_size()
        }

class ServerCluster:
    """Manages multiple server instances for testing"""
    
    def __init__(self, base_port: int = 12345, num_servers: int = 2):
        self.base_port = base_port
        self.num_servers = num_servers
        self.servers = []
        self.running = False
    
    def start_all(self):
        """Start all servers in the cluster"""
        if self.running:
            logger.warning("Cluster is already running")
            return
        
        self.running = True
        
        for i in range(self.num_servers):
            port = self.base_port + i
            server = EnhancedServer(port)
            self.servers.append(server)
            
            # Start server in a separate thread
            server_thread = threading.Thread(target=server.start, daemon=True)
            server_thread.start()
            
            logger.info(f"Started server {i+1} on port {port}")
        
        logger.info(f"Started {self.num_servers} servers in cluster")
    
    def stop_all(self):
        """Stop all servers in the cluster"""
        self.running = False
        
        for server in self.servers:
            server.stop()
        
        self.servers.clear()
        logger.info("Stopped all servers in cluster")
    
    def get_cluster_status(self) -> Dict[str, Any]:
        """Get status of all servers in the cluster"""
        return {
            'running': self.running,
            'num_servers': len(self.servers),
            'servers': [server.get_status() for server in self.servers]
        }

if __name__ == "__main__":
    import sys
    
    # Allow port to be specified as command line argument
    port = 12345  # default port
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("Invalid port number, using default port 12345")
    
    # Check if we should start a cluster
    if len(sys.argv) > 2 and sys.argv[2] == "cluster":
        num_servers = 2
        if len(sys.argv) > 3:
            try:
                num_servers = int(sys.argv[3])
            except ValueError:
                pass
        
        cluster = ServerCluster(port, num_servers)
        try:
            cluster.start_all()
            # Keep main thread alive
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down cluster...")
            cluster.stop_all()
    else:
        # Start single server
        server = EnhancedServer(port)
        try:
            server.start()
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            server.stop()

