"""
ML Model Loader
"""
import json
import logging
from typing import Optional, List, Tuple
from pathlib import Path

import torch
import torch.nn as nn
from torchvision import models

from app.config import settings

logger = logging.getLogger(__name__)


class ModelLoader:
    """Singleton class for loading and managing the ML model"""

    _instance: Optional["ModelLoader"] = None
    _model: Optional[nn.Module] = None
    _class_names: Optional[List[str]] = None
    _device: Optional[torch.device] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._model is None:
            self._load_model()

    def _load_model(self):
        """Load the PyTorch model and class mapping"""
        logger.info("Loading ML model...")

        # Determine device
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {self._device}")

        # Load class mapping
        class_mapping_path = Path(settings.CLASS_MAPPING_PATH)
        if class_mapping_path.exists():
            with open(class_mapping_path, 'r', encoding='utf-8') as f:
                class_names_dict = json.load(f)
                self._class_names = [class_names_dict[str(i)] for i in range(len(class_names_dict))]
            logger.info(f"Loaded {len(self._class_names)} classes: {self._class_names}")
        else:
            # Fallback class names
            self._class_names = [
                "Актинический кератоз",
                "Базальноклеточная карцинома",
                "Меланома",
                "Невус (родинка)",
                "Плоскоклеточная карцинома",
                "Себорейный кератоз"
            ]
            logger.warning(f"Class mapping not found at {class_mapping_path}, using default classes")

        # Create model architecture (ResNet18)
        self._model = models.resnet18(weights=None)
        num_ftrs = self._model.fc.in_features
        self._model.fc = nn.Linear(num_ftrs, len(self._class_names))

        # Load weights
        model_path = Path(settings.MODEL_PATH)
        if model_path.exists():
            state_dict = torch.load(model_path, map_location=self._device)
            self._model.load_state_dict(state_dict)
            logger.info(f"Model weights loaded from {model_path}")
        else:
            logger.warning(f"Model weights not found at {model_path}")

        # Set to evaluation mode
        self._model.to(self._device)
        self._model.eval()

        logger.info("Model loaded successfully!")

    @property
    def model(self) -> nn.Module:
        """Get the loaded model"""
        return self._model

    @property
    def class_names(self) -> List[str]:
        """Get class names"""
        return self._class_names

    @property
    def device(self) -> torch.device:
        """Get the device"""
        return self._device

    @property
    def num_classes(self) -> int:
        """Get number of classes"""
        return len(self._class_names)

    def predict(self, image_tensor: torch.Tensor) -> Tuple[int, List[float]]:
        """
        Run prediction on an image tensor.

        Args:
            image_tensor: Preprocessed image tensor [1, 3, H, W]

        Returns:
            Tuple of (predicted_class_index, probabilities_list)
        """
        with torch.no_grad():
            image_tensor = image_tensor.to(self._device)
            outputs = self._model(image_tensor)
            probabilities = torch.nn.functional.softmax(outputs[0], dim=0)
            predicted_idx = probabilities.argmax().item()

            return predicted_idx, probabilities.cpu().numpy().tolist()

    def get_top_predictions(
        self,
        probabilities: List[float],
        top_k: int = 3
    ) -> List[dict]:
        """
        Get top-k predictions with class names and malignancy info.

        Args:
            probabilities: List of probabilities for each class
            top_k: Number of top predictions to return

        Returns:
            List of dicts with class_name, confidence, is_malignant
        """
        # Get indices of top probabilities
        indices = sorted(range(len(probabilities)), key=lambda i: probabilities[i], reverse=True)[:top_k]

        results = []
        for idx in indices:
            class_name = self._class_names[idx]
            results.append({
                "class_name": class_name,
                "confidence": probabilities[idx],
                "is_malignant": settings.MALIGNANCY_MAP.get(class_name, False)
            })

        return results


# Global model loader instance
_model_loader: Optional[ModelLoader] = None


def get_model_loader() -> ModelLoader:
    """Get the global model loader instance"""
    global _model_loader
    if _model_loader is None:
        _model_loader = ModelLoader()
    return _model_loader
