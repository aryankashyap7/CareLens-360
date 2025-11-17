"""
Gemini Pro Vision API client module.
Handles clinical summarization of medical images using Gemini.
"""

from typing import Optional, Dict
import google.generativeai as genai
from PIL import Image
import logging
import json
from datetime import datetime

from src.config import Config

logger = logging.getLogger(__name__)


class GeminiClient:
    """Client for interacting with Gemini Pro Vision API."""
    
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        """
        Initialize Gemini client.
        
        Args:
            api_key: Gemini API key. If None, uses Config value.
            model_name: Model name. If None, uses Config value.
        """
        self.api_key = api_key or Config.GEMINI_API_KEY
        self.model_name = model_name or Config.GEMINI_MODEL
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        # Try to initialize the model, with fallback options
        try:
            self.model = genai.GenerativeModel(self.model_name)
            logger.info(f"Initialized Gemini client with model: {self.model_name}")
        except Exception as e:
            logger.warning(f"Failed to initialize model {self.model_name}: {str(e)}")
            # Try fallback models
            fallback_models = ["gemini-1.5-flash", "gemini-pro-vision", "gemini-1.0-pro-vision"]
            for fallback in fallback_models:
                try:
                    logger.info(f"Trying fallback model: {fallback}")
                    self.model = genai.GenerativeModel(fallback)
                    self.model_name = fallback
                    logger.info(f"Successfully initialized with fallback model: {fallback}")
                    break
                except Exception:
                    continue
            else:
                # If all fallbacks fail, raise the original error
                raise Exception(f"Could not initialize any Gemini model. Original error: {str(e)}")
    
    def generate_clinical_summary(self, image: Image.Image, image_name: str) -> Dict[str, any]:
        """
        Generate a clinical summary for a medical image using Gemini Pro Vision.
        
        Args:
            image: PIL Image object
            image_name: Name/path of the image for reference
            
        Returns:
            Dict containing summary, extracted_data, and metadata
        """
        try:
            # Create a comprehensive prompt for clinical analysis
            prompt = """
            Analyze this medical image (lab report, X-ray, scan, or other clinical document) and provide a comprehensive analysis:
            
            1. **Clinical Summary**: A detailed, complete description of all findings, observations, and clinical significance. Include ALL details from the report - do not truncate or summarize. Provide the full analysis.
            
            2. **Key Measurements**: Extract any numerical values mentioned (e.g., blood pressure, heart rate, lab values, measurements, etc.) in the format:
               - Parameter: Value Unit (e.g., "BP: 120/80 mmHg", "Heart Rate: 72 bpm", "Hemoglobin: 12.5 g/dL")
            
            3. **Abnormalities**: List any abnormalities, anomalies, or areas of concern found in the report.
            
            4. **Prescriptions**: Based on the findings, suggest potential medications or treatments.
               IMPORTANT: DO NOT include any disclaimer text inside each prescription string.
               Just return clean items like: "Medication name - dosage - frequency - reason".
               The application UI will show the clinical disclaimer separately.
               Format as: ["Medication name - dosage - frequency - reason", ...]
            
            5. **Exercise Recommendations**: Suggest appropriate exercises or physical activities if applicable based on the condition. If not applicable, state "No specific exercise recommendations based on this report."
               Format as: ["Exercise type - frequency - duration - notes", ...]
            
            6. **Dietary Recommendations**: Provide nutritional and dietary suggestions based on the findings (e.g., foods to include, foods to avoid, dietary modifications).
               Format as: ["Food/Item to include/avoid - reason - frequency", ...]
            
            7. **General Recommendations**: Any other clinical recommendations, follow-up suggestions, or lifestyle modifications.
            
            Format your response as a JSON object with the following structure:
            {
                "summary": "Complete, detailed clinical summary with ALL information - do not truncate",
                "measurements": {
                    "parameter_name": "value unit",
                    ...
                },
                "abnormalities": ["abnormality 1", "abnormality 2", ...],
                "prescriptions": ["prescription 1", "prescription 2", ...],
                "exercises": ["exercise 1", "exercise 2", ...],
                "dietary": ["dietary recommendation 1", "dietary recommendation 2", ...],
                "recommendations": ["recommendation 1", "recommendation 2", ...]
            }
            
            If the image is not a medical image or cannot be analyzed, return appropriate error information.
            """
            
            # Generate content using Gemini
            try:
                response = self.model.generate_content([prompt, image])
                
                # Check if response was blocked or has errors
                if not response.text:
                    if response.candidates and response.candidates[0].finish_reason:
                        finish_reason = response.candidates[0].finish_reason
                        if finish_reason == 2:  # SAFETY
                            error_msg = "Content was blocked by safety filters"
                            logger.error(f"{error_msg} for {image_name}")
                            raise Exception(error_msg)
                        elif finish_reason == 3:  # RECITATION
                            error_msg = "Content was blocked due to recitation"
                            logger.error(f"{error_msg} for {image_name}")
                            raise Exception(error_msg)
                        else:
                            error_msg = f"Response blocked with reason: {finish_reason}"
                            logger.error(f"{error_msg} for {image_name}")
                            raise Exception(error_msg)
                    else:
                        error_msg = "Empty response from Gemini API"
                        logger.error(f"{error_msg} for {image_name}")
                        raise Exception(error_msg)
                
                # Parse response
                response_text = response.text.strip()
            except Exception as api_error:
                # Re-raise API errors to be caught by caller
                raise
            
            # Try to extract JSON from response (may be wrapped in markdown code blocks)
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            # Parse JSON response
            try:
                clinical_data = json.loads(response_text)
            except json.JSONDecodeError:
                # If JSON parsing fails, create a structured response from text
                logger.warning(f"Failed to parse JSON from Gemini response for {image_name}")
                clinical_data = {
                    "summary": response_text,
                    "measurements": {},
                    "abnormalities": [],
                    "recommendations": []
                }
            
            result = {
                "summary": clinical_data.get("summary", response_text),
                "measurements": clinical_data.get("measurements", {}),
                "abnormalities": clinical_data.get("abnormalities", []),
                "prescriptions": clinical_data.get("prescriptions", []),
                "exercises": clinical_data.get("exercises", []),
                "dietary": clinical_data.get("dietary", []),
                "recommendations": clinical_data.get("recommendations", []),
                "raw_response": response_text,
                "timestamp": datetime.utcnow().isoformat(),
                "model_used": self.model_name
            }
            
            logger.info(f"Generated clinical summary for {image_name}")
            return result
            
        except Exception as e:
            logger.error(f"Error generating clinical summary for {image_name}: {str(e)}")
            return {
                "summary": f"Error analyzing image: {str(e)}",
                "measurements": {},
                "abnormalities": [],
                "prescriptions": [],
                "exercises": [],
                "dietary": [],
                "recommendations": [],
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "model_used": self.model_name
            }

