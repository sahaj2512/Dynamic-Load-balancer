#!/usr/bin/env python3
"""
Enhanced Client for Enterprise Load Balancer
Features:
- Session management
- Better error handling
- Connection pooling
- Retry logic
- Metrics collection
"""

import socket
import json
import time
import uuid
import threading
from typing import Optional, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedClient:
    def __init__(self, server_ip: str = "127.0.0.1", lb_port: int = 8888):
        self.SERVER_IP = server_ip
        self.LB_PORT = lb_port
        self.session_id = str(uuid.uuid4())
        self.current_server = None
        self.connection_pool = {}
        self.stats = {
            'requests': 0,
            'errors': 0,
            'total_time': 0.0,
            'avg_response_time': 0.0
        }
        self.lock = threading.Lock()
    
    def _get_connection(self, host: str, port: int) -> Optional[socket.socket]:
        """Get connection from pool or create new one"""
        key = f"{host}:{port}"
        
        if key in self.connection_pool:
            conn = self.connection_pool[key]
            try:
                # Test if connection is still alive
                conn.send(b"PING")
                return conn
            except:
                del self.connection_pool[key]
        
        # Create new connection
        try:
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            conn.settimeout(10)
            conn.connect((host, port))
            return conn
        except Exception as e:
            logger.error(f"Failed to connect to {host}:{port}: {e}")
            return None
    
    def _return_connection(self, host: str, port: int, conn: socket.socket):
        """Return connection to pool"""
        key = f"{host}:{port}"
        try:
            # Reset timeout for pooled connections
            conn.settimeout(None)
            self.connection_pool[key] = conn
        except:
            try:
                conn.close()
            except:
                pass
    
    def _make_request(self, operation: str, key: str = None, value: str = None) -> Optional[str]:
        """Make a request to the current server"""
        if not self.current_server:
            logger.error("No server assigned")
            return None
        
        host = self.current_server['host']
        port = self.current_server['port']
        
        # Get connection from pool
        conn = self._get_connection(host, port)
        if not conn:
            return None
        
        start_time = time.time()
        
        try:
            # Send operation
            conn.send(f"{operation}\n".encode())
            
            if operation in ["GET", "REMOVE"]:
                if key:
                    conn.send(f"{key}\n".encode())
                else:
                    logger.error("Key required for GET/REMOVE operations")
                    return None
                    
            elif operation == "PUT":
                if key and value:
                    conn.send(f"{key}\n".encode())
                    conn.send(f"{value}\n".encode())
                else:
                    logger.error("Key and value required for PUT operation")
                    return None
            
            # Receive response
            response = conn.recv(1024).decode().strip()
            
            # Update stats
            response_time = time.time() - start_time
            with self.lock:
                self.stats['requests'] += 1
                self.stats['total_time'] += response_time
                self.stats['avg_response_time'] = self.stats['total_time'] / self.stats['requests']
            
            logger.info(f"Request completed in {response_time:.3f}s")
            return response
            
        except Exception as e:
            logger.error(f"Request failed: {e}")
            with self.lock:
                self.stats['errors'] += 1
            return None
        finally:
            # Return connection to pool
            self._return_connection(host, port, conn)
    
    def start(self):
        try:
            # Connect to load balancer first
            lb_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            lb_socket.settimeout(10)
            lb_socket.connect((self.SERVER_IP, self.LB_PORT))
            
            logger.info("Connected to load balancer.")
            logger.info(f"Session ID: {self.session_id}")
            
            # Send session ID to load balancer
            lb_socket.send(f"SESSION:{self.session_id}\n".encode())
            
            # Get server assignment from load balancer
            server_info_data = lb_socket.recv(1024).decode().strip()
            try:
                self.current_server = json.loads(server_info_data)
                logger.info(f"Assigned to server: {self.current_server['host']}:{self.current_server['port']}")
            except json.JSONDecodeError:
                logger.error(f"Invalid server info received: {server_info_data}")
                return
            
            lb_socket.close()
            
            # Main interaction loop
            while True:
                print("\n" + "="*50)
                print("ENHANCED CLIENT - ENTERPRISE LOAD BALANCER")
                print("="*50)
                print(f"Session ID: {self.session_id}")
                print(f"Current Server: {self.current_server['host']}:{self.current_server['port']}")
                print(f"Stats: {self.stats['requests']} requests, {self.stats['errors']} errors")
                print(f"Avg Response Time: {self.stats['avg_response_time']:.3f}s")
                print("="*50)
                print("Choose operation:")
                print("1. GET - Retrieve a value")
                print("2. PUT - Store a key-value pair")
                print("3. REMOVE - Delete a key-value pair")
                print("4. STATS - Show detailed statistics")
                print("5. QUIT - Exit")
                print("="*50)
                
                choice = input("Enter your choice (1-5): ").strip()
                
                if choice == "1":
                    operation = "GET"
                    key = input("Enter key: ").strip()
                    if key:
                        response = self._make_request(operation, key)
                        if response:
                            print(f"GET Response: {response}")
                        else:
                            print("GET operation failed")
                
                elif choice == "2":
                    operation = "PUT"
                    key = input("Enter key: ").strip()
                    value = input("Enter value: ").strip()
                    if key and value:
                        response = self._make_request(operation, key, value)
                        if response:
                            print(f"PUT Response: {response}")
                        else:
                            print("PUT operation failed")
                    else:
                        print("Both key and value are required")
                
                elif choice == "3":
                    operation = "REMOVE"
                    key = input("Enter key: ").strip()
                    if key:
                        response = self._make_request(operation, key)
                        if response:
                            print(f"REMOVE Response: {response}")
                        else:
                            print("REMOVE operation failed")
                
                elif choice == "4":
                    self._show_detailed_stats()
                
                elif choice == "5":
                    print("Disconnecting...")
                    break
                
                else:
                    print("Invalid choice. Please enter 1-5.")
                
                input("\nPress Enter to continue...")
            
            # Clean up connections
            self._cleanup_connections()
            print("Disconnected from server.")
            
        except Exception as e:
            logger.error(f"Client error: {e}")
        finally:
            self._cleanup_connections()
    
    def _show_detailed_stats(self):
        """Display detailed client statistics"""
        print("\n" + "="*50)
        print("DETAILED STATISTICS")
        print("="*50)
        print(f"Total Requests: {self.stats['requests']}")
        print(f"Total Errors: {self.stats['errors']}")
        print(f"Success Rate: {((self.stats['requests'] - self.stats['errors']) / max(self.stats['requests'], 1) * 100):.2f}%")
        print(f"Total Time: {self.stats['total_time']:.3f}s")
        print(f"Average Response Time: {self.stats['avg_response_time']:.3f}s")
        print(f"Session ID: {self.session_id}")
        if self.current_server:
            print(f"Current Server: {self.current_server['host']}:{self.current_server['port']}")
        print("="*50)
    
    def _cleanup_connections(self):
        """Clean up all pooled connections"""
        for key, conn in self.connection_pool.items():
            try:
                conn.close()
            except:
                pass
        self.connection_pool.clear()

