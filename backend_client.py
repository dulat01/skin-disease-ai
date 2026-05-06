"""
Backend API Client for Skin Disease AI
Communicates with the microservices backend instead of using local models
"""

import requests
import json
from typing import Dict, Any, Optional
from pathlib import Path

class BackendClient:
    def __init__(self, api_url: str = "http://localhost:8000", user_id: str = "local-user"):
        """
        Initialize backend client

        Args:
            api_url: Base URL of API gateway
            user_id: User identifier for predictions
        """
        self.api_url = api_url.rstrip('/')
        self.user_id = user_id
        self.session = requests.Session()
        self.session.headers.update({
            'X-User-ID': user_id,
            'Accept': 'application/json'
        })

    def predict(self, image_path: str) -> Dict[str, Any]:
        """
        Send image to backend for prediction

        Args:
            image_path: Path to image file

        Returns:
            Dictionary with prediction results

        Raises:
            ConnectionError: If backend is unreachable
            ValueError: If prediction fails
        """
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        try:
            with open(image_path, 'rb') as f:
                files = {'image': (image_path.name, f, 'image/jpeg')}
                response = self.session.post(
                    f"{self.api_url}/api/v1/predictions/",
                    files=files,
                    timeout=30
                )

            if response.status_code == 201:
                result = response.json()
                return result.get('data', result)
            else:
                raise ValueError(f"Prediction failed: {response.text}")

        except requests.exceptions.ConnectionError as e:
            raise ConnectionError(
                f"Cannot connect to backend at {self.api_url}. "
                f"Make sure the backend is running: 'cd backend && make up'"
            ) from e

    def predict_async(self, image_path: str) -> Dict[str, Any]:
        """
        Send image for asynchronous prediction
        Returns task ID to check status later
        """
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        try:
            with open(image_path, 'rb') as f:
                files = {'image': (image_path.name, f, 'image/jpeg')}
                response = self.session.post(
                    f"{self.api_url}/api/v1/predictions/async",
                    files=files,
                    timeout=10
                )

            if response.status_code == 202:
                return response.json()
            else:
                raise ValueError(f"Async prediction failed: {response.text}")

        except requests.exceptions.ConnectionError as e:
            raise ConnectionError(
                f"Cannot connect to backend at {self.api_url}"
            ) from e

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get status of async prediction task"""
        try:
            response = self.session.get(
                f"{self.api_url}/api/v1/predictions/task/{task_id}",
                timeout=5
            )
            if response.status_code == 200:
                return response.json()
            else:
                raise ValueError(f"Failed to get task status: {response.text}")
        except requests.exceptions.ConnectionError as e:
            raise ConnectionError(f"Cannot connect to backend at {self.api_url}") from e

    def get_history(self) -> Dict[str, Any]:
        """Get prediction history for user"""
        try:
            response = self.session.get(
                f"{self.api_url}/api/v1/predictions/history",
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            else:
                raise ValueError(f"Failed to get history: {response.text}")
        except requests.exceptions.ConnectionError as e:
            raise ConnectionError(f"Cannot connect to backend at {self.api_url}") from e

    def health_check(self) -> bool:
        """Check if backend is running"""
        try:
            response = self.session.get(
                f"{self.api_url}/health",
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
