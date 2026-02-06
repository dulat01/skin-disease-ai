"""
Image Processing Service
"""
import logging
import io
from typing import Tuple

from PIL import Image
import torch

from app.ml.transforms import get_transforms
from app.config import settings

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Service for processing images for ML model"""

    def __init__(self):
        self.transforms = get_transforms()

    def load_image(self, image_data: bytes) -> Image.Image:
        """
        Load image from bytes.

        Args:
            image_data: Raw image bytes

        Returns:
            PIL Image in RGB format
        """
        image = Image.open(io.BytesIO(image_data))
        return image.convert('RGB')

    def preprocess(self, image: Image.Image) -> torch.Tensor:
        """
        Preprocess image for model inference.

        Args:
            image: PIL Image in RGB format

        Returns:
            Preprocessed tensor ready for model
        """
        tensor = self.transforms(image)
        # Add batch dimension
        return tensor.unsqueeze(0)

    def validate_image(self, image_data: bytes) -> Tuple[bool, str]:
        """
        Validate image data.

        Args:
            image_data: Raw image bytes

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            image = Image.open(io.BytesIO(image_data))

            # Check format
            if image.format not in ['JPEG', 'PNG', 'JPG']:
                return False, f"Unsupported image format: {image.format}"

            # Check size
            max_size = 10 * 1024 * 1024  # 10MB
            if len(image_data) > max_size:
                return False, f"Image too large. Maximum size is 10MB"

            # Check dimensions
            min_dim = 32
            if image.width < min_dim or image.height < min_dim:
                return False, f"Image too small. Minimum dimension is {min_dim}px"

            return True, ""

        except Exception as e:
            return False, f"Invalid image: {str(e)}"

    def get_image_info(self, image_data: bytes) -> dict:
        """
        Get image metadata.

        Args:
            image_data: Raw image bytes

        Returns:
            Dict with image info
        """
        image = Image.open(io.BytesIO(image_data))
        return {
            "format": image.format,
            "mode": image.mode,
            "width": image.width,
            "height": image.height,
            "size_bytes": len(image_data)
        }
