# 🚀 Enterprise-Grade Load Balancer

A production-ready, feature-rich load balancer built in Python with enterprise-level capabilities including multiple algorithms, health checking, monitoring, and more.

## ✨ Features

### 🔄 Load Balancing Algorithms
- **Round Robin**: Distributes requests evenly across servers
- **Least Connections**: Routes to server with fewest active connections
- **Weighted Round Robin**: Distributes based on server weights
- **IP Hash**: Consistent hashing for session persistence
- **Least Response Time**: Routes to fastest responding server

### 🏥 Health Monitoring
- Automatic health checks for backend servers
- Failover and recovery mechanisms
- Real-time server status monitoring
- Configurable health check intervals

### 🛡️ Security & Protection
- Rate limiting (DDoS protection)
- Connection pooling
- SSL/TLS termination support
- Session persistence (sticky sessions)

### 📊 Monitoring & Metrics
- Real-time performance metrics
- Response time tracking
- Error rate monitoring
- Connection utilization tracking
- Web dashboard for visualization

### ⚙️ Configuration Management
- JSON-based configuration
- Runtime configuration updates
- Validation and error checking
- Multiple environment support

### 🔧 Advanced Features
- Graceful shutdown handling
- Connection limits per server
- Automatic failover
- Comprehensive logging
- Thread-safe operations

## 🚀 Quick Start

### 1. Start the Load Balancer

```bash
# Start with default configuration
python3 load_balancer.py

# Or start with custom config
python3 load_balancer.py --config custom_config.json
```

### 2. Start Backend Servers

```bash
# Start single server
python3 server.py 12345

# Start server cluster (multiple servers)
python3 server.py 12345 cluster 3
```

### 3. Connect with Client

```bash
# Interactive client
python3 client.py

# Load testing
python3 client.py loadtest 1000
```

### 4. Monitor the System

```bash
# Interactive monitoring
python3 monitor.py

# Web dashboard
python3 monitor.py --web-dashboard

# Monitor only mode
python3 monitor.py --monitor-only
```

## 📁 File Structure

```
├── load_balancer.py          # Main load balancer implementation
├── server.py                 # Enhanced backend server
├── client.py                 # Enhanced client with session support
├── monitor.py                # Monitoring and management tool
├── load_balancer_config.json # Configuration file
└── README.md                 # This file
```

## ⚙️ Configuration

The load balancer is configured via `load_balancer_config.json`:

```json
{
  "port": 8888,
  "algorithm": "least_connections",
  "health_check_interval": 30.0,
  "connection_timeout": 30.0,
  "max_connections_per_server": 100,
  "rate_limit_requests_per_minute": 1000,
  "enable_ssl": false,
  "ssl_cert_file": "",
  "ssl_key_file": "",
  "session_timeout": 300,
  "enable_sticky_sessions": true,
  "log_level": "INFO"
}
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `port` | int | 8888 | Load balancer listening port |
| `algorithm` | string | "least_connections" | Load balancing algorithm |
| `health_check_interval` | float | 30.0 | Health check frequency (seconds) |
| `connection_timeout` | float | 30.0 | Connection timeout (seconds) |
| `max_connections_per_server` | int | 100 | Max connections per backend server |
| `rate_limit_requests_per_minute` | int | 1000 | Rate limiting threshold |
| `enable_ssl` | bool | false | Enable SSL/TLS termination |
| `session_timeout` | int | 300 | Session timeout (seconds) |
| `enable_sticky_sessions` | bool | true | Enable session persistence |

## 🔄 Load Balancing Algorithms

### Round Robin
- **Use Case**: Simple, even distribution
- **Pros**: Simple, predictable
- **Cons**: Doesn't consider server load

### Least Connections
- **Use Case**: Dynamic load distribution
- **Pros**: Adapts to server load
- **Cons**: May not consider response time

### Weighted Round Robin
- **Use Case**: Servers with different capacities
- **Pros**: Respects server weights
- **Cons**: Static weight assignment

### IP Hash
- **Use Case**: Session persistence
- **Pros**: Consistent routing
- **Cons**: May not distribute evenly

### Least Response Time
- **Use Case**: Performance optimization
- **Pros**: Routes to fastest server
- **Cons**: Requires response time tracking

## 🏥 Health Checking

The load balancer automatically monitors backend server health:

- **Active Health Checks**: Regular connectivity tests
- **Passive Health Checks**: Response time and error rate monitoring
- **Automatic Failover**: Unhealthy servers are removed from rotation
- **Recovery**: Healthy servers are automatically re-added

## 📊 Monitoring & Metrics

### Real-time Metrics
- Request count and rate
- Response times (average, P95)
- Error rates
- Connection utilization
- Server health status

### Web Dashboard
Access the web dashboard at `http://localhost:8080` to view:
- System status overview
- Performance metrics
- Server health
- Active alerts
- Configuration details

