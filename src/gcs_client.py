"""
Google Cloud Storage client module.
Handles reading and listing images from GCS buckets.
"""

from typing import List, Tuple, Optional, Union
from google.cloud import storage
from google.cloud.exceptions import NotFound
import io
from PIL import Image
import logging

from src.config import Config

logger = logging.getLogger(__name__)


class GCSClient:
    """Client for interacting with Google Cloud Storage."""
    
    def __init__(self, bucket_name: Optional[str] = None):
        """
        Initialize GCS client.
        
        Args:
            bucket_name: Name of the GCS bucket. If None, uses Config value.
        """
        self.bucket_name = bucket_name or Config.GCS_BUCKET_NAME
        logger.info(f"Initializing GCS client for bucket: {self.bucket_name}, project: {Config.GCP_PROJECT_ID}")
        self.storage_client = storage.Client(project=Config.GCP_PROJECT_ID)
        self.bucket = self.storage_client.bucket(self.bucket_name)
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Test connection to the GCS bucket.
        
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            # Try to access the bucket
            self.bucket.reload()
            return True, f"Successfully connected to bucket: {self.bucket_name}"
        except NotFound:
            return False, f"Bucket '{self.bucket_name}' not found. Please check the bucket name."
        except Exception as e:
            return False, f"Error connecting to bucket: {str(e)}"
    
    def list_patients(self) -> List[str]:
        """
        List all patient folders in the bucket.
        Each folder represents a patient.
        
        Returns:
            List[str]: List of patient folder names
        """
        try:
            # First, try the delimiter method (faster if it works)
            blobs = self.bucket.list_blobs(delimiter="/")
            patients = set()
            
            # Get prefixes from delimiter method
            for prefix in blobs.prefixes:
                patient_name = prefix.rstrip("/")
                if patient_name:  # Only add non-empty names
                    patients.add(patient_name)
            
            # Also list all blobs and extract folder names (more robust)
            # This handles cases where delimiter method doesn't work
            all_blobs = self.bucket.list_blobs()
            for blob in all_blobs:
                # Extract the first folder name from the blob path
                # e.g., "patient1/image1.png" -> "patient1"
                parts = blob.name.split("/")
                if len(parts) > 1 and parts[0]:  # Has at least one folder level
                    patients.add(parts[0])
            
            patients_list = sorted(list(patients))
            logger.info(f"Found {len(patients_list)} patients in bucket {self.bucket_name}")
            if patients_list:
                logger.info(f"Patient folders: {', '.join(patients_list[:5])}{'...' if len(patients_list) > 5 else ''}")
            return patients_list
            
        except NotFound:
            logger.error(f"Bucket {self.bucket_name} not found. Please check the bucket name and permissions.")
            return []
        except Exception as e:
            logger.error(f"Error listing patients from bucket {self.bucket_name}: {str(e)}")
            logger.exception("Full error traceback:")
            return []
    
    def list_patient_images(self, patient_name: str) -> List[str]:
        """
        List all image files for a specific patient.
        
        Args:
            patient_name: Name of the patient folder
            
        Returns:
            List[str]: List of image blob names (paths) for the patient
        """
        try:
            prefix = f"{patient_name}/"
            blobs = self.bucket.list_blobs(prefix=prefix)
            
            images = []
            for blob in blobs:
                # Check if file is an image
                if any(blob.name.lower().endswith(ext) for ext in Config.SUPPORTED_IMAGE_FORMATS):
                    images.append(blob.name)
            
            logger.info(f"Found {len(images)} images for patient {patient_name}")
            return sorted(images)
        except Exception as e:
            logger.error(f"Error listing images for patient {patient_name}: {str(e)}")
            return []
    
    def download_image(self, blob_name: str) -> Optional[Image.Image]:
        """
        Download an image from GCS and return as PIL Image.
        
        Args:
            blob_name: Full path to the image blob in GCS
            
        Returns:
            Optional[Image.Image]: PIL Image object or None if error
        """
        try:
            blob = self.bucket.blob(blob_name)
            
            # Check if blob exists
            if not blob.exists():
                logger.error(f"Blob {blob_name} does not exist in bucket")
                return None
            
            # Check file size
            blob.reload()
            size_mb = blob.size / (1024 * 1024)
            if size_mb > Config.MAX_IMAGE_SIZE_MB:
                error_msg = f"Image {blob_name} exceeds size limit ({size_mb:.2f}MB > {Config.MAX_IMAGE_SIZE_MB}MB)"
                logger.warning(error_msg)
                return None
            
            # Download image data
            image_data = blob.download_as_bytes()
            
            if not image_data:
                logger.error(f"Downloaded empty data for {blob_name}")
                return None
            
            # Try to open as image
            try:
                image = Image.open(io.BytesIO(image_data))
                # Convert to RGB if necessary (some formats like PNG with transparency)
                if image.mode in ('RGBA', 'LA', 'P'):
                    # Create a white background
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    if image.mode == 'P':
                        image = image.convert('RGBA')
                    background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
                    image = background
                elif image.mode != 'RGB':
                    image = image.convert('RGB')
                
                logger.debug(f"Downloaded and processed image: {blob_name} ({image.size[0]}x{image.size[1]})")
                return image
            except Exception as img_error:
                logger.error(f"Error opening image {blob_name}: {str(img_error)}")
                return None
            
        except NotFound:
            logger.error(f"Blob {blob_name} not found in bucket {self.bucket_name}")
            return None
        except Exception as e:
            logger.error(f"Error downloading image {blob_name}: {str(e)}", exc_info=True)
            return None
    
    def get_image_metadata(self, blob_name: str) -> dict:
        """
        Get metadata for an image blob.
        
        Args:
            blob_name: Full path to the image blob in GCS
            
        Returns:
            dict: Metadata including size, content_type, time_created, etc.
        """
        try:
            blob = self.bucket.blob(blob_name)
            blob.reload()
            
            return {
                "name": blob.name,
                "size": blob.size,
                "content_type": blob.content_type,
                "time_created": blob.time_created.isoformat() if blob.time_created else None,
                "updated": blob.updated.isoformat() if blob.updated else None,
            }
        except Exception as e:
            logger.error(f"Error getting metadata for {blob_name}: {str(e)}")
            return {}

    def upload_patient_image(
        self,
        patient_name: str,
        file_name: str,
        file_bytes: bytes,
        content_type: Optional[str] = None,
    ) -> str:
        """
        Upload a new image for a patient into GCS.

        Args:
            patient_name: Name of the patient folder (used as prefix in the bucket)
            file_name: Original file name
            file_bytes: Raw file content
            content_type: Optional MIME type (e.g. "image/png")

        Returns:
            str: The full blob path created in the bucket (e.g. "patient1/report1.png")
        """
        # Normalize patient folder and file path
        patient_name = patient_name.strip()
        if not patient_name:
            raise ValueError("patient_name cannot be empty when uploading an image")

        blob_path = f"{patient_name}/{file_name}"
        try:
            blob = self.bucket.blob(blob_path)
            blob.upload_from_string(file_bytes, content_type=content_type)
            logger.info(f"Uploaded image for patient '{patient_name}' to {blob_path}")
            return blob_path
        except Exception as e:
            logger.error(f"Error uploading image {file_name} for patient {patient_name}: {str(e)}")
            raise

