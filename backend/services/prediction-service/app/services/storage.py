"""
MinIO Storage Service
"""
import logging
import io
from typing import Optional, BinaryIO
from datetime import datetime
import uuid

from minio import Minio
from minio.error import S3Error

from app.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """MinIO storage service for image files"""

    _instance: Optional["StorageService"] = None
    _client: Optional[Minio] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._client is None:
            self._initialize_client()

    def _initialize_client(self):
        """Initialize MinIO client and create bucket if needed"""
        self._client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )

        # Create bucket if it doesn't exist
        try:
            if not self._client.bucket_exists(settings.MINIO_BUCKET):
                self._client.make_bucket(settings.MINIO_BUCKET)
                logger.info(f"Created bucket: {settings.MINIO_BUCKET}")
        except S3Error as e:
            logger.error(f"Error creating bucket: {e}")

    def generate_object_name(self, user_id: str, original_filename: str) -> str:
        """Generate unique object name for storage"""
        ext = original_filename.split('.')[-1] if '.' in original_filename else 'jpg'
        date_prefix = datetime.utcnow().strftime('%Y/%m/%d')
        unique_id = str(uuid.uuid4())[:8]
        return f"{date_prefix}/{user_id}/{unique_id}.{ext}"

    def upload_image(
        self,
        file_data: BinaryIO,
        object_name: str,
        content_type: str = "image/jpeg"
    ) -> str:
        """
        Upload an image to MinIO.

        Args:
            file_data: File-like object containing image data
            object_name: The object name/path in the bucket
            content_type: MIME type of the image

        Returns:
            The full path to the uploaded object
        """
        try:
            # Get file size
            file_data.seek(0, 2)  # Seek to end
            file_size = file_data.tell()
            file_data.seek(0)  # Seek back to start

            self._client.put_object(
                settings.MINIO_BUCKET,
                object_name,
                file_data,
                file_size,
                content_type=content_type
            )

            logger.info(f"Uploaded image: {object_name}")
            return f"{settings.MINIO_BUCKET}/{object_name}"

        except S3Error as e:
            logger.error(f"Error uploading image: {e}")
            raise

    def download_image(self, object_name: str) -> bytes:
        """
        Download an image from MinIO.

        Args:
            object_name: The object name/path in the bucket

        Returns:
            Image data as bytes
        """
        try:
            # Remove bucket prefix if present
            if object_name.startswith(f"{settings.MINIO_BUCKET}/"):
                object_name = object_name[len(settings.MINIO_BUCKET) + 1:]

            response = self._client.get_object(settings.MINIO_BUCKET, object_name)
            data = response.read()
            response.close()
            response.release_conn()

            return data

        except S3Error as e:
            logger.error(f"Error downloading image: {e}")
            raise

    def get_presigned_url(self, object_name: str, expires_hours: int = 1) -> str:
        """
        Get a presigned URL for an image.

        Args:
            object_name: The object name/path in the bucket
            expires_hours: URL expiration time in hours

        Returns:
            Presigned URL for the image
        """
        try:
            # Remove bucket prefix if present
            if object_name.startswith(f"{settings.MINIO_BUCKET}/"):
                object_name = object_name[len(settings.MINIO_BUCKET) + 1:]

            from datetime import timedelta
            url = self._client.presigned_get_object(
                settings.MINIO_BUCKET,
                object_name,
                expires=timedelta(hours=expires_hours)
            )
            return url

        except S3Error as e:
            logger.error(f"Error generating presigned URL: {e}")
            raise

    def delete_image(self, object_name: str) -> bool:
        """
        Delete an image from MinIO.

        Args:
            object_name: The object name/path in the bucket

        Returns:
            True if successful
        """
        try:
            # Remove bucket prefix if present
            if object_name.startswith(f"{settings.MINIO_BUCKET}/"):
                object_name = object_name[len(settings.MINIO_BUCKET) + 1:]

            self._client.remove_object(settings.MINIO_BUCKET, object_name)
            logger.info(f"Deleted image: {object_name}")
            return True

        except S3Error as e:
            logger.error(f"Error deleting image: {e}")
            return False


# Singleton instance
_storage_service: Optional[StorageService] = None


def get_storage_service() -> StorageService:
    """Get the global storage service instance"""
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service