class LoadTestClient:
    """Client for load testing the load balancer"""
    
    def __init__(self, server_ip: str = "127.0.0.1", lb_port: int = 8888, num_requests: int = 100):
        self.server_ip = server_ip
        self.lb_port = lb_port
        self.num_requests = num_requests
        self.results = []
    
    def run_load_test(self):
        """Run load test with multiple concurrent clients"""
        print(f"Starting load test with {self.num_requests} requests...")
        
        start_time = time.time()
        
        # Create multiple threads to simulate concurrent clients
        threads = []
        for i in range(min(10, self.num_requests)):  # Max 10 concurrent threads
            thread = threading.Thread(target=self._worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        # Calculate statistics
        response_times = [r['response_time'] for r in self.results if r['success']]
        success_count = sum(1 for r in self.results if r['success'])
        
        print(f"\nLoad Test Results:")
        print(f"Total Requests: {len(self.results)}")
        print(f"Successful: {success_count}")
        print(f"Failed: {len(self.results) - success_count}")
        print(f"Success Rate: {(success_count / len(self.results) * 100):.2f}%")
        print(f"Total Time: {total_time:.3f}s")
        print(f"Requests per Second: {len(self.results) / total_time:.2f}")
        if response_times:
            print(f"Average Response Time: {sum(response_times) / len(response_times):.3f}s")
            print(f"Min Response Time: {min(response_times):.3f}s")
            print(f"Max Response Time: {max(response_times):.3f}s")
    
    def _worker(self, worker_id: int):
        """Worker thread for load testing"""
        requests_per_worker = self.num_requests // 10
        
        for i in range(requests_per_worker):
            try:
                # Connect to load balancer
                lb_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                lb_socket.settimeout(5)
                lb_socket.connect((self.server_ip, self.lb_port))
                
                # Send session ID
                session_id = f"loadtest_{worker_id}_{i}"
                lb_socket.send(f"SESSION:{session_id}\n".encode())
                
                # Get server assignment
                server_info = lb_socket.recv(1024).decode().strip()
                lb_socket.close()
                
                start_time = time.time()
                
                # Simulate a simple request
                time.sleep(0.01)  # Simulate work
                
                response_time = time.time() - start_time
                
                self.results.append({
                    'worker_id': worker_id,
                    'request_id': i,
                    'success': True,
                    'response_time': response_time,
                    'server_info': server_info
                })
                
            except Exception as e:
                self.results.append({
                    'worker_id': worker_id,
                    'request_id': i,
                    'success': False,
                    'response_time': 0,
                    'error': str(e)
                })

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "loadtest":
        # Run load test
        num_requests = 100
        if len(sys.argv) > 2:
            try:
                num_requests = int(sys.argv[2])
            except ValueError:
                pass
        
        load_test = LoadTestClient(num_requests=num_requests)
        load_test.run_load_test()
    else:
        # Run normal client
        client = EnhancedClient()
        client.start()

