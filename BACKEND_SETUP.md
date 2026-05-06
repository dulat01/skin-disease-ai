# 🔗 Backend Integration Guide

This project now uses a **microservices backend** for skin disease prediction instead of local model loading.

## 🏗️ Architecture

```
┌─────────────────────┐
│  GUI Applications   │
│ (predict_*.py)      │
└──────────┬──────────┘
           │ HTTP/REST
           ▼
┌─────────────────────┐
│  API Gateway        │ (Port 8000)
│  (jwt, rate limit)  │
└──────────┬──────────┘
           │
    ┌──────┼──────┬──────────┬─────────┐
    │      │      │          │         │
    ▼      ▼      ▼          ▼         ▼
  Auth   Pred   Admin    RabbitMQ   MinIO
  Svc    Svc     Svc     (Queue)   (Storage)
 (8001) (8002)  (8003)   (5672)    (9010)
    │      │      │
    └──────┼──────┘
           │
        DB (PostgreSQL)
       (Port 5433)
        Redis
       (Port 6380)
```

## 🚀 Quick Start

### 1. Start the Backend

```bash
cd backend
make up
```

Check services are healthy:
```bash
make health
```

You should see all services returning `"status": "healthy"`.

### 2. Run the Frontend

Now you can run the prediction GUIs:

```bash
# Option 1: Single image prediction (6 classes)
python predict_single_image.py

# Option 2: Universal prediction (14+ classes)
python predict_universal.py
```

The GUI will automatically connect to the backend at `http://localhost:8000`.

## 🔌 API Connection Details

### Backend Client (`backend_client.py`)

The `BackendClient` class handles all communication with the backend:

```python
from backend_client import BackendClient

# Initialize
client = BackendClient(api_url="http://localhost:8000", user_id="my-user")

# Check health
if client.health_check():
    print("Backend is running")

# Synchronous prediction
result = client.predict("path/to/image.jpg")
print(result['predicted_class'])
print(result['confidence'])  # 0.0-1.0
print(result['is_malignant'])
print(result['top_predictions'])  # List of top 3

# Async prediction (returns task_id)
task = client.predict_async("path/to/image.jpg")
task_id = task['task_id']

# Check async status
status = client.get_task_status(task_id)
print(status['status'])  # 'pending', 'completed', 'failed'

# Get user history
history = client.get_history()
```

### Available Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v1/predictions/` | Synchronous prediction |
| POST | `/api/v1/predictions/async` | Asynchronous prediction |
| GET | `/api/v1/predictions/task/{task_id}` | Check async task status |
| GET | `/api/v1/predictions/history` | Get user prediction history |
| GET | `/api/v1/predictions/{prediction_id}` | Get specific prediction |
| GET | `/health` | Check API gateway health |

## 📊 Prediction Response

```json
{
  "id": "uuid",
  "user_id": "user-id",
  "predicted_class": "Меланома",
  "confidence": 0.87,
  "is_malignant": true,
  "image_path": "s3://bucket/path",
  "processing_time_ms": 245,
  "model_version": "1.0.0",
  "status": "completed",
  "top_predictions": [
    {
      "class_name": "Меланома",
      "confidence": 0.87,
      "is_malignant": true
    },
    {
      "class_name": "Невус",
      "confidence": 0.10,
      "is_malignant": false
    }
  ],
  "created_at": "2024-04-18T10:30:00Z",
  "completed_at": "2024-04-18T10:30:02Z"
}
```

## 🔧 Troubleshooting

### Backend not connecting
- Check if backend is running: `make ps` in backend folder
- Ensure ports aren't blocked: 8000, 5433 (postgres), 6380 (redis)
- Verify health: `make health`

### Prediction fails
- Check backend logs: `make logs-f`
- Ensure image format is JPEG or PNG
- Max file size: 10MB

### Port conflicts
Edit `backend/docker-compose.yml` to use different ports:
```yaml
ports:
  - "5434:5432"  # PostgreSQL
  - "6381:6379"  # Redis
```

## 📝 Development

### Adding custom user ID
```python
client = BackendClient(
    api_url="http://localhost:8000",
    user_id="doctor-smith-123"
)
```

### Testing the API directly
```bash
curl -X POST http://localhost:8000/api/v1/predictions/ \
  -H "X-User-ID: test-user" \
  -F "image=@test.jpg"
```

## 🔐 Authentication

Currently, the backend expects a `X-User-ID` header. For production, JWT authentication should be implemented through the auth service at port 8001.

## 📈 Scaling

- **Increase prediction concurrency**: Modify Celery worker count in `docker-compose.yml`
- **Add more workers**: `docker-compose up -d --scale celery-worker=3`
- **Monitor performance**: Check RabbitMQ management UI at `http://localhost:15672`

## 📚 More Information

See `backend/README.md` for detailed backend documentation and development guide.
