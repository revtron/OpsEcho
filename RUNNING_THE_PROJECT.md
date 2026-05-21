# How to Run OpsEcho

## Prerequisites
- Docker Engine (v20.10+)
- Docker Compose (v2.0+)
- Approximately 6-8GB RAM available
- Approximately 10GB disk space

## Quick Start

1. Clone this repository
2. Navigate to the project directory
3. Start all services:

```bash
docker-compose up --build
```

4. Wait for services to initialize (first startup may take 2-3 minutes to download Ollama model)
5. Access the application:
   - Frontend UI: http://localhost:3000
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

## Services Started

- **postgres**: PostgreSQL 15 database for storing events and embeddings
- **ollama**: Local LLM server running Mistral 7B Q4 model
- **backend**: FastAPI application providing REST APIs
- **frontend**: Next.js application providing the user interface

## Testing the System

Once all services are running, you can test the system:

### 1. Send a Test Event
```bash
curl -X POST http://localhost:8000/api/events/k8s \
  -H "Content-Type: application/json" \
  -d '{
    "type": "Pod",
    "name": "test-app-123",
    "namespace": "default",
    "status": "Running",
    "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"
  }'
```

### 2. Check the Timeline
Visit http://localhost:3000 to see the event in the timeline

### 3. Search Events
```bash
curl "http://localhost:8000/api/search?q=test%20app"
```

### 4. View API Documentation
Visit http://localhost:8000/docs to explore all available endpoints

## Stopping the System

To stop all services:
```bash
docker-compose down
```

To stop and remove volumes (including database data):
```bash
docker-compose down -v
```

## Notes

- The first startup will download the Mistral 7B model (~4GB) which may take several minutes
- The system is designed to run on CPU-only hardware
- All data is persisted in Docker volumes (postgres_data, ollama_data)
- For production use, consider setting proper resource limits and security configurations

## Troubleshooting

If services fail to start:
1. Check Docker logs: `docker-compose logs [service-name]`
2. Ensure sufficient RAM is available (minimum 4GB recommended)
3. Verify Docker daemon is running properly
4. Check port conflicts (5432, 11434, 8000, 3000)