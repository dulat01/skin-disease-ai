# Skin Disease AI - Microservices Backend

Production-ready microservices architecture for skin disease classification using deep learning (ResNet18).

## Features

- **6 Skin Condition Classifications** (in Russian):
  - Меланома (Melanoma) - MALIGNANT
  - Базальноклеточная карцинома (Basal Cell Carcinoma) - MALIGNANT
  - Плоскоклеточная карцинома (Squamous Cell Carcinoma) - MALIGNANT
  - Актинический кератоз (Actinic Keratosis) - MALIGNANT
  - Невус/родинка (Nevus/Mole) - BENIGN
  - Себорейный кератоз (Seborrheic Keratosis) - BENIGN

- **JWT Authentication** with access/refresh tokens
- **Sync & Async Predictions** (Celery workers for background processing)
- **Rate Limiting** and request throttling
- **Admin Dashboard** with statistics
- **Image Storage** with MinIO
- **Event-driven Architecture** with RabbitMQ

## Architecture

```
                    ┌─────────────────┐
                    │   API Gateway   │ :8000
                    └────────┬────────┘
          ┌──────────────────┼──────────────────┐
          │                  │                  │
   ┌──────▼──────┐   ┌───────▼───────┐   ┌─────▼──────┐
   │Auth Service │   │Prediction Svc │   │Admin Service│
   │   :8001     │   │    :8002      │   │   :8003    │
   └─────────────┘   └───────┬───────┘   └────────────┘
                             │
                    ┌────────▼────────┐
                    │ Celery Workers  │
                    └─────────────────┘
```

## Quick Start

### Prerequisites

- **Docker** and **Docker Compose** (v2.0+)
- **GNU Make** (or use `docker-compose` commands directly)
- **4GB RAM** minimum (8GB recommended)
- Available ports: 3000, 5433, 6380, 5672, 8000-8003, 9010-9011, 15672

### 1. Start All Services (One Command!)

```bash
cd backend
make up
```

This starts:
- ✅ Frontend Web GUI (port 3000)
- ✅ API Gateway (port 8000)
- ✅ Auth Service (port 8001)
- ✅ Prediction Service (port 8002)
- ✅ Admin Service (port 8003)
- ✅ PostgreSQL, Redis, RabbitMQ, MinIO

**First run**: 3-5 minutes (building images)
**Subsequent runs**: Instant

### 2. Access the Web Interface

Open your browser:

```
http://localhost:3000
```

You can now:
- Upload skin disease images
- View instant predictions with confidence scores
- See malignancy status (benign/malignant)
- View top-3 disease predictions

### 3. Check Service Status

```bash
# List all running containers
make ps

# Check service health
make health

# View logs in real-time
make logs-f
```

All services should show "healthy" status.

### 4. API Testing (Advanced)

**Get API documentation:**

| Service | Swagger UI |
|---------|------------|
| API Gateway | http://localhost:8000/docs |
| Auth Service | http://localhost:8001/docs |
| Prediction Service | http://localhost:8002/docs |
| Admin Service | http://localhost:8003/docs |

**Direct API test:**
```bash
# Test prediction service health
curl http://localhost:8002/health
```

## Services Overview

| Service | Port | Description |
|---------|------|-------------|
| API Gateway | 8000 | Entry point, rate limiting, JWT validation, routing |
| Auth Service | 8001 | User registration, login, JWT tokens |
| Prediction Service | 8002 | ML inference, image processing, history |
| Admin Service | 8003 | Dashboard, statistics, user management |
| PostgreSQL | 5432 | Database (3 databases: auth_db, prediction_db, admin_db) |
| Redis | 6379 | Cache, rate limiting, Celery broker |
| RabbitMQ | 5672/15672 | Message queue, event bus |
| MinIO | 9010/9011 | Object storage for images |

## API Reference

### Authentication (`/api/v1/auth`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register` | Register new user (returns JWT) |
| POST | `/login` | Login (returns JWT) |
| POST | `/logout` | Logout (revoke tokens) |
| POST | `/refresh` | Refresh access token |
| GET | `/me` | Get current user profile |
| PUT | `/me` | Update profile |

### Predictions (`/api/v1/predictions`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/` | Upload image, get instant prediction |
| POST | `/async` | Upload image, get task ID for polling |
| GET | `/task/{task_id}` | Check async task status |
| GET | `/history` | Get user's prediction history |
| GET | `/{id}` | Get prediction by ID |
| POST | `/{id}/feedback` | Submit feedback on prediction |

