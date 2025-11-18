"""
Main Streamlit application for CareLens 360.
Provides UI for scanning, querying, and searching clinical summaries.
"""

import streamlit as st
import logging
from typing import Dict, Any, List
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import Config
from src.gcs_client import GCSClient
from src.gemini_client import GeminiClient
from src.firestore_client import FirestoreClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="CareLens 360",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Enhanced Custom CSS - Premium Glassmorphism Design
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    /* ========== GLOBAL RESET ========== */
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
        font-family: 'Inter', 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* ========== HIDE STREAMLIT BRANDING ========== */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
    [data-testid="stToolbar"] {display: none;}
    [data-testid="stDecoration"] {display: none;}
    
    /* ========== MAIN BACKGROUND ========== */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 25%, #334155 50%, #1e293b 75%, #0f172a 100%);
        background-size: 400% 400%;
        animation: gradientShift 20s ease infinite;
        min-height: 100vh;
    }
    
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* ========== FLOATING BACKGROUND ORBS ========== */
    .stApp::before {
        content: '';
        position: fixed;
        top: -10%;
        right: 10%;
        width: 700px;
        height: 700px;
        background: radial-gradient(circle, rgba(99, 102, 241, 0.2) 0%, rgba(139, 92, 246, 0.1) 50%, transparent 70%);
        border-radius: 50%;
        filter: blur(100px);
        pointer-events: none;
        z-index: 0;
        animation: float 25s ease-in-out infinite;
    }
    
    .stApp::after {
        content: '';
        position: fixed;
        bottom: -15%;
        left: -5%;
        width: 600px;
        height: 600px;
        background: radial-gradient(circle, rgba(14, 165, 233, 0.2) 0%, rgba(6, 182, 212, 0.1) 50%, transparent 70%);
        border-radius: 50%;
        filter: blur(100px);
        pointer-events: none;
        z-index: 0;
        animation: float 30s ease-in-out infinite reverse;
    }
    
    @keyframes float {
        0%, 100% { transform: translate(0, 0) scale(1); }
        33% { transform: translate(50px, -50px) scale(1.1); }
        66% { transform: translate(-30px, 30px) scale(0.9); }
    }
    
    /* ========== MAIN CONTENT CONTAINER ========== */
    .block-container {
        padding: 3rem 2rem !important;
        max-width: 1400px !important;
        position: relative;
        z-index: 1;
    }
    
    /* ========== TYPOGRAPHY ========== */
    h1 {
        color: #ffffff !important;
        font-weight: 800 !important;
        font-size: 3.5rem !important;
        letter-spacing: -0.03em !important;
        text-align: center !important;
        margin-bottom: 1rem !important;
        text-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
        background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    h2 {
        color: #f1f5f9 !important;
        font-weight: 700 !important;
        font-size: 1.75rem !important;
        margin-top: 2rem !important;
        margin-bottom: 1rem !important;
        letter-spacing: -0.02em !important;
    }
    
    h3 {
        color: #e2e8f0 !important;
        font-weight: 600 !important;
        font-size: 1.3rem !important;
        margin-bottom: 0.75rem !important;
        margin-top: 1.5rem !important;
    }
    
    h4 {
        color: #cbd5e1 !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
        margin-bottom: 0.5rem !important;
        margin-top: 1rem !important;
    }
    
    p, div, span, li {
        color: #cbd5e1 !important;
        line-height: 1.7 !important;
    }
    
    /* Subtitle styling */
    .subtitle {
        text-align: center !important;
        color: #94a3b8 !important;
        font-size: 1.15rem !important;
        line-height: 1.7 !important;
        margin-bottom: 3rem !important;
        font-weight: 400 !important;
        max-width: 100vw;
        margin-left: auto;
        margin-right: auto;
    }
    
    /* ========== SECTION CONTAINERS ========== */
    .section-container {
        background: rgba(255, 255, 255, 0.06);
        backdrop-filter: blur(24px) saturate(180%);
        -webkit-backdrop-filter: blur(24px) saturate(180%);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 24px;
        padding: 2rem;
        margin-bottom: 2rem;
        box-shadow: 
            0 8px 32px rgba(0, 0, 0, 0.3),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .section-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
    }
    
    /* ========== BUTTONS ========== */
    .stButton > button {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.9) 0%, rgba(139, 92, 246, 0.9) 100%) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 12px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        letter-spacing: 0.01em !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 
            0 4px 20px rgba(99, 102, 241, 0.4),
            inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
        backdrop-filter: blur(10px) !important;
        cursor: pointer !important;
        width: 100%;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, rgba(99, 102, 241, 1) 0%, rgba(139, 92, 246, 1) 100%) !important;
        transform: translateY(-2px) !important;
        box-shadow: 
            0 6px 25px rgba(99, 102, 241, 0.5),
            inset 0 1px 0 rgba(255, 255, 255, 0.3) !important;
        border-color: rgba(255, 255, 255, 0.3) !important;
    }
    
    .stButton > button:active {
        transform: translateY(0) !important;
    }
    
    /* ========== INPUT FIELDS ========== */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select {
        background: rgba(255, 255, 255, 0.08) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 12px !important;
        color: #f1f5f9 !important;
        padding: 0.75rem 1rem !important;
        font-size: 0.95rem !important;
        transition: all 0.3s ease !important;
        backdrop-filter: blur(10px) !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus {
        border-color: rgba(99, 102, 241, 0.7) !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15) !important;
        background: rgba(255, 255, 255, 0.12) !important;
        outline: none !important;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: #64748b !important;
    }
    
    /* ========== LABELS ========== */
    .stTextInput > label,
    .stSelectbox > label,
    .stFileUploader > label {
        color: #cbd5e1 !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        margin-bottom: 0.5rem !important;
        letter-spacing: 0.01em !important;
    }
    
    /* ========== EXPANDER ========== */
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.06) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 12px !important;
        color: #e2e8f0 !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        padding: 0.875rem 1.25rem !important;
        transition: all 0.3s ease !important;
        backdrop-filter: blur(10px) !important;
    }
    
    .streamlit-expanderHeader:hover {
        background: rgba(255, 255, 255, 0.09) !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
    }
    
    .streamlit-expanderContent {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-top: none !important;
        border-radius: 0 0 12px 12px !important;
        backdrop-filter: blur(10px) !important;
        padding: 1rem !important;
    }
    
    /* ========== METRICS ========== */
    [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
        text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
    }
    
    [data-testid="stMetricLabel"] {
        color: #94a3b8 !important;
        font-size: 0.9rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em !important;
    }
    
    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.05);
        padding: 1.25rem;
        border-radius: 14px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
    }
    
    /* ========== ALERT MESSAGES ========== */
    .stSuccess, .element-container .stSuccess {
        background: rgba(34, 197, 94, 0.15) !important;
        border: 1px solid rgba(34, 197, 94, 0.4) !important;
        border-radius: 12px !important;
        color: #86efac !important;
        backdrop-filter: blur(10px) !important;
        padding: 0.875rem 1.25rem !important;
        font-weight: 500 !important;
    }
    
    .stWarning, .element-container .stWarning {
        background: rgba(251, 191, 36, 0.15) !important;
        border: 1px solid rgba(251, 191, 36, 0.4) !important;
        border-radius: 12px !important;
        color: #fde047 !important;
        backdrop-filter: blur(10px) !important;
        padding: 0.875rem 1.25rem !important;
        font-weight: 500 !important;
    }
    
    .stError, .element-container .stError {
        background: rgba(239, 68, 68, 0.15) !important;
        border: 1px solid rgba(239, 68, 68, 0.4) !important;
        border-radius: 12px !important;
        color: #fca5a5 !important;
        backdrop-filter: blur(10px) !important;
        padding: 0.875rem 1.25rem !important;
        font-weight: 500 !important;
    }
    
    .stInfo, .element-container .stInfo {
        background: rgba(59, 130, 246, 0.15) !important;
        border: 1px solid rgba(59, 130, 246, 0.4) !important;
        border-radius: 12px !important;
        color: #93c5fd !important;
        backdrop-filter: blur(10px) !important;
        padding: 0.875rem 1.25rem !important;
        font-weight: 500 !important;
    }
    
    /* ========== PROGRESS BAR ========== */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%) !important;
        border-radius: 10px !important;
        height: 10px !important;
    }
    
    .stProgress > div > div {
        background: rgba(255, 255, 255, 0.1) !important;
        border-radius: 10px !important;
        height: 10px !important;
    }
    
    /* ========== FILE UPLOADER ========== */
    [data-testid="stFileUploader"] {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 2px dashed rgba(255, 255, 255, 0.2) !important;
        border-radius: 16px !important;
        padding: 2rem !important;
        transition: all 0.3s ease !important;
        backdrop-filter: blur(10px) !important;
    }
    
    [data-testid="stFileUploader"]:hover {
        border-color: rgba(99, 102, 241, 0.6) !important;
        background: rgba(255, 255, 255, 0.08) !important;
        border-style: solid !important;
    }
    
    [data-testid="stFileUploader"] section {
        border: none !important;
        padding: 0 !important;
    }
    
    [data-testid="stFileUploader"] button {
        background: rgba(99, 102, 241, 0.2) !important;
        border: 1px solid rgba(99, 102, 241, 0.4) !important;
        color: #a5b4fc !important;
        border-radius: 10px !important;
    }
    
    /* ========== DIVIDER ========== */
    hr {
        border: none !important;
        height: 1px !important;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.15), transparent) !important;
        margin: 2.5rem 0 !important;
    }
    
    /* ========== SCROLLBAR ========== */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.2);
        border-radius: 10px;
        border: 2px solid transparent;
        background-clip: padding-box;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.3);
        background-clip: padding-box;
    }
    
    /* ========== SPINNER ========== */
    .stSpinner > div {
        border-top-color: #6366f1 !important;
    }
    
    /* ========== RESPONSIVE ========== */
    @media (max-width: 768px) {
        h1 {
            font-size: 2.5rem !important;
        }
        
        .block-container {
            padding: 2rem 1rem !important;
        }
        
        .section-container {
            padding: 1.5rem !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "gcs_client" not in st.session_state:
    st.session_state.gcs_client = None
if "gemini_client" not in st.session_state:
    st.session_state.gemini_client = None
if "firestore_client" not in st.session_state:
    st.session_state.firestore_client = None


def initialize_clients():
    """Initialize GCP clients if not already initialized."""
    try:
        if st.session_state.gcs_client is None:
            st.session_state.gcs_client = GCSClient()
        if st.session_state.gemini_client is None:
            st.session_state.gemini_client = GeminiClient()
        if st.session_state.firestore_client is None:
            st.session_state.firestore_client = FirestoreClient()
        return True
    except Exception as e:
        st.error(f"Error initializing clients: {str(e)}")
        logger.error(f"Error initializing clients: {str(e)}")
        return False


def scan_patient_folder(patient_name: str) -> Dict[str, Any]:
    """
    Scan a patient folder and generate summaries for all images.
    
    Args:
        patient_name: Name of the patient folder
        
    Returns:
        Dict with results and statistics
    """
    results = {
        "patient_name": patient_name,
        "total_images": 0,
        "processed": 0,
        "failed": 0,
        "summaries": [],
        "errors": []
    }
    
    try:
        images = st.session_state.gcs_client.list_patient_images(patient_name)
        results["total_images"] = len(images)
        
        if not images:
            return results
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for idx, image_path in enumerate(images):
            status_text.text(f"Processing {idx + 1}/{len(images)}: {image_path}")
            
            try:
                image = st.session_state.gcs_client.download_image(image_path)
                if image is None:
                    error_msg = f"Failed to download image: {image_path}"
                    logger.error(error_msg)
                    results["errors"].append({"image": image_path, "error": error_msg})
                    results["failed"] += 1
                    continue
                
                try:
                    image_metadata = st.session_state.gcs_client.get_image_metadata(image_path)
                except Exception as e:
                    logger.warning(f"Could not get metadata for {image_path}: {str(e)}")
                    image_metadata = {}
                
                try:
                    summary_data = st.session_state.gemini_client.generate_clinical_summary(
                        image, image_path
                    )
                    
                    if "error" in summary_data:
                        error_msg = f"Gemini API error: {summary_data.get('error', 'Unknown error')}"
                        logger.error(f"{error_msg} for {image_path}")
                        results["errors"].append({"image": image_path, "error": error_msg})
                        results["failed"] += 1
                        continue
                        
                except Exception as e:
                    error_msg = f"Gemini API error: {str(e)}"
                    logger.error(f"{error_msg} for {image_path}")
                    results["errors"].append({"image": image_path, "error": error_msg})
                    results["failed"] += 1
                    continue
                
                try:
                    doc_id = st.session_state.firestore_client.save_summary(
                        patient_name=patient_name,
                        image_name=image_path,
                        summary_data=summary_data,
                        image_metadata=image_metadata
                    )
                except Exception as e:
                    error_msg = f"Firestore save error: {str(e)}"
                    logger.error(f"{error_msg} for {image_path}")
                    results["errors"].append({"image": image_path, "error": error_msg})
                    results["failed"] += 1
                    continue
                
                results["processed"] += 1
                results["summaries"].append({
                    "image_path": image_path,
                    "doc_id": doc_id,
                    "summary": summary_data.get("summary", "")
                })
                
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                logger.error(f"Error processing {image_path}: {str(e)}", exc_info=True)
                results["errors"].append({"image": image_path, "error": error_msg})
                results["failed"] += 1
            
            progress_bar.progress((idx + 1) / len(images))
        
        status_text.text("Processing complete!")
        progress_bar.empty()
        
    except Exception as e:
        error_msg = f"Error scanning patient folder: {str(e)}"
        logger.error(error_msg, exc_info=True)
        st.error(error_msg)
    
    return results


def generate_patient_analysis(summaries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate comprehensive patient analysis from all summaries.
    
    Args:
        summaries: List of all summaries for a patient
        
    Returns:
        Dict with aggregated patient analysis
    """
    if not summaries:
        return {}
    
    all_measurements = {}
    all_abnormalities = []
    all_prescriptions = []
    all_exercises = []
    all_dietary = []
    all_recommendations = []
    
    for summary in summaries:
        measurements = summary.get("measurements", {})
        for key, value in measurements.items():
            if key not in all_measurements:
                all_measurements[key] = []
            all_measurements[key].append(value)
        
        abnormalities = summary.get("abnormalities", [])
        all_abnormalities.extend(abnormalities)
        
        prescriptions = summary.get("prescriptions", [])
        all_prescriptions.extend(prescriptions)
        
        exercises = summary.get("exercises", [])
        all_exercises.extend(exercises)
        
        dietary = summary.get("dietary", [])
        all_dietary.extend(dietary)
        
        recommendations = summary.get("recommendations", [])
        all_recommendations.extend(recommendations)
    
    all_abnormalities = list(dict.fromkeys(all_abnormalities))
    all_prescriptions = list(dict.fromkeys(all_prescriptions))
    all_exercises = list(dict.fromkeys(all_exercises))
    all_dietary = list(dict.fromkeys(all_dietary))
    all_recommendations = list(dict.fromkeys(all_recommendations))
    
    analysis = {
        "total_reports": len(summaries),
        "measurements": all_measurements,
        "abnormalities": all_abnormalities,
        "prescriptions": all_prescriptions,
        "exercises": all_exercises,
        "dietary": all_dietary,
        "recommendations": all_recommendations,
        "summary_text": f"Comprehensive analysis based on {len(summaries)} report(s)."
    }
    
    return analysis


def main():
    """Main application function."""
    
    # Header
    st.markdown('<h1>CareLens 360</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Advanced clinical summarization powered by Google Cloud and Gemini Flash API</p>', unsafe_allow_html=True)
    
    # Check configuration
    if not Config.validate():
        st.error("⚠️ Configuration Error")
        missing = Config.get_missing_configs()
        st.error(f"Missing required configuration: {', '.join(missing)}")
        st.info("Please set the required environment variables or update your .env file.")
        return
    
    # Initialize clients
    if not initialize_clients():
        return
    
    # Configuration Section
    st.markdown("## 🔧 Configuration & Connection")
    with st.expander("View Settings", expanded=False):
        st.text(f"GCS Bucket: {Config.GCS_BUCKET_NAME}")
        st.text(f"GCP Project: {Config.GCP_PROJECT_ID}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh Patient List"):
                st.rerun()
        with col2:
            if st.button("🔌 Test Connection"):
                success, message = st.session_state.gcs_client.test_connection()
                if success:
                    st.success(message)
                else:
                    st.error(message)
    
    st.divider()
    
    # Get list of patients
    with st.spinner("Loading patients from GCS..."):
        try:
            patients = st.session_state.gcs_client.list_patients()
        except Exception as e:
            st.error(f"Error connecting to GCS: {str(e)}")
            st.info("Please check your bucket configuration and credentials.")
            return
    
    # Add New Patient Section
    st.markdown("## ➕ Add New Patient")
    with st.expander("Upload New Patient Reports", expanded=False):
        new_patient_name = st.text_input(
            "Patient name", 
            key="new_patient_name", 
            placeholder="Enter patient name"
        )
        uploaded_files = st.file_uploader(
            "Upload report images (PNG, JPG, JPEG, TIFF, WEBP, BMP)",
            type=[ext.lstrip(".") for ext in Config.SUPPORTED_IMAGE_FORMATS],
            accept_multiple_files=True,
            key="new_patient_files",
        )
        
        if st.button("📤 Upload & Analyze", type="primary", key="btn_new_patient"):
            patient_name = new_patient_name.strip()
            if not patient_name:
                st.error("Please enter a patient name.")
            elif not uploaded_files:
                st.error("Please upload at least one report image.")
            else:
                try:
                    upload_count = 0
                    for f in uploaded_files:
                        data = f.read()
                        if not data:
                            continue
                        content_type = getattr(f, "type", None)
                        st.session_state.gcs_client.upload_patient_image(
                            patient_name=patient_name,
                            file_name=f.name,
                            file_bytes=data,
                            content_type=content_type,
                        )
                        upload_count += 1
                    
                    if upload_count == 0:
                        st.error("No valid files were uploaded.")
                    else:
                        st.success(f"✅ Uploaded {upload_count} file(s) for {patient_name}")
                        
                        with st.spinner(f"Analyzing reports for {patient_name}..."):
                            scan_results = scan_patient_folder(patient_name)
                        
                        st.session_state.current_patient = patient_name
                        summaries_new = st.session_state.firestore_client.get_patient_summaries(patient_name)
                        if summaries_new:
                            st.session_state.current_summaries = summaries_new
                            st.session_state.current_analysis = generate_patient_analysis(summaries_new)
                        else:
                            st.session_state.current_summaries = []
                            st.session_state.current_analysis = {}
                        
                        if patient_name not in patients:
                            patients.append(patient_name)
                            patients.sort()
                        
                        st.info(
                            f"Analysis complete: "
                            f"{scan_results.get('processed', 0)} processed, "
                            f"{scan_results.get('failed', 0)} failed."
                        )
                except Exception as e:
                    st.error(f"Error creating new patient: {str(e)}")
                    logger.error(f"Error creating new patient {patient_name}: {str(e)}")
    
    st.divider()
    
    # Existing Patient Analysis
    if not patients:
        st.warning("No existing patients found. Use 'Add New Patient' above to upload reports.")
    else:
        st.markdown("## 📊 Patient Analysis")
        
        selected_patient = st.selectbox("Select Patient", patients, key="existing_patient_select")
        
        # Initialize session state
        if "current_patient" not in st.session_state:
            st.session_state.current_patient = None
        if "current_summaries" not in st.session_state:
            st.session_state.current_summaries = []
        if "current_analysis" not in st.session_state:
            st.session_state.current_analysis = {}
        
        if st.button("🔍 Scan and Analyze", type="primary"):
            if selected_patient:
                with st.spinner(f"Scanning and analyzing {selected_patient}..."):
                    results = scan_patient_folder(selected_patient)
                
                st.session_state.current_patient = selected_patient
                
                if results["processed"] > 0:
                    st.success(f"✅ Processing complete! {results['processed']} image(s) processed successfully.")
                else:
                    st.warning(f"⚠️ Processing completed with {results['failed']} failed image(s).")
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Images", results["total_images"])
                col2.metric("Processed", results["processed"])
                col3.metric("Failed", results["failed"])
                
                if results.get("errors"):
                    with st.expander("❌ Error Details", expanded=False):
                        for error_info in results["errors"]:
                            st.error(f"**{error_info['image'].split('/')[-1]}**: {error_info['error']}")
                
                try:
                    summaries = st.session_state.firestore_client.get_patient_summaries(selected_patient)
                    if summaries and len(summaries) > 0:
                        st.session_state.current_summaries = summaries
                        st.session_state.current_analysis = generate_patient_analysis(summaries)
                    else:
                        st.session_state.current_summaries = []
                        st.session_state.current_analysis = {}
                        if results["processed"] == 0:
                            st.info("No summaries found. Please ensure images were processed successfully.")
                except Exception as e:
                    logger.error(f"Error loading summaries: {str(e)}")
                    st.error(f"Error loading summaries: {str(e)}")
    
    # Display full report if available
    if st.session_state.get("current_patient") and st.session_state.get("current_summaries") and len(st.session_state.current_summaries) > 0:
        display_full_report(
            st.session_state.current_patient,
            st.session_state.current_summaries,
            st.session_state.current_analysis
        )


def display_full_report(patient_name: str, summaries: List[Dict[str, Any]], patient_analysis: Dict[str, Any]):
    """Display the complete patient report."""
    if not summaries or len(summaries) == 0:
        return
    
    if not patient_analysis or not patient_analysis.get("total_reports"):
        patient_analysis = generate_patient_analysis(summaries)
        st.session_state.current_analysis = patient_analysis
    
    st.divider()
    st.success(f"📊 **Analysis for: {patient_name}**")
    st.markdown(f"*Based on {patient_analysis.get('total_reports', len(summaries))} report(s)*")
    
    st.markdown("### ⚠️ Overview")
    
    if patient_analysis.get("abnormalities"):
        with st.expander("All Abnormalities Found", expanded=True):
            for abnormality in patient_analysis["abnormalities"]:
                st.warning(f"• {abnormality}")
    
    if patient_analysis.get("measurements"):
        with st.expander("📈 All Measurements", expanded=False):
            for param, values in patient_analysis["measurements"].items():
                if len(values) == 1:
                    st.metric(param, values[0])
                else:
                    st.text(f"{param}: {', '.join(map(str, values))} (from {len(values)} reports)")
    
    st.divider()
    
    # File-wise analysis
    st.markdown("## 📄 File-wise Analysis")
    st.markdown(f"<p class='subtitle'>Detailed breakdown of each individual report ({len(summaries)} total)</p>", unsafe_allow_html=True)
    st.markdown("")
    
    for idx, summary in enumerate(summaries, 1):
        with st.expander(f"📄 **Report {idx}**: {summary.get('image_name', 'Unknown')}", expanded=False):
            st.caption(f"📅 Created: {summary.get('created_at', 'N/A')}")
            st.markdown("---")
            st.markdown("#### 📋 Clinical Summary")
            st.write(summary.get("summary", "No summary available"))
            st.markdown("")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if summary.get("abnormalities"):
                    st.markdown("#### ⚠️ Abnormalities")
                    for abnormality in summary.get("abnormalities", []):
                        st.warning(f"• {abnormality}")
                
                if summary.get("measurements"):
                    st.markdown("#### 📈 Measurements")
                    for param, value in summary.get("measurements", {}).items():
                        st.metric(param, value)
            
            with col2:
                if summary.get("prescriptions"):
                    st.markdown("#### 💊 Prescriptions")
                    st.caption("⚠️ Consult doctor before use")
                    for prescription in summary.get("prescriptions", []):
                        st.info(f"• {prescription}")
                
                if summary.get("exercises"):
                    st.markdown("#### 🏃 Exercise Recommendations")
                    for exercise in summary.get("exercises", []):
                        st.success(f"• {exercise}")
                
                if summary.get("dietary"):
                    st.markdown("#### 🍎 Dietary Recommendations")
                    for dietary_rec in summary.get("dietary", []):
                        st.info(f"• {dietary_rec}")
                
                if summary.get("recommendations"):
                    st.markdown("#### 💡 Recommendations")
                    for rec in summary.get("recommendations", []):
                        st.info(f"• {rec}")
    
    st.divider()
    
    # Final combined report
    st.markdown("## 📋 Final Combined Report")
    st.markdown("<p class='subtitle'>Comprehensive analysis and recommendations across all reports</p>", unsafe_allow_html=True)
    st.markdown("")
    
    # Check if we have any data to display
    has_content = any([
        patient_analysis.get("prescriptions"),
        patient_analysis.get("exercises"),
        patient_analysis.get("dietary"),
        patient_analysis.get("recommendations")
    ])
    
    if not has_content:
        st.info("ℹ️ No combined recommendations available. The analysis may be based on individual report findings shown above.")
    else:
        if patient_analysis.get("prescriptions"):
            st.markdown("#### 💊 Prescription Suggestions")
            st.warning("⚠️ **IMPORTANT**: These are AI-generated suggestions. Always consult with a qualified healthcare professional before taking any medication.")
            for prescription in patient_analysis["prescriptions"]:
                st.info(f"💊 {prescription}")
            st.markdown("")
        
        if patient_analysis.get("exercises"):
            st.markdown("#### 🏃 Exercise Recommendations")
            for exercise in patient_analysis["exercises"]:
                st.success(f"🏃 {exercise}")
            st.markdown("")
        
        if patient_analysis.get("dietary"):
            st.markdown("#### 🍎 Dietary Preferences & Recommendations")
            for dietary_rec in patient_analysis["dietary"]:
                st.info(f"🍎 {dietary_rec}")
            st.markdown("")
        
        if patient_analysis.get("recommendations"):
            st.markdown("#### 💡 General Recommendations")
            for rec in patient_analysis["recommendations"]:
                st.info(f"💡 {rec}")
            st.markdown("")
    
    st.divider()
    
    # Q&A section
    st.markdown("### 💬 Ask Questions About This Report")
    st.markdown("Ask any question about the patient's reports and get AI-powered answers.")
    
    user_query = st.text_input("Enter your question", key="user_query", placeholder="e.g., What are the main concerns? What medications are suggested?")
    
    if st.button("🔍 Get Answer", type="primary", key="answer_button"):
        if user_query:
            with st.spinner("Analyzing and generating answer..."):
                try:
                    context_text = f"Patient: {patient_name}\n\n"
                    context_text += f"Total Reports: {len(summaries)}\n\n"
                    
                    for idx, summary in enumerate(summaries, 1):
                        context_text += f"Report {idx} ({summary.get('image_name', 'Unknown')}):\n"
                        context_text += f"Summary: {summary.get('summary', '')}\n"
                        if summary.get('measurements'):
                            context_text += f"Measurements: {summary.get('measurements')}\n"
                        if summary.get('abnormalities'):
                            context_text += f"Abnormalities: {', '.join(summary.get('abnormalities', []))}\n"
                        context_text += "\n"
                    
                    answer = st.session_state.gemini_client.model.generate_content(
                        f"""Based on the following patient reports, answer this question: {user_query}
                        
                        Patient Reports:
                        {context_text}
                        
                        Provide a clear, comprehensive answer based on the reports. If the information is not available in the reports, state that clearly."""
                    )
                    
                    st.markdown("#### Answer")
                    st.write(answer.text)
                    
                except Exception as e:
                    st.error(f"Error generating answer: {str(e)}")
                    logger.error(f"Error answering query: {str(e)}")
        else:
            st.warning("Please enter a question first.")


if __name__ == "__main__":
    main()
