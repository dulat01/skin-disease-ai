"""
Image transforms for ML model
"""
from torchvision import transforms

from app.config import settings


def get_transforms():
    """Get image transforms for the model"""
    return transforms.Compose([
        transforms.Resize((settings.IMG_SIZE, settings.IMG_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
    ])