### Admin (`/api/v1/admin`) - Requires admin role

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/dashboard` | Overview statistics |
| GET | `/statistics/daily` | Daily stats breakdown |
| GET | `/users` | List all users |
| GET | `/model/metrics` | Model performance metrics |

## Common Commands

### Using Make (Recommended)

```bash
make up              # Start all services
make down            # Stop all services
make ps              # List all containers
make logs            # View all logs (one page)
make logs-f          # Follow all logs in real-time
make health          # Check service health status
make clean           # Remove all containers & volumes
make shell-pred      # Shell into prediction service
make shell-auth      # Shell into auth service
make shell-admin     # Shell into admin service
make shell-db        # PostgreSQL shell (psql)
```

### Using Docker Compose Directly

```bash
# Start all services
docker compose up -d

# Stop all services
docker compose down

# View specific service logs
docker compose logs -f prediction-service

# Restart a service
docker compose restart auth-service

# Rebuild after code changes
docker compose build prediction-service
docker compose up -d prediction-service
```

### Database Access

```bash
# Access PostgreSQL
make shell-db

# Or directly:
docker compose exec postgres psql -U postgres -d auth_db

# Access Redis
docker compose exec redis redis-cli -a redis123

# Access MinIO console
# Open http://localhost:9011 in browser
# Login: minioadmin / minioadmin123
```

## Test Images

Test images are available in `../TEST_IMAGES/` organized by condition:

```
TEST_IMAGES/
├── 1_MEL_Melanoma_DANGER/
├── 2_BCC_BasalCellCarcinoma_DANGER/
├── 3_SCC_SquamousCellCarcinoma_DANGER/
├── 4_ACK_ActinicKeratosis_DANGER/
├── 5_NEV_Nevus_SAFE/
└── 6_SEK_SeborrheicKeratosis_SAFE/
```

## Project Structure

```
backend/
├── docker-compose.yml          # All services orchestration
├── .env.example                 # Environment template
├── services/
│   ├── api-gateway/            # Request routing, auth validation
│   ├── auth-service/           # User management, JWT
│   ├── prediction-service/     # ML model, predictions
│   └── admin-service/          # Admin dashboard
├── shared/                     # Common code between services
├── scripts/
│   ├── quick_test.sh          # Quick functionality test
│   ├── test_api.sh            # Comprehensive API tests
│   └── init-db.sh             # Database initialization
└── k8s/                        # Kubernetes manifests
```

## Environment Variables

Key variables (see `.env.example` for all):

```bash
# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# JWT (change in production!)
JWT_SECRET=your-super-secret-jwt-key-change-in-production

# Redis
REDIS_PASSWORD=redis123

# RabbitMQ
RABBITMQ_USER=rabbitmq
RABBITMQ_PASSWORD=rabbitmq123

# MinIO
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin123
```

## Troubleshooting

### Services not starting
```bash
# Check container status
docker compose ps

# Check logs for errors
docker compose logs auth-service
```

### Database connection errors
```bash
# Ensure PostgreSQL is healthy
docker compose exec postgres pg_isready

# Check if databases exist
docker compose exec postgres psql -U postgres -l
```

### Prediction service slow on first request
The ML model (43MB ResNet18) is loaded on first prediction. Subsequent requests are fast (~50-100ms).

### Port conflicts
If ports are in use, modify `docker-compose.yml` port mappings or stop conflicting services.

## Technology Stack

| Component | Technology |
|-----------|------------|
| Framework | FastAPI 0.109 |
| Database | PostgreSQL 15 |
| Cache/Broker | Redis 7 |
| Message Queue | RabbitMQ 3.12 |
| Task Queue | Celery 5.3 |
| ML Model | PyTorch 2.0 (ResNet18) |
| Object Storage | MinIO |
| Containers | Docker / Docker Compose |

## Production Deployment

For Kubernetes deployment:

```bash
kubectl apply -k k8s/
kubectl get pods -n skin-disease
```

See `k8s/` directory for all manifests including:
- Deployments for all services
- StatefulSets for databases
- Horizontal Pod Autoscalers
- Ingress with TLS
- Secrets and ConfigMaps

## License

MIT License
