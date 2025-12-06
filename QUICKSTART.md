# 🚀 Quick Start Guide

Get up and running in 3 simple steps!

## ✅ What's Included

When you clone this repository, you get:
- ✅ **Trained Model** (39.6 MB) - Ready to use!
- ✅ **30 Test Images** - Real dermatoscopy examples
- ✅ **Beautiful GUI** - Easy-to-use interface
- ✅ **All Scripts** - No manual setup needed

## 📦 Step 1: Clone & Install

```bash
git clone https://github.com/dulat01/skin-disease-ai.git
cd skin-disease-ai
install.bat
```

**Installation time**: 5-10 minutes (downloads PyTorch ~200MB)

## 🧪 Step 2: Test Immediately

```bash
test_single.bat
```

This launches a beautiful GUI where you can:
- 📂 Load any skin lesion image
- 🎯 See diagnosis with confidence %
- 🔴/🟢 View malignancy status
- 📊 View TOP-3 predictions

## 📸 Step 3: Try Test Images

The repository includes 30 professional dermatoscopy images in `TEST_IMAGES/`:

### Malignant (DANGER) 🔴
- `1_MEL_Melanoma_DANGER/` - 5 melanoma cases
- `2_BCC_BasalCellCarcinoma_DANGER/` - 5 basal cell carcinoma cases
- `3_SCC_SquamousCellCarcinoma_DANGER/` - 5 squamous cell carcinoma cases
- `4_ACK_ActinicKeratosis_DANGER/` - 5 actinic keratosis cases

### Benign (SAFE) 🟢
- `5_NEV_Nevus_SAFE/` - 5 nevus (mole) cases
- `6_SEK_SeborrheicKeratosis_SAFE/` - 5 seborrheic keratosis cases

**Try loading these images and see the predictions!**

---

## 🎯 Model Performance

- **Architecture**: ResNet18 (CAS_ISIC Adapted)
- **Training Accuracy**: 77.10%
- **Classes**: 6 skin disease types
- **Dataset**: PAD-UFES-20 (Brazilian dermatoscopy images)

---

## ⚠️ Important Note

This AI is a **diagnostic aid tool** only. Always consult a qualified dermatologist for proper diagnosis and treatment.

---

## 🆘 Troubleshooting

### Python Not Found
Make sure Python 3.10+ is installed:
```bash
python --version
```

### Model Not Loading
Check if `models/final_model_CAS.pth` exists (39.6 MB)

### GUI Not Opening
Try running directly:
```bash
venv310\Scripts\activate
python predict_single_image.py
```

---

## 📚 Full Documentation

See [README.md](README.md) for:
- Training your own model
- Technical details
- Dataset information
- Contributing guidelines

---

**Ready to save lives with AI! 🩺💙**

