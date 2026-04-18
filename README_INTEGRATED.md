# 🔬 Skin Disease AI - Fully Integrated System

This is a **completely integrated microservices + frontend system** where all components communicate within Docker.

## 🏗️ Architecture

```
Your Computer
    │
    ├─ Port 3000 ──────────────> Frontend Container (Flask)
    │                                    │
    │                         (internal Docker network)
    │                                    │
    │                                    ▼
    │                           API Gateway (8000)
    │                                    │
    │              ┌─────────────────────┼─────────────────┐
    │              │                     │                 │
    │              ▼                     ▼                 ▼
    │        Auth Svc (8001)   Prediction Svc (8002)  Admin Svc (8003)
    │              │                     │                 │
    │              └─────────────────────┼─────────────────┘
    │                                    │
    │              ┌─────────────────────┼─────────────────┐
    │              │                     │                 │
    │              ▼                     ▼                 ▼
    │        PostgreSQL (5433)      Redis (6380)      RabbitMQ (5672)
    │
    └─ Port 8000 ──> Backend API (direct access if needed)
```

## 🚀 Quick Start

### Start Everything

```bash
cd backend
make up
```

This runs **ALL services** in Docker:
- ✅ Frontend (Flask web GUI)
- ✅ API Gateway
- ✅ Prediction Service (ML model)
- ✅ Auth Service
- ✅ Admin Service
- ✅ PostgreSQL Database
- ✅ Redis Cache
- ✅ RabbitMQ Queue
- ✅ MinIO Storage

### Access the Application

**🌐 Web GUI**: Open your browser to:
```
http://localhost:3000
```

**📊 Direct API Access** (if needed):
```
http://localhost:8000
```

**🛠️ RabbitMQ Management**:
```
http://localhost:15672
(default: guest/guest)
```

## 🎨 Frontend Features

### Web-based GUI
- **Drag & Drop**: Drop image anywhere on upload box
- **Image Preview**: See your image before analysis
- **Real-time Results**: Get diagnosis in seconds
- **Confidence Bars**: Visual representation of model confidence
- **Top-3 Predictions**: See all likely diagnoses
- **Malignancy Badge**: Clear indication of risk level
- **Backend Status**: Know if services are running

### Image Upload
- Supported formats: JPEG, PNG
- Max size: 10MB
- Automatic validation

### Results Display
- Disease name with emoji indicators
- Confidence percentage (0-100%)
- Malignancy status (🔴 MALIGNANT / 🟢 BENIGN)
- Top 3 predictions ranked by confidence
- Processing details

## 📱 How It Works

1. **User opens** `http://localhost:3000` in browser
2. **Selects or drags** an image
3. **Clicks "Analyze Image"**
4. **Frontend container** receives request
5. **Forwards to API Gateway** (internal Docker network)
6. **Gateway routes to Prediction Service**
7. **Service loads ML model** and runs inference
8. **Results sent back** to frontend
9. **Browser displays** diagnosis and confidence

**All communication inside Docker** — no external network calls needed!

## 📊 Services Details

| Service | Port | Purpose |
|---------|------|---------|
| **Frontend** | 3000 | Web GUI (Flask) |
| **API Gateway** | 8000 | Route requests, JWT auth, rate limiting |
| **Prediction Svc** | 8002 | ML model inference |
| **Auth Service** | 8001 | User authentication |
| **Admin Service** | 8003 | Analytics & management |
| **PostgreSQL** | 5433 | Main database |
| **Redis** | 6380 | Caching & sessions |
| **RabbitMQ** | 5672 | Async task queue |
| **MinIO** | 9010 | Image storage |

## 🔧 Common Commands

### Check Service Status
```bash
cd backend
make ps        # List all containers
make health    # Check service health
```

### View Logs
```bash
make logs      # View all logs
make logs-f    # Follow logs in real-time
make logs-f | grep frontend  # Frontend logs only
```

### Stop Everything
```bash
make down
```

### Clean Up
```bash
make clean     # Remove all containers & volumes
```

### Access Service Shells
```bash
make shell-pred     # Prediction service shell
make shell-auth     # Auth service shell
make shell-admin    # Admin service shell
make shell-db       # PostgreSQL shell
```

## 🐛 Troubleshooting

### Frontend not loading
```bash
# Check if frontend container is running
make ps | grep frontend

# View frontend logs
docker-compose logs frontend

# Restart frontend only
docker-compose restart frontend
```

### Prediction failing
```bash
# Check prediction service
docker-compose logs prediction-service

# Check database connection
docker-compose logs postgres

# Verify model file exists
docker-compose exec prediction-service ls -la /app/models/
```

### Port conflicts
If ports 3000, 5433, or 6380 are in use:
1. Edit `backend/docker-compose.yml`
2. Change port mappings (e.g., `5434:5432`)
3. Restart: `make clean && make up`

### High memory usage
```bash
# Reduce workers
docker-compose exec frontend sed -i 's/workers=4/workers=2/' app.py

# Scale down Celery workers
docker-compose up -d --scale celery-worker=1
```

## 📚 Development

### Running Frontend Locally (for development)
```bash
cd frontend
python3 -m flask run --host=0.0.0.0 --port=3000
```

### Backend API Testing
```bash
# Test health
curl http://localhost:8000/health

# Upload image (requires X-User-ID header)
curl -X POST http://localhost:8000/api/v1/predictions/ \
  -H "X-User-ID: test-user" \
  -F "image=@test.jpg"
```

## 📈 Scaling

### Add more prediction workers
```bash
docker-compose up -d --scale celery-worker=4
```

### Increase API gateway workers
Edit `backend/services/api-gateway/Dockerfile`:
```dockerfile
CMD ["uvicorn", "app.main:app", "--workers", "8", ...]
```

### Monitor performance
```bash
docker stats
```

## 🔐 Security Notes

- Default credentials (change in production):
  - PostgreSQL: `postgres:postgres`
  - Redis: `redis123`
  - RabbitMQ: `rabbitmq:rabbitmq123`
  - MinIO: `minioadmin:minioadmin123`

- Frontend currently doesn't require auth (add JWT validation in production)
- API Gateway has rate limiting enabled
- All inter-service communication uses Docker network (not exposed)

## 🚢 Deployment

To deploy to production:

1. Update credentials in `.env` file
2. Use production docker-compose file
3. Add HTTPS/TLS
4. Set up proper authentication
5. Configure persistent volumes for database
6. Set up monitoring & alerting

Example `.env`:
```env
POSTGRES_USER=prod_user
POSTGRES_PASSWORD=your_secure_password
REDIS_PASSWORD=your_redis_password
JWT_SECRET=your_jwt_secret_key
```

## 📞 Support

For issues:
1. Check logs: `make logs-f`
2. Verify all containers running: `make ps`
3. Test API directly: `curl http://localhost:8000/health`
4. Check Docker network: `docker network inspect backend_skin-disease-network`

---

**Everything runs in Docker.** One command to start everything!

```bash
cd backend && make up
```

Then open: **http://localhost:3000** 🎉
