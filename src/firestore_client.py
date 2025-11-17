"""
Firestore client module.
Handles storing and querying clinical summaries in Firestore.
"""

from typing import List, Dict, Optional, Any
from google.cloud import firestore
from datetime import datetime
import logging

from src.config import Config

logger = logging.getLogger(__name__)


class FirestoreClient:
    """Client for interacting with Firestore."""
    
    def __init__(self, collection_name: Optional[str] = None):
        """
        Initialize Firestore client.
        
        Args:
            collection_name: Name of the Firestore collection. If None, uses Config value.
        """
        self.collection_name = collection_name or Config.FIRESTORE_COLLECTION
        self.db = firestore.Client(project=Config.GCP_PROJECT_ID)
        self.collection = self.db.collection(self.collection_name)
        
        logger.info(f"Initialized Firestore client for collection: {self.collection_name}")
    
    def save_summary(
        self,
        patient_name: str,
        image_name: str,
        summary_data: Dict[str, Any],
        image_metadata: Optional[Dict] = None
    ) -> str:
        """
        Save a clinical summary to Firestore.
        
        Args:
            patient_name: Name of the patient
            image_name: Name/path of the image
            summary_data: Clinical summary data from Gemini
            image_metadata: Optional metadata about the image
            
        Returns:
            str: Document ID of the saved summary
        """
        try:
            # Extract filename from full path
            image_filename = image_name.split("/")[-1]
            
            # Create document data
            doc_data = {
                "patient_name": patient_name,
                "image_name": image_filename,
                "image_path": image_name,
                "summary": summary_data.get("summary", ""),
                "measurements": summary_data.get("measurements", {}),
                "abnormalities": summary_data.get("abnormalities", []),
                "prescriptions": summary_data.get("prescriptions", []),
                "exercises": summary_data.get("exercises", []),
                "dietary": summary_data.get("dietary", []),
                "recommendations": summary_data.get("recommendations", []),
                "created_at": firestore.SERVER_TIMESTAMP,
                "updated_at": firestore.SERVER_TIMESTAMP,
                "model_used": summary_data.get("model_used", ""),
            }
            
            # Add image metadata if provided
            if image_metadata:
                doc_data["image_metadata"] = image_metadata
            
            # Add error info if present
            if "error" in summary_data:
                doc_data["error"] = summary_data["error"]
            
            # Create document with patient_name and image_name as composite key
            doc_id = f"{patient_name}_{image_filename}"
            doc_ref = self.collection.document(doc_id)
            doc_ref.set(doc_data)
            
            logger.info(f"Saved summary for {patient_name}/{image_filename}")
            return doc_id
            
        except Exception as e:
            logger.error(f"Error saving summary to Firestore: {str(e)}")
            raise
    
    def get_patient_summaries(self, patient_name: str) -> List[Dict[str, Any]]:
        """
        Retrieve all summaries for a specific patient.
        
        Args:
            patient_name: Name of the patient
            
        Returns:
            List[Dict]: List of summary documents
        """
        try:
            # NOTE: We deliberately avoid Firestore .order_by here to prevent composite index requirements.
            # We filter by patient_name in Firestore, then sort by created_at in Python.
            query = self.collection.where("patient_name", "==", patient_name)
            docs = query.stream()

            summaries: List[Dict[str, Any]] = []
            for doc in docs:
                doc_data = doc.to_dict()
                doc_data["doc_id"] = doc.id

                # Preserve raw timestamps for sorting
                created_raw = doc_data.get("created_at")
                updated_raw = doc_data.get("updated_at")
                doc_data["_created_at_raw"] = created_raw
                doc_data["_updated_at_raw"] = updated_raw

                # Convert Firestore timestamps to ISO strings for UI
                if created_raw:
                    doc_data["created_at"] = created_raw.isoformat() if hasattr(created_raw, "isoformat") else str(created_raw)
                if updated_raw:
                    doc_data["updated_at"] = updated_raw.isoformat() if hasattr(updated_raw, "isoformat") else str(updated_raw)

                summaries.append(doc_data)

            # Sort in Python by created_at (newest first)
            summaries.sort(
                key=lambda d: d.get("_created_at_raw") or d.get("created_at") or "",
                reverse=True,
            )

            # Remove internal helper fields
            for doc_data in summaries:
                doc_data.pop("_created_at_raw", None)
                doc_data.pop("_updated_at_raw", None)

            logger.info(f"Retrieved {len(summaries)} summaries for patient {patient_name}")
            return summaries

        except Exception as e:
            logger.error(f"Error retrieving summaries for patient {patient_name}: {str(e)}")
            return []
    
    def search_by_nl_query(self, query_text: str) -> List[Dict[str, Any]]:
        """
        Search for patients based on natural language query.
        This performs a text search across all summaries.
        
        Args:
            query_text: Natural language query (e.g., "Who has BP < 80 mmHg?")
            
        Returns:
            List[Dict]: List of matching summary documents with patient names
        """
        try:
            # Get all documents (for small datasets)
            # For production, consider using Algolia, Elasticsearch, or Firestore vector search
            all_docs = self.collection.stream()
            
            matching_summaries = []
            query_lower = query_text.lower()
            
            for doc in all_docs:
                doc_data = doc.to_dict()
                
                # Search in summary text
                summary_text = doc_data.get("summary", "").lower()
                measurements = doc_data.get("measurements", {})
                
                # Check if query matches summary text
                if query_lower in summary_text:
                    doc_data["doc_id"] = doc.id
                    matching_summaries.append(doc_data)
                    continue
                
                # Check measurements for numerical queries
                # Simple pattern matching for queries like "BP < 80" or "heart rate > 100"
                if self._matches_measurement_query(query_text, measurements):
                    doc_data["doc_id"] = doc.id
                    matching_summaries.append(doc_data)
                    continue
                
                # Check abnormalities
                abnormalities = doc_data.get("abnormalities", [])
                for abnormality in abnormalities:
                    if query_lower in str(abnormality).lower():
                        doc_data["doc_id"] = doc.id
                        matching_summaries.append(doc_data)
                        break
            
            # Remove duplicates by patient_name
            unique_patients = {}
            for summary in matching_summaries:
                patient_name = summary.get("patient_name")
                if patient_name not in unique_patients:
                    unique_patients[patient_name] = summary
            
            logger.info(f"Found {len(unique_patients)} matching patients for query: {query_text}")
            return list(unique_patients.values())
            
        except Exception as e:
            logger.error(f"Error searching with NL query: {str(e)}")
            return []
    
    def _matches_measurement_query(self, query: str, measurements: Dict[str, str]) -> bool:
        """
        Check if a natural language query matches measurement values.
        
        Args:
            query: Natural language query
            measurements: Dictionary of measurements
            
        Returns:
            bool: True if query matches any measurement
        """
        query_lower = query.lower()
        
        # Extract parameter and value from query (e.g., "BP < 80" -> param="bp", value=80, op="<")
        import re
        
        # Pattern for queries like "BP < 80 mmHg" or "heart rate > 100"
        patterns = [
            r"(\w+)\s*([<>=]+)\s*(\d+)",
            r"(\w+)\s*(\d+)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                param = match.group(1)
                if len(match.groups()) >= 3:
                    op = match.group(2)
                    value = float(match.group(3))
                else:
                    op = None
                    value = float(match.group(2))
                
                # Check if parameter exists in measurements
                for meas_key, meas_value in measurements.items():
                    if param in meas_key.lower():
                        # Extract numeric value from measurement string
                        meas_nums = re.findall(r"\d+\.?\d*", str(meas_value))
                        if meas_nums:
                            meas_num = float(meas_nums[0])
                            if op:
                                if op == "<" and meas_num < value:
                                    return True
                                elif op == ">" and meas_num > value:
                                    return True
                                elif op == "=" or op == "==" and abs(meas_num - value) < 0.1:
                                    return True
                            else:
                                # Just checking if value exists
                                if abs(meas_num - value) < 0.1:
                                    return True
        
        return False
    
    def get_all_patients(self) -> List[str]:
        """
        Get list of all unique patient names in Firestore.
        
        Returns:
            List[str]: List of patient names
        """
        try:
            docs = self.collection.stream()
            patients = set()
            for doc in docs:
                doc_data = doc.to_dict()
                patient_name = doc_data.get("patient_name")
                if patient_name:
                    patients.add(patient_name)
            
            return sorted(list(patients))
        except Exception as e:
            logger.error(f"Error getting all patients: {str(e)}")
            return []

