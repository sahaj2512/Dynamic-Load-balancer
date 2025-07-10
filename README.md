# Dynamic Load Balancer

A Python implementation of a dynamic load balancer with key-value store servers, featuring round-robin load balancing, custom HashMap implementation, and multi-threaded client-server architecture.

## Components

### 1. Load Balancer (`load_balancer.py`)
- Implements round-robin load balancing algorithm
- Distributes client requests across multiple servers
- Handles concurrent client connections using threading
- Default port: 8888

### 2. Server (`server.py`)
- Key-value store server with custom HashMap implementation
- Supports GET, PUT, and REMOVE operations
- Generic type support with TypeVar
- Automatic resizing with load factor management
- Multi-threaded client handling
- Default ports: 12345, 12346

### 3. Client (`client.py`)
- Interactive client interface
- Connects to load balancer for server assignment
- Supports all CRUD operations on the key-value store
- Graceful connection handling

## Features

- **Round-Robin Load Balancing**: Evenly distributes requests across available servers
- **Custom HashMap**: Efficient key-value storage with collision handling and dynamic resizing
- **Thread Safety**: Concurrent request handling with proper resource management
- **Generic Types**: Type-safe implementation using Python's typing system
- **Socket Programming**: TCP-based communication between components
- **Error Handling**: Robust error handling and connection management

## Usage

1. **Start the servers** (in separate terminals):
   ```bash
   python3 server.py 12345
   python3 server.py 12346
   ```

2. **Start the load balancer**:
   ```bash
   python3 load_balancer.py
   ```

3. **Run the client**:
   ```bash
   python3 client.py
   ```

## Interview Preparation

This project serves as an excellent foundation for technical interviews. See [`INTERVIEW_QUESTIONS.md`](INTERVIEW_QUESTIONS.md) for **50 comprehensive interview questions** covering:

- Load balancing concepts and algorithms
- Network programming with sockets
- Threading and concurrency
- Data structures and algorithms
- System design principles
- Python programming concepts
- Distributed systems
- Performance optimization
- Error handling and reliability

## Architecture

```
Client → Load Balancer → Server Pool
                      ├── Server 1 (Port 12345)
                      └── Server 2 (Port 12346)
```

## Technical Highlights

- **Scalable Architecture**: Easy to add more servers to the pool
- **Efficient Data Structures**: O(1) average case HashMap operations
- **Concurrent Processing**: Multi-threaded server and load balancer
- **Type Safety**: Generic implementation with proper type annotations
- **Resource Management**: Proper socket cleanup and daemon threading

## Learning Objectives

This implementation demonstrates:
- Distributed system design patterns
- Network programming fundamentals
- Data structure implementation
- Concurrent programming concepts
- Python best practices
- System architecture principles

Perfect for understanding the fundamentals of load balancing, distributed systems, and preparing for technical interviews in system design and backend engineering roles.