# 🩺 Skin Disease Classification AI

A **fully integrated microservices system** with web GUI for skin disease classification using PyTorch deep learning. Diagnose 20 different types of skin conditions with high accuracy using a containerized, production-ready architecture.

## 🎯 Key Features

- **🐳 Fully Dockerized**: One command starts entire system
- **🌐 Web GUI**: Beautiful drag-and-drop interface
- **🧠 20 Disease Classes**: Comprehensive skin disease coverage
- **⚡ Real-time Inference**: ML predictions in milliseconds
- **🔄 Microservices**: Scalable, independent services
- **💾 Persistent Storage**: PostgreSQL, Redis, MinIO
- **📊 Admin Dashboard**: Analytics and management UI

## 🚀 Quick Start (Docker)

### Prerequisites

- **Docker** and **Docker Compose** installed
- ~5GB disk space
- ~4GB RAM available

### Start Everything (One Command!)

```bash
cd backend
make up
```

This starts:
- ✅ Frontend Web GUI (http://localhost:3000)
- ✅ Prediction Service (ML model inference)
- ✅ Auth Service (user management)
- ✅ Admin Service (analytics)
- ✅ PostgreSQL Database
- ✅ Redis Cache
- ✅ RabbitMQ Message Queue
- ✅ MinIO Image Storage

### Access the Application

Open your browser:
```
http://localhost:3000
```

Then:
1. Upload or drag a skin disease image (JPEG/PNG)
2. Click "Analyze Image"
3. View diagnosis with confidence scores and malignancy status

## 📊 Supported Diseases

The model classifies 20 skin conditions from 3 datasets:

**PAD-UFES-20**: Melanoma, Basal Cell Carcinoma, Squamous Cell Carcinoma, Actinic Keratosis, Nevus, Seborrheic Keratosis

**DermaMNIST**: Melanocytic nevi, Melanoma, Benign keratosis, Basal cell carcinoma, Actinic keratoses, Vascular lesions, Dermatofibroma

**HAM10000**: Actinic keratoses, Basal cell carcinoma, Benign keratosis-like lesions, Dermatofibroma, Melanoma, Melanocytic nevi, Vascular lesions

## 🏗️ Architecture

```
Browser (http://localhost:3000)
    │
    └─> Frontend Container (Flask)
            │
            └─> Docker Internal Network
                    │
                    ├─> Prediction Service (ML inference)
                    ├─> Auth Service
                    ├─> Admin Service
                    └─> Infrastructure
                        ├─> PostgreSQL
                        ├─> Redis
                        ├─> RabbitMQ
                        └─> MinIO
```

All services communicate securely within Docker. Only necessary ports exposed to host.

## 🔧 Common Commands

```bash
cd backend

make up         # Start all services
make down       # Stop all services
make ps         # List all containers
make logs       # View all logs
make logs-f     # Follow logs in real-time
make health     # Check service health
make clean      # Remove all containers & volumes
```

## 📚 Detailed Documentation

For more information, see:

- **[README_INTEGRATED.md](README_INTEGRATED.md)** - Comprehensive system guide
  - Full architecture overview
  - All available commands
  - Troubleshooting guide
  - API testing examples
  - Scaling information
  - Security notes

## 🎓 Training & Development

### Local Development (Optional)

For training a custom model or running locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests locally
python predict_single_image.py
python predict_universal.py
```

See [BACKEND_SETUP.md](BACKEND_SETUP.md) for detailed development instructions.

## 📋 System Requirements

- **Docker**: Latest version
- **Docker Compose**: v2.0+
- **RAM**: 4GB minimum (8GB recommended)
- **Disk**: 5GB free space
- **OS**: Linux, macOS, or Windows (with WSL2)

## ⚠️ Medical Disclaimer

This AI model is designed as a **diagnostic aid tool** only. It should **NOT** replace professional medical consultation. Always consult with a qualified dermatologist for proper diagnosis and treatment.

## 🔐 Security & Deployment

**Development Mode** (Default):
- Debug mode enabled
- Default credentials used
- Suitable for testing only

**Production Deployment**:
1. Change all default credentials in `.env`
2. Enable HTTPS/TLS
3. Set strong JWT secrets
4. Use environment-based configuration
5. Set up monitoring and backups

See [README_INTEGRATED.md](README_INTEGRATED.md) for production deployment guide.

## 🐛 Troubleshooting

**Services not starting?**
```bash
# Check if ports are free
lsof -i :3000
lsof -i :5433
lsof -i :6380

# View detailed logs
docker-compose logs -f
```

**Image upload fails?**
- Ensure image is JPEG or PNG format
- Check file size is under 10MB
- Verify backend services are healthy: `make health`

**Port conflicts?**
- Edit `backend/docker-compose.yml`
- Change port mappings
- Restart: `make clean && make up`

See [README_INTEGRATED.md](README_INTEGRATED.md) for more troubleshooting.

## 📦 Project Structure

```
├── frontend/                 # Web GUI (Flask + HTML/CSS/JS)
│   ├── app.py               # Flask backend
│   ├── Dockerfile           # Container definition
│   ├── requirements.txt      # Python dependencies
│   └── templates/
│       └── index.html       # Web interface
│
├── backend/                 # Microservices & infrastructure
│   ├── docker-compose.yml   # Orchestration
│   ├── Makefile             # Helper commands
│   ├── services/
│   │   ├── api-gateway/
│   │   ├── auth-service/
│   │   ├── prediction-service/
│   │   └── admin-service/
│   └── scripts/             # Database initialization
│
├── models/                  # Pre-trained ML models
│   ├── final_model_CAS.pth  # ResNet18 model (39.6 MB)
│   └── class_mapping_ru.json # Disease class labels
│
└── TEST_IMAGES/            # Sample test images (30 examples)
    ├── (various disease categories)
```

## 🤝 Contributing

Contributions welcome! For major changes:
1. Create a feature branch
2. Test thoroughly
3. Submit a pull request

## 🙏 Acknowledgments

- **DermaMNIST**: MedMNIST dataset collection
- **PAD-UFES-20**: UFES public dermatoscopic dataset
- **HAM10000**: Harvard skin lesion dataset
- **PyTorch**: Deep learning framework
- **Flask**: Web framework
- **Docker**: Containerization

## 📄 License

Educational and research purposes.

## 📞 Support

For issues or questions:
1. Check [README_INTEGRATED.md](README_INTEGRATED.md) troubleshooting section
2. Review service logs: `make logs-f`
3. Open an issue on GitHub

---

**Everything runs in Docker. Get started in seconds!**

```bash
cd backend && make up
```

Then open: **http://localhost:3000** 🎉

