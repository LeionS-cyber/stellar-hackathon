"""
Image processing and perceptual hashing service.
"""

import os
import uuid
from PIL import Image
import imagehash
from fastapi import UploadFile
from app.core.config import settings
from app.core.exceptions import ValidationException


class ImageService:
    """Service for image processing and pHash generation"""

    @staticmethod
    def validate_image_file(filename: str) -> bool:
        """Validate file extension"""
        if not filename:
            return False
        ext = filename.rsplit(".", 1)[-1].lower()
        return ext in settings.ALLOWED_IMAGE_EXTENSIONS

    @staticmethod
    async def save_upload_file(upload_file: UploadFile) -> tuple[str, int]:
        """
        Save uploaded file and return file path and size.
        
        Returns:
            Tuple of (file_path, file_size)
        """
        if not ImageService.validate_image_file(upload_file.filename):
            raise ValidationException("Invalid image format. Allowed: jpg, png, gif, webp")

        # Check file size
        content = await upload_file.read()
        if len(content) > settings.MAX_FILE_SIZE:
            raise ValidationException(f"File size exceeds {settings.MAX_FILE_SIZE / 1024 / 1024}MB limit")

        # Generate unique filename
        file_ext = os.path.splitext(upload_file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)

        # Save file
        with open(file_path, "wb") as f:
            f.write(content)

        return file_path, len(content)

    @staticmethod
    def generate_phash(file_path: str) -> str:
        """
        Generate perceptual hash from image file.
        
        Args:
            file_path: Path to image file
            
        Returns:
            Hex string representation of pHash
        """
        try:
            img = Image.open(file_path)
            # Resize if needed
            img.thumbnail(
                (settings.IMAGE_RESIZE_MAX_WIDTH, settings.IMAGE_RESIZE_MAX_HEIGHT),
                Image.Resampling.LANCZOS,
            )
            hash_value = imagehash.phash(img)
            return str(hash_value)
        except Exception as e:
            raise ValidationException(f"Failed to process image: {str(e)}")

    @staticmethod
    def get_image_metadata(file_path: str) -> dict:
        """
        Extract metadata from image file.
        
        Returns:
            Dictionary with width, height, and mime type
        """
        try:
            img = Image.open(file_path)
            return {
                "width": img.width,
                "height": img.height,
                "mime_type": Image.MIME.get(img.format, "image/unknown"),
            }
        except Exception as e:
            raise ValidationException(f"Failed to extract image metadata: {str(e)}")

    @staticmethod
    def calculate_hamming_distance(hash1_str: str, hash2_str: str) -> int:
        """
        Calculate Hamming distance between two pHashes.
        
        Lower distance = more similar images
        """
        try:
            h1 = imagehash.hex_to_hash(hash1_str)
            h2 = imagehash.hex_to_hash(hash2_str)
            return h1 - h2
        except Exception:
            return float("inf")

    @staticmethod
    def cleanup_file(file_path: str):
        """Delete a file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass