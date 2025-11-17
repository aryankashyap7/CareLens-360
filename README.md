# CareLens 360 🏥

A clinical summarization dashboard that uses Google Cloud services and Gemini Pro Vision API to analyze medical images and generate clinical summaries.

## Features

- **📸 Scan Patient Folders**: Automatically scan patient folders in Google Cloud Storage and generate clinical summaries for all medical images
- **📊 Patient Analysis (Single Page)**:
  - Aggregated overview of all reports for a patient (abnormalities, key measurements)
  - File-wise analysis for each individual image/report with full clinical summary
  - Combined recommendations: prescriptions, exercise suggestions, dietary guidance, and general advice
- **💬 Question & Answer**: Ask natural-language questions (e.g., "What are the main concerns?", "What dietary changes are recommended?") and get answers based on the patient's reports

## Architecture

```
CareLens 360
├── Google Cloud Storage (GCS)     → Stores patient folders with medical images
├── Gemini Pro Vision API          → Generates clinical summaries from images
├── Firestore                      → Stores summaries and metadata
└── Streamlit UI                   → Interactive dashboard for users
```

## Tech Stack

- **Streamlit**: Web UI framework
- **Google Cloud Storage**: Image storage and retrieval
- **Gemini Pro Vision API**: Medical image analysis and summarization
- **Firestore**: NoSQL database for storing summaries
- **Python 3.11+**: Backend language

## Project Structure

```
CareLens-360/
├── src/
│   ├── __init__.py           # Package initialization
│   ├── config.py             # Configuration management
│   ├── gcs_client.py         # Google Cloud Storage client
│   ├── gemini_client.py      # Gemini Pro / Vision API client
│   ├── firestore_client.py   # Firestore client
│   └── app.py                # Main Streamlit single‑page application
├── tests/
│   ├── __init__.py
│   └── test_config.py        # Configuration tests
├── requirements.txt          # Python dependencies
├── Dockerfile                # Container configuration
├── cloudbuild.yaml           # Cloud Build configuration
├── deploy.sh                 # Convenience deploy script
├── run_local.py              # Local dev runner
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore rules
├── QUICKSTART.md             # Quick start guide
└── README.md                 # This file
```

## Prerequisites

1. **Google Cloud Project** with the following APIs enabled:
   - Cloud Storage API
   - Firestore API
   - Cloud Run API (for deployment)

2. **Service Account** with the following permissions:
   - Cloud Storage Object Viewer
   - Firestore User
   - Cloud Run Admin (for deployment)

3. **Gemini API Key** from [Google AI Studio](https://makersuite.google.com/app/apikey)

4. **GCS Bucket** with patient folders structured as:
   ```
   bucket-name/
   ├── patient-1/
   │   ├── image1.png
   │   ├── image2.jpg
   │   └── ...
   ├── patient-2/
   │   └── ...
   ```

## Installation

### Local Development

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd CareLens-360
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and fill in your values:
   ```env
   GCP_PROJECT_ID=your-project-id
   GCS_BUCKET_NAME=your-bucket-name
   FIRESTORE_COLLECTION=clinical_summaries
   GEMINI_API_KEY=your-gemini-api-key
   # Optional – defaults to gemini-1.5-pro in code
   GEMINI_MODEL=gemini-1.5-pro
   ```

5. **Set up Google Cloud credentials**:
   
   Option A: Using Application Default Credentials (recommended for local dev)
   ```bash
   gcloud auth application-default login
   ```
   
   Option B: Using Service Account JSON
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account-key.json"
   ```

6. **Run the application**:
   ```bash
   streamlit run src/app.py
   ```

   The app will be available at `http://localhost:8501`

## Usage (Single‑Page Flow)

### 1. Scan and Analyze a Patient

1. Select a patient from the **Select Patient** dropdown (each option corresponds to a folder in your GCS bucket).
2. Click **"🔍 Scan and Analyze"**.
3. For each image in the patient's folder, the app will:
   - Download the image from GCS
   - Generate a rich clinical summary using Gemini (summary, measurements, abnormalities, prescriptions, exercise and dietary recommendations)
   - Store the structured summary in Firestore
4. After processing, the page will show:
   - **Overview** – aggregated abnormalities and measurements across all reports
   - **File‑wise Analysis** – one expandable section per image/report, with the full clinical summary and extracted details
   - **Final Combined Report** – merged prescription, exercise, dietary, and general recommendations for the patient

### 2. Ask Questions About the Report

1. Scroll to the **"💬 Ask Questions About This Report"** section.
2. Enter any natural language question, for example:
   - "What are the main clinical concerns for this patient?"
   - "Summarize the key lab abnormalities."
   - "What dietary changes are recommended?"
3. Click **"🔍 Get Answer"**.
4. The app uses Gemini with the patient’s summaries as context and returns a tailored answer. If something is not present in the reports, the answer explicitly notes that.

## Deployment to Cloud Run

### Prerequisites

1. Enable required APIs:
   ```bash
   gcloud services enable cloudbuild.googleapis.com
   gcloud services enable run.googleapis.com
   gcloud services enable storage-api.googleapis.com
   gcloud services enable firestore.googleapis.com
   ```

2. Set up Cloud Build:
   ```bash
   gcloud builds submit --config cloudbuild.yaml
   ```

### Manual Deployment

1. **Build the Docker image**:
   ```bash
   docker build -t gcr.io/YOUR_PROJECT_ID/carelens-360:latest .
   ```

2. **Push to Google Container Registry**:
   ```bash
   docker push gcr.io/YOUR_PROJECT_ID/carelens-360:latest
   ```

3. **Deploy to Cloud Run**:
   ```bash
   gcloud run deploy carelens-360 \
     --image gcr.io/YOUR_PROJECT_ID/carelens-360:latest \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars GCP_PROJECT_ID=YOUR_PROJECT_ID,GCS_BUCKET_NAME=YOUR_BUCKET_NAME,GEMINI_API_KEY=YOUR_API_KEY,FIRESTORE_COLLECTION=clinical_summaries \
     --memory 2Gi \
     --cpu 2 \
     --timeout 3600
   ```

### Environment Variables in Cloud Run

Set the following environment variables in Cloud Run:
- `GCP_PROJECT_ID`: Your GCP project ID
- `GCS_BUCKET_NAME`: Your GCS bucket name
- `GEMINI_API_KEY`: Your Gemini API key
- `FIRESTORE_COLLECTION`: Firestore collection name (default: `clinical_summaries`)
- `GEMINI_MODEL`: Gemini model to use (default in code: `gemini-1.5-pro`)

### Service Account Permissions

Ensure your Cloud Run service account has:
- `roles/storage.objectViewer` (for GCS)
- `roles/datastore.user` (for Firestore)

## Configuration

### Supported Image Formats

- PNG, JPG, JPEG, GIF, BMP, TIFF, WEBP

### Image Size Limits

- Default maximum: 10 MB per image
- Configurable via `MAX_IMAGE_SIZE_MB` environment variable

### Firestore Collection Structure

Each document in Firestore has the following structure:
```json
{
  "patient_name": "patient-1",
  "image_name": "image1.png",
  "image_path": "patient-1/image1.png",
  "summary": "Clinical summary text...",
  "measurements": {
    "BP": "120/80 mmHg",
    "Heart Rate": "72 bpm"
  },
  "abnormalities": ["abnormality 1", "abnormality 2"],
  "prescriptions": [
    "Medication name - dosage - frequency - reason"
  ],
  "exercises": [
    "Exercise type - frequency - duration - notes"
  ],
  "dietary": [
    "Food/Item to include/avoid - reason - frequency"
  ],
  "recommendations": ["recommendation 1", "recommendation 2"],
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z",
  "model_used": "gemini-1.5-pro"
}
```

## Troubleshooting

### Common Issues

1. **"Bucket not found" error**:
   - Verify `GCS_BUCKET_NAME` is correct
   - Ensure the service account has Storage Object Viewer permissions

2. **"Permission denied" for Firestore**:
   - Ensure the service account has Datastore User role
   - Check that Firestore is enabled in your project

3. **Gemini API errors**:
   - Verify `GEMINI_API_KEY` is correct
   - Check API quota and rate limits
   - Ensure the model name is correct

4. **Image processing fails**:
   - Check image format is supported
   - Verify image size is within limits
   - Check network connectivity to GCS

## Security Considerations

- **API Keys**: Never commit API keys to version control. Use environment variables or Google Secret Manager.
- **Service Accounts**: Use least-privilege principle for service account permissions.
- **Data Privacy**: Ensure compliance with healthcare data regulations (HIPAA, etc.) when handling patient data.
- **Authentication**: Consider adding authentication to the Streamlit app for production use.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

See LICENSE file for details.

## Support

For issues and questions, please open an issue on the repository.

---

**Built with ❤️ for healthcare professionals**
