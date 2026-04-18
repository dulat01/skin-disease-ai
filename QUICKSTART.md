# 🚀 Quick Start Guide

Get the full system running in **30 seconds**!

## ✅ Prerequisites

- **Docker** and **Docker Compose** installed ([download here](https://www.docker.com/products/docker-desktop))
- **4GB RAM** available
- **5GB disk space**

## 📦 Step 1: Clone Repository

```bash
git clone https://github.com/dulat01/skin-disease-ai.git
cd skin-disease-ai
```

## 🚀 Step 2: Start Everything

```bash
cd backend
make up
```

This command:
- Builds all Docker containers
- Starts 10 services (frontend, backend, databases)
- Initializes databases
- Loads the pre-trained ML model

**First run**: 3-5 minutes (downloading Docker images)
**Subsequent runs**: Instant

## 🌐 Step 3: Open Web Interface

Open your browser and go to:

```
http://localhost:3000
```

You now have:
- ✅ Web GUI running
- ✅ ML model loaded
- ✅ Database connected
- ✅ All services healthy

## 🖼️ Use the Application

1. **Upload an Image**
   - Drag and drop a skin lesion image
   - Or click to browse
   - Supports JPEG and PNG (max 10MB)

2. **Get Diagnosis**
   - Click "Analyze Image"
   - Wait 1-2 seconds for inference
   - View results with confidence scores

3. **View Results**
   - Top disease diagnosis
   - Confidence percentage (0-100%)
   - Malignancy status (🔴 MALIGNANT / 🟢 BENIGN)
   - Top 3 predictions ranked

## 📸 Test Images Included

30 sample images in `TEST_IMAGES/`:

```
TEST_IMAGES/
├── 1_MEL_Melanoma_DANGER/           (5 melanoma examples)
├── 2_BCC_BasalCellCarcinoma_DANGER/ (5 basal cell carcinoma)
├── 3_SCC_SquamousCellCarcinoma_DANGER/ (5 squamous cell carcinoma)
├── 4_ACK_ActinicKeratosis_DANGER/   (5 actinic keratosis)
├── 5_NEV_Nevus_SAFE/                (5 nevus/mole examples)
└── 6_SEK_SeborrheicKeratosis_SAFE/  (5 seborrheic keratosis)
```

Try uploading these to test the system!

## 📊 System Features

- **Fully Dockerized**: One command starts everything
- **Web-Based**: Access from any browser
- **Real-time Inference**: Results in ~100-200ms
- **Confidence Visualization**: See model certainty
- **Top-3 Predictions**: View alternative diagnoses
- **Service Health**: Built-in status monitoring

## 🔧 Common Commands

```bash
cd backend

# Check if all services are running
make ps

# View live logs
make logs-f

# Check service health
make health

# Stop everything
make down

# Clean everything (including data)
make clean
```

## 🐛 Troubleshooting

**Services won't start?**
```bash
# Check if Docker is running
docker ps

# View detailed logs
docker-compose logs -f
```

**Ports already in use?**
Edit `backend/docker-compose.yml` and change port mappings (first number in `xxxx:yyyy`)

**Image upload fails?**
- Ensure file is JPEG or PNG
- Check file size under 10MB
- Verify all services are healthy: `make health`

## 📚 More Information

For complete documentation, see:
- **[README.md](README.md)** - System overview
- **[README_INTEGRATED.md](README_INTEGRATED.md)** - Full technical guide
- **[BACKEND_SETUP.md](BACKEND_SETUP.md)** - Backend development details

## 🎯 Model Performance

- **Architecture**: ResNet18 with EfficientNet backbone
- **Accuracy**: 77.10% on test set
- **Classes**: 20 skin disease types
- **Inference Time**: ~100ms per image
- **Training Data**: 3 major dermatology datasets

## ⚠️ Medical Disclaimer

This AI is a **diagnostic aid tool** only. It should **NOT** replace professional medical consultation.

**Always consult a qualified dermatologist for proper diagnosis and treatment.**

## ✨ Next Steps

1. ✅ System is running at http://localhost:3000
2. 📸 Try uploading sample images from `TEST_IMAGES/`
3. 🔍 Review confidence scores and predictions
4. 📖 Read [README_INTEGRATED.md](README_INTEGRATED.md) for advanced features
5. 🚀 Deploy to production (see [README.md](README.md) for details)

---

**That's it! Your skin disease AI system is live!** 🎉

Got questions? Check troubleshooting above or see [README_INTEGRATED.md](README_INTEGRATED.md).

**Ready to save lives with AI! 🩺💙**

