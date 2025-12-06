# 🩺 Skin Disease Classification AI

A universal deep learning model for skin disease classification using PyTorch and EfficientNet-B4. This system can diagnose 20 different types of skin conditions with high accuracy.

## 🎯 Features

- **20 Disease Classes**: Covers a wide spectrum of skin diseases from 3 major datasets
- **State-of-the-art Architecture**: Uses EfficientNet-B4 with transfer learning
- **High Accuracy**: Achieves competitive performance on medical imaging benchmarks
- **Easy to Use**: Simple GUI interface for testing predictions
- **Production Ready**: Two-stage training with data augmentation and class balancing

## 📊 Supported Diseases

The model can classify the following skin conditions:

### DermaMNIST (7 classes)
- Melanocytic nevi
- Melanoma
- Benign keratosis
- Basal cell carcinoma
- Actinic keratoses
- Vascular lesions
- Dermatofibroma

### PAD-UFES-20 (6 classes)
- Melanoma (MEL)
- Basal Cell Carcinoma (BCC)
- Squamous Cell Carcinoma (SCC)
- Actinic Keratosis (ACK)
- Nevus (NEV)
- Seborrheic Keratosis (SEK)

### HAM10000 (7 classes)
- Actinic keratoses
- Basal cell carcinoma
- Benign keratosis-like lesions
- Dermatofibroma
- Melanoma
- Melanocytic nevi
- Vascular lesions

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/dulat01/skin-disease-ai.git
cd skin-disease-ai
```

### 2. Installation

Run the installation script to set up the environment:

```bash
install.bat
```

This will:
- Create a Python virtual environment
- Install PyTorch with CPU support
- Install all required dependencies

**Note**: The repository already includes:
- ✅ Trained model (`models/final_model_CAS.pth` - 39.6 MB)
- ✅ Class mappings (`models/class_mapping_ru.json`)
- ✅ 30 test images in `TEST_IMAGES/` folder

You can start testing immediately after installation!

### 3. Test the Model (No Training Needed!)

#### Option A: Simple Single-Image GUI (Recommended for Quick Testing)

```bash
test_single.bat
```

This launches a beautiful GUI where you can:
- 📂 Load any skin lesion image
- 🎯 See the main diagnosis with confidence percentage
- 🔴/🟢 View malignancy status (benign vs malignant)
- 📊 View TOP-3 predictions with probability bars

#### Option B: Universal Model Testing

```bash
test.bat
```

For testing the universal model with 20 disease classes.

---

## 🎓 Training Your Own Model (Optional)

If you want to retrain the model from scratch:

### 1. Prepare Datasets

Download the following datasets and place them in the `dataset/` folder:

- **DermaMNIST**: `dermamnist_224.npz` (from MedMNIST)
- **PAD-UFES-20**: Extract to `dataset/PAD_UFES_20/`
- **HAM10000**: Extract images and metadata to `dataset/HAM10000/`

### 2. Train the Model

Run the training script (2-5 hours depending on your hardware):

```bash
train.bat
```

The training uses a two-stage approach:
- **Stage 1** (10 epochs): Train only the classification head with frozen base
- **Stage 2** (20 epochs): Fine-tune all layers with lower learning rate

## 🏗️ Project Structure

```
├── install.bat              # Setup environment
├── train.bat                # Train the model
├── test.bat                 # Test universal model (20 classes)
├── test_single.bat          # Test single image GUI (6 classes)
├── train_universal_model.py # Training script
├── predict_universal.py     # Universal model GUI
├── predict_single_image.py  # Single image GUI (simple & beautiful)
├── setup_pytorch_environment.py  # Dependency installer
├── requirements.txt         # Python dependencies
├── dataset/                 # Place your datasets here
├── models/                  # Trained models saved here
├── results/                 # Training results and plots
└── TEST_IMAGES/             # Sample test images (30 examples)
```

## 🧠 Model Architecture

- **Base Model**: EfficientNet-B4 (pre-trained on ImageNet)
- **Input Size**: 224x224 RGB images
- **Output**: 20-class classification with softmax
- **Optimizer**: Adam with learning rate scheduling
- **Loss Function**: Cross-Entropy with class weights
- **Data Augmentation**: Random flips, rotations, color jitter, resizing

## 📈 Training Details

### Data Augmentation
- Random horizontal/vertical flips
- Random rotations (±15°)
- Color jitter (brightness, contrast, saturation)
- Random resized crop (0.8-1.0 scale)

### Class Imbalance Handling
- Weighted Random Sampler for training
- Class weights in loss function
- Balanced validation set

### Two-Stage Training Strategy
1. **Stage 1**: Freeze base layers, train only the head
   - Learning rate: 0.001
   - Batch size: 32
   - Epochs: 10

2. **Stage 2**: Fine-tune all layers
   - Learning rate: 0.0001
   - Batch size: 32
   - Epochs: 20
   - ReduceLROnPlateau scheduler

## 📋 Requirements

- Python 3.10+
- PyTorch 2.0+
- torchvision
- NumPy < 2.0 (compatibility)
- Pillow
- matplotlib
- scikit-learn
- tqdm

## ⚠️ Medical Disclaimer

This AI model is designed as a **diagnostic aid tool** only. It should **NOT** replace professional medical consultation. Always consult with a qualified dermatologist for proper diagnosis and treatment.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.

## 📄 License

This project is for educational and research purposes.

## 🙏 Acknowledgments

- **DermaMNIST**: Part of the MedMNIST dataset collection
- **PAD-UFES-20**: Public dermatoscopic dataset from UFES
- **HAM10000**: Harvard Dataverse skin lesion dataset
- **EfficientNet**: Google Research architecture
- **CAS_ISIC**: Inspiration from the CAS-ISIC project

## 📦 Publishing to GitHub

This repository is ready to be pushed to GitHub:

1. **Create a new private repository** on GitHub: https://github.com/new
   - Name: `skin-disease-ai` (or any name you prefer)
   - Privacy: **Private**
   - Don't add README, .gitignore, or license (already included)

2. **Push your code**:
```bash
git remote add origin https://github.com/YOUR-USERNAME/skin-disease-ai.git
git branch -M main
git push -u origin main
```

3. **Note**: Datasets are not included in the repository (too large). Users must download them separately and place in `dataset/` folder.

## 📞 Support

For questions or issues, please open an issue on GitHub.

---

**Made with ❤️ for advancing medical AI diagnostics**