### Command-line Monitoring
```bash
# Start monitoring
python3 monitor.py

# Available commands:
# status    - Show system status
# metrics   - Show performance metrics
# config    - Show configuration
# alerts    - Show active alerts
# quit      - Exit monitoring
```

## 🧪 Testing & Load Testing

### Load Testing
```bash
# Run load test with 1000 requests
python3 client.py loadtest 1000

# Run load test with 10000 requests
python3 client.py loadtest 10000
```

### Performance Testing
The system includes built-in performance testing capabilities:
- Concurrent client simulation
- Response time measurement
- Throughput analysis
- Error rate calculation

## 🔧 Advanced Usage

### Custom Server Configuration
```python
from load_balancer import EnterpriseLoadBalancer, LoadBalancerConfig

# Create custom configuration
config = LoadBalancerConfig(
    algorithm=LoadBalancingAlgorithm.WEIGHTED_ROUND_ROBIN,
    health_check_interval=15.0,
    rate_limit_requests_per_minute=500
)

# Create and start load balancer
lb = EnterpriseLoadBalancer(config)
lb.add_backend_server("server1.example.com", 8080, weight=2)
lb.add_backend_server("server2.example.com", 8080, weight=1)
lb.start()
```

### Health Check Customization
```python
# Custom health check implementation
class CustomHealthChecker(HealthChecker):
    def _check_all_servers(self):
        for server in self.config.backend_servers:
            # Implement custom health check logic
            server.is_healthy = self._custom_health_check(server)
```

### Metrics Collection
```python
# Access metrics
metrics = lb.metrics.get_stats()
print(f"Total requests: {metrics['total_requests']}")
print(f"Error rate: {metrics['error_rate']:.2%}")
print(f"Average response time: {metrics['avg_response_time']:.3f}s")
```

## 🚨 Troubleshooting

### Common Issues

#### Load Balancer Won't Start
- Check if port 8888 is available
- Verify configuration file syntax
- Check log files for errors

#### Backend Servers Not Responding
- Ensure servers are running on correct ports
- Check firewall settings
- Verify server health check endpoints

#### High Error Rates
- Check backend server logs
- Verify server capacity
- Adjust rate limiting settings

#### Performance Issues
- Monitor connection limits
- Check server response times
- Consider adjusting load balancing algorithm

### Log Files
- **Load Balancer**: `load_balancer.log`
- **Servers**: Console output with structured logging
- **Monitor**: Console output with health status

## 🔒 Security Considerations

### Rate Limiting
- Configurable per-minute request limits
- IP-based rate limiting
- DDoS protection

### Connection Security
- Connection pooling
- Timeout handling
- Graceful connection termination

### SSL/TLS Support
- SSL certificate configuration
- TLS termination
- Secure communication

## 📈 Performance Optimization

### Connection Pooling
- Reuse connections when possible
- Reduce connection overhead
- Improve response times

### Algorithm Selection
- **High traffic**: Use Least Connections
- **Session-based**: Use IP Hash
- **Performance**: Use Least Response Time
- **Simple**: Use Round Robin

### Server Configuration
- Adjust connection limits based on server capacity
- Configure appropriate health check intervals
- Set reasonable timeouts

## 🤝 Contributing

This load balancer is designed to be extensible. Key areas for contribution:

- Additional load balancing algorithms
- Enhanced health checking mechanisms
- More monitoring backends
- Performance optimizations
- Security enhancements

## 📄 License

This project is open source and available under the MIT License.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review log files
3. Verify configuration
4. Test with minimal setup

---

**Built with ❤️ for production environments**