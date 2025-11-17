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

# Page configuration - hide sidebar
st.set_page_config(
    page_title="CareLens 360",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Hide sidebar completely
st.markdown("""
<style>
    [data-testid="stSidebar"] {
        display: none;
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
        "errors": []  # Track specific errors
    }
    
    try:
        # Get list of images for patient
        images = st.session_state.gcs_client.list_patient_images(patient_name)
        results["total_images"] = len(images)
        
        if not images:
            return results
        
        # Process each image
        progress_bar = st.progress(0)
        status_text = st.empty()
        error_container = st.container()
        
        for idx, image_path in enumerate(images):
            status_text.text(f"Processing {idx + 1}/{len(images)}: {image_path}")
            error_msg = None
            
            try:
                # Download image
                image = st.session_state.gcs_client.download_image(image_path)
                if image is None:
                    error_msg = f"Failed to download image: {image_path}"
                    logger.error(error_msg)
                    results["errors"].append({"image": image_path, "error": error_msg})
                    results["failed"] += 1
                    continue
                
                # Get image metadata
                try:
                    image_metadata = st.session_state.gcs_client.get_image_metadata(image_path)
                except Exception as e:
                    logger.warning(f"Could not get metadata for {image_path}: {str(e)}")
                    image_metadata = {}
                
                # Generate clinical summary
                try:
                    summary_data = st.session_state.gemini_client.generate_clinical_summary(
                        image, image_path
                    )
                    
                    # Check if there's an error in the summary
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
                
                # Save to Firestore
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
                    "summary": summary_data.get("summary", "")  # Full summary, no truncation
                })
                
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                logger.error(f"Error processing {image_path}: {str(e)}", exc_info=True)
                results["errors"].append({"image": image_path, "error": error_msg})
                results["failed"] += 1
            
            # Update progress
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
    
    # Aggregate all data
    all_measurements = {}
    all_abnormalities = []
    all_prescriptions = []
    all_exercises = []
    all_dietary = []
    all_recommendations = []
    
    for summary in summaries:
        # Aggregate measurements
        measurements = summary.get("measurements", {})
        for key, value in measurements.items():
            if key not in all_measurements:
                all_measurements[key] = []
            all_measurements[key].append(value)
        
        # Aggregate abnormalities
        abnormalities = summary.get("abnormalities", [])
        all_abnormalities.extend(abnormalities)
        
        # Aggregate prescriptions
        prescriptions = summary.get("prescriptions", [])
        all_prescriptions.extend(prescriptions)
        
        # Aggregate exercises
        exercises = summary.get("exercises", [])
        all_exercises.extend(exercises)
        
        # Aggregate dietary
        dietary = summary.get("dietary", [])
        all_dietary.extend(dietary)
        
        # Aggregate recommendations
        recommendations = summary.get("recommendations", [])
        all_recommendations.extend(recommendations)
    
    # Remove duplicates while preserving order
    all_abnormalities = list(dict.fromkeys(all_abnormalities))
    all_prescriptions = list(dict.fromkeys(all_prescriptions))
    all_exercises = list(dict.fromkeys(all_exercises))
    all_dietary = list(dict.fromkeys(all_dietary))
    all_recommendations = list(dict.fromkeys(all_recommendations))
    
    # Create comprehensive analysis
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
    st.title("🏥 CareLens 360")
    st.markdown("### Clinical Summarization Dashboard")
    st.markdown("---")
    
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
    
    # Main content area - Single page flow
    st.header("📸 Patient Analysis")
    st.markdown("Select a patient and generate comprehensive clinical analysis from their medical images.")
    
    # Display current configuration
    with st.expander("🔧 Configuration Info", expanded=False):
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
    
    # Get list of patients from GCS
    with st.spinner("Loading patients from GCS..."):
        try:
            patients = st.session_state.gcs_client.list_patients()
        except Exception as e:
            st.error(f"Error connecting to GCS: {str(e)}")
            st.info("Please check:")
            st.markdown("""
            - Bucket name is correct in `.env` file
            - GCP credentials are set up (`gcloud auth application-default login`)
            - Service account has Storage Object Viewer permissions
            - Bucket exists and is accessible
            """)
            return

    # Section: Add New Patient & Upload Reports
    st.markdown("---")
    st.subheader("➕ Add New Patient & Upload Reports")

    with st.expander("Add New Patient", expanded=False):
        new_patient_name = st.text_input("New patient name", key="new_patient_name")
        uploaded_files = st.file_uploader(
            "Upload report images (PNG, JPG, JPEG, TIFF, WEBP, BMP)",
            type=[ext.lstrip(".") for ext in Config.SUPPORTED_IMAGE_FORMATS],
            accept_multiple_files=True,
            key="new_patient_files",
        )
        create_clicked = st.button("Upload & Analyze New Patient", type="primary", key="btn_new_patient")

        if create_clicked:
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
                        st.success(f"Uploaded {upload_count} file(s) for {patient_name}. Starting analysis...")
                        # Run analysis pipeline for the new patient
                        with st.spinner(f"Scanning and analyzing {patient_name}..."):
                            scan_results = scan_patient_folder(patient_name)

                        st.session_state.current_patient = patient_name
                        summaries_new = st.session_state.firestore_client.get_patient_summaries(patient_name)
                        if summaries_new:
                            st.session_state.current_summaries = summaries_new
                            st.session_state.current_analysis = generate_patient_analysis(summaries_new)
                        else:
                            st.session_state.current_summaries = []
                            st.session_state.current_analysis = {}

                        # Ensure new patient appears in the existing list for this session
                        if patient_name not in patients:
                            patients.append(patient_name)
                            patients.sort()

                        # Show quick metrics
                        st.info(
                            f"New patient '{patient_name}' analyzed: "
                            f"{scan_results.get('processed', 0)} processed, "
                            f"{scan_results.get('failed', 0)} failed."
                        )
                except Exception as e:
                    st.error(f"Error creating new patient: {str(e)}")
                    logger.error(f"Error creating new patient {patient_name}: {str(e)}")

    # Inform if there are no existing patients yet
    if not patients:
        st.warning("No existing patients found in the GCS bucket yet. Use 'Add New Patient' above to upload reports.")

        # Optional debug tools
        if st.button("🔍 Debug: List All Blobs in Bucket"):
            try:
                with st.spinner("Listing all blobs..."):
                    all_blobs = list(st.session_state.gcs_client.bucket.list_blobs(max_results=50))
                    if all_blobs:
                        st.write(f"Found {len(all_blobs)} blob(s) in bucket:")
                        for blob in all_blobs[:20]:  # Show first 20
                            st.text(f"  - {blob.name}")
                        if len(all_blobs) > 20:
                            st.text(f"  ... and {len(all_blobs) - 20} more")
                    else:
                        st.info("No blobs found in the bucket.")
            except Exception as e:
                st.error(f"Error listing blobs: {str(e)}")

    # Existing patient selection (only meaningful if patients list is non-empty)
    selected_patient = st.selectbox("Select Existing Patient", patients, key="existing_patient_select") if patients else None

    # Initialize session state for current patient data
    if "current_patient" not in st.session_state:
        st.session_state.current_patient = None
    if "current_summaries" not in st.session_state:
        st.session_state.current_summaries = []
    if "current_analysis" not in st.session_state:
        st.session_state.current_analysis = {}
    
    # Scan button
    scan_clicked = st.button("🔍 Scan and Analyze", type="primary")
    
    if scan_clicked:
        if selected_patient:
            with st.spinner(f"Scanning and analyzing {selected_patient}..."):
                results = scan_patient_folder(selected_patient)
            
            # Store in session state
            st.session_state.current_patient = selected_patient
            
            # Show immediate results
            if results["processed"] > 0:
                st.success(f"✅ Processing complete! {results['processed']} image(s) processed successfully.")
            else:
                st.warning(f"⚠️ Processing completed with {results['failed']} failed image(s).")
            
            # Show metrics
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Images", results["total_images"])
            col2.metric("Processed", results["processed"])
            col3.metric("Failed", results["failed"])
            
            # Show errors if any
            if results.get("errors"):
                with st.expander("❌ Error Details", expanded=False):
                    for error_info in results["errors"]:
                        st.error(f"**{error_info['image'].split('/')[-1]}**: {error_info['error']}")
            
            # Get full summaries from Firestore immediately (report will be rendered below)
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
    
    # If we have a previously scanned patient and summaries, display the report once
    if st.session_state.current_patient and st.session_state.current_summaries and len(st.session_state.current_summaries) > 0:
        display_full_report(
            st.session_state.current_patient,
            st.session_state.current_summaries,
            st.session_state.current_analysis
        )


def display_full_report(patient_name: str, summaries: List[Dict[str, Any]], patient_analysis: Dict[str, Any]):
    """Display the complete patient report."""
    if not summaries or len(summaries) == 0:
        return
    
    # Ensure analysis is properly initialized
    if not patient_analysis or not patient_analysis.get("total_reports"):
        patient_analysis = generate_patient_analysis(summaries)
        st.session_state.current_analysis = patient_analysis
    
    st.markdown("---")
    st.success(f"📊 **Analysis for: {patient_name}**")
    st.markdown(f"*Based on {patient_analysis.get('total_reports', len(summaries))} report(s)*")
    
    # Display Patient Analysis Section - Overview
    st.markdown("---")
    st.header("📊 Overview")
    
    # Display aggregated abnormalities
    if patient_analysis.get("abnormalities"):
        with st.expander("⚠️ All Abnormalities Found", expanded=True):
            for abnormality in patient_analysis["abnormalities"]:
                st.warning(f"• {abnormality}")
    
    # Display aggregated measurements
    if patient_analysis.get("measurements"):
        with st.expander("📈 All Measurements", expanded=False):
            for param, values in patient_analysis["measurements"].items():
                if len(values) == 1:
                    st.metric(param, values[0])
                else:
                    st.text(f"{param}: {', '.join(map(str, values))} (from {len(values)} reports)")
    
    # File-wise Analysis Section
    st.markdown("---")
    st.header("📄 File-wise Analysis")
    st.markdown("**Detailed analysis for each individual report:**")
    
    # Display individual summaries with full details
    for idx, summary in enumerate(summaries, 1):
        with st.expander(f"📄 Report {idx}: {summary.get('image_name', 'Unknown')} - {summary.get('created_at', 'N/A')}", expanded=False):
            # Full clinical summary (no truncation)
            st.markdown("### Clinical Summary")
            st.write(summary.get("summary", "No summary available"))
            
            col1, col2 = st.columns(2)
            
            with col1:
                if summary.get("abnormalities"):
                    st.markdown("### ⚠️ Abnormalities")
                    for abnormality in summary.get("abnormalities", []):
                        st.warning(f"• {abnormality}")
                
                if summary.get("measurements"):
                    st.markdown("### 📈 Measurements")
                    for param, value in summary.get("measurements", {}).items():
                        st.metric(param, value)
            
            with col2:
                if summary.get("prescriptions"):
                    st.markdown("### 💊 Prescriptions")
                    st.caption("⚠️ Consult doctor before use")
                    for prescription in summary.get("prescriptions", []):
                        st.info(f"• {prescription}")
                
                if summary.get("exercises"):
                    st.markdown("### 🏃 Exercise Recommendations")
                    for exercise in summary.get("exercises", []):
                        st.success(f"• {exercise}")
                
                if summary.get("dietary"):
                    st.markdown("### 🍎 Dietary Recommendations")
                    for dietary_rec in summary.get("dietary", []):
                        st.info(f"• {dietary_rec}")
                
                if summary.get("recommendations"):
                    st.markdown("### 💡 Recommendations")
                    for rec in summary.get("recommendations", []):
                        st.info(f"• {rec}")
    
    # Final Combined Report Section
    st.markdown("---")
    st.header("📋 Final Combined Report")
    st.markdown("**Comprehensive recommendations combining all reports:**")
    
    # Show combined prescriptions
    if patient_analysis.get("prescriptions"):
        st.markdown("### 💊 Prescription Suggestions")
        st.warning("⚠️ **IMPORTANT**: These are AI-generated suggestions. Consult with a qualified healthcare professional before taking any medication. Do not self-medicate.")
        for prescription in patient_analysis["prescriptions"]:
            st.info(f"💊 {prescription}")
        st.markdown("")
    
    # Show combined exercises
    if patient_analysis.get("exercises"):
        st.markdown("### 🏃 Exercise Recommendations")
        for exercise in patient_analysis["exercises"]:
            st.success(f"🏃 {exercise}")
        st.markdown("")
    
    # Show combined dietary
    if patient_analysis.get("dietary"):
        st.markdown("### 🍎 Dietary Preferences & Recommendations")
        for dietary_rec in patient_analysis["dietary"]:
            st.info(f"🍎 {dietary_rec}")
        st.markdown("")
    
    # Show combined recommendations
    if patient_analysis.get("recommendations"):
        st.markdown("### 💡 General Recommendations")
        for rec in patient_analysis["recommendations"]:
            st.info(f"💡 {rec}")
        st.markdown("")
    
    # Query/Question Box
    st.markdown("---")
    st.header("💬 Ask Questions About This Report")
    st.markdown("Ask any question about the patient's reports and get AI-powered answers based on all the analysis above.")
    
    user_query = st.text_input("Enter your question", key="user_query", placeholder="e.g., What are the main concerns? What medications are suggested? What dietary changes are recommended?")
    
    answer_button = st.button("🔍 Get Answer", type="primary", key="answer_button")
    
    if answer_button and user_query:
        with st.spinner("Analyzing and generating answer..."):
            # Use Gemini to answer questions based on the summaries
            try:
                # Combine all summaries into context
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
                
                # Use Gemini to answer the question
                answer = st.session_state.gemini_client.model.generate_content(
                    f"""Based on the following patient reports, answer this question: {user_query}
                    
                    Patient Reports:
                    {context_text}
                    
                    Provide a clear, comprehensive answer based on the reports. If the information is not available in the reports, state that clearly."""
                )
                
                st.markdown("### Answer")
                st.write(answer.text)
                
            except Exception as e:
                st.error(f"Error generating answer: {str(e)}")
                logger.error(f"Error answering query: {str(e)}")


if __name__ == "__main__":
    main()

