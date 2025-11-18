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

### High-Level Overview

```
CareLens 360
├── Google Cloud Storage (GCS)     → Stores patient folders with medical images
├── Gemini Pro Vision API          → Generates clinical summaries from images
├── Firestore                      → Stores summaries and metadata
└── Streamlit UI                   → Interactive dashboard for users
```

### Detailed Architecture Diagram

```
╔══════════════════════════════════════════════════════════════════════════════════╗
║                           CARELENS 360 ARCHITECTURE                              ║
╚══════════════════════════════════════════════════════════════════════════════════╝

┌──────────────────────────────────────────────────────────────────────────────────┐
│                              PRESENTATION LAYER                                  │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────┐    │
│  │                      Streamlit Web Interface                            │    │
│  │                         (src/app.py)                                    │    │
│  │                                                                          │    │
│  │  Features:                                                               │    │
│  │  • Patient folder scanning                                              │    │
│  │  • File upload & management                                             │    │
│  │  • Clinical summary display                                             │    │
│  │  • File-wise analysis views                                             │    │
│  │  • Combined report generation                                           │    │
│  │  • Q&A interface (natural language queries)                             │    │
│  │  • Glassmorphism UI with dark theme                                     │    │
│  └────────────────────────────────────────────────────────────────────────┘    │
│                                       │                                          │
└───────────────────────────────────────┼──────────────────────────────────────────┘
                                        │
                                        ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                            APPLICATION LAYER                                     │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────┐      │
│  │                     Configuration Manager                             │      │
│  │                        (src/config.py)                                │      │
│  │                                                                        │      │
│  │  • Environment variable management                                    │      │
│  │  • GCP Project ID, GCS Bucket, Firestore Collection                  │      │
│  │  • Gemini API Key & Model configuration                               │      │
│  │  • Image format & size validation                                     │      │
│  │  • Configuration validation                                            │      │
│  └──────────────────────────────────────────────────────────────────────┘      │
│                                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐        │
│  │   GCS Client    │  │ Gemini Client   │  │  Firestore Client       │        │
│  │  (gcs_client)   │  │(gemini_client)  │  │ (firestore_client)      │        │
│  │                 │  │                 │  │                         │        │
│  │ • List patients │  │ • Image         │  │ • Save summaries        │        │
│  │ • List images   │  │   analysis      │  │ • Query by patient      │        │
│  │ • Download      │  │ • Clinical      │  │ • NL search             │        │
│  │   images        │  │   summary       │  │ • Get all patients      │        │
│  │ • Upload images │  │   generation    │  │ • Measurement query     │        │
│  │ • Get metadata  │  │ • JSON parsing  │  │ • Timestamp mgmt        │        │
│  │ • Format        │  │ • Fallback      │  │ • Composite keys        │        │
│  │   validation    │  │   models        │  │                         │        │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────────────┘        │
│           │                    │                     │                          │
└───────────┼────────────────────┼─────────────────────┼──────────────────────────┘
            │                    │                     │
            ▼                    ▼                     ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                         EXTERNAL SERVICES LAYER                                  │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐  │
│  │  Google Cloud        │  │   Gemini Pro/Flash   │  │   Cloud Firestore    │  │
│  │  Storage (GCS)       │  │      Vision API      │  │    (NoSQL DB)        │  │
│  │                      │  │                      │  │                      │  │
│  │  Bucket Structure:   │  │  Models:             │  │  Collection:         │  │
│  │  ├─ patient-1/       │  │  • gemini-1.5-pro    │  │  clinical_summaries  │  │
│  │  │  ├─ report1.png   │  │  • gemini-1.5-flash  │  │                      │  │
│  │  │  ├─ scan1.jpg     │  │  • gemini-pro-vision │  │  Document Schema:    │  │
│  │  │  └─ lab1.tiff     │  │                      │  │  {                   │  │
│  │  ├─ patient-2/       │  │  Analysis:           │  │   patient_name,      │  │
│  │  │  └─ ...           │  │  • Clinical summary  │  │   image_name,        │  │
│  │  └─ ...              │  │  • Measurements      │  │   summary,           │  │
│  │                      │  │  • Abnormalities     │  │   measurements,      │  │
│  │  Features:           │  │  • Prescriptions     │  │   abnormalities,     │  │
│  │  • Hierarchical      │  │  • Exercise recs     │  │   prescriptions,     │  │
│  │    folder structure  │  │  • Dietary advice    │  │   exercises,         │  │
│  │  • Image versioning  │  │  • Recommendations   │  │   dietary,           │  │
│  │  • Metadata storage  │  │                      │  │   recommendations,   │  │
│  │  • Access control    │  │  Safety Filters:     │  │   created_at,        │  │
│  │                      │  │  • Content blocking  │  │   updated_at,        │  │
│  │  Supported Formats:  │  │  • Recitation check  │  │   model_used         │  │
│  │  PNG, JPG, JPEG,     │  │  • Error handling    │  │  }                   │  │
│  │  GIF, BMP, TIFF,     │  │                      │  │                      │  │
│  │  WEBP                │  │  Response Format:    │  │  Features:           │  │
│  │                      │  │  • Structured JSON   │  │  • Patient queries   │  │
│  │  Max Size: 10MB      │  │  • Markdown parsing  │  │  • NL search         │  │
│  └──────────────────────┘  └──────────────────────┘  │  • Sorting           │  │
│                                                       │  • Timestamp mgmt    │  │
│                                                       └──────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────────┐
│                              DATA FLOW                                           │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    1. Patient Folder Scanning Flow                      │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│     User Selection                                                               │
│          │                                                                       │
│          ▼                                                                       │
│     List Patients ──────► GCS Client ──────► List folders in bucket            │
│          │                                                                       │
│          ▼                                                                       │
│     Select Patient ─────► List Patient Images ────► Get all images             │
│          │                                                                       │
│          ▼                                                                       │
│     Scan & Analyze                                                               │
│          │                                                                       │
│          ├──► For each image:                                                   │
│          │    1. Download from GCS ────────────────────┐                        │
│          │                                              │                        │
│          │    2. Send to Gemini API ───────────────────┼──► Analyze image       │
│          │                                              │    Extract data        │
│          │    3. Parse JSON response ◄─────────────────┘    Generate summary    │
│          │                                                                       │
│          │    4. Save to Firestore ─────────────────────► Store summary         │
│          │                                                  + metadata           │
│          │                                                                       │
│          ▼                                                                       │
│     Display Results ──► Aggregated Analysis                                     │
│                      ├─► Overview (abnormalities, measurements)                 │
│                      ├─► File-wise breakdown                                    │
│                      └─► Combined recommendations                               │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    2. New Patient Upload Flow                           │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│     User Input                                                                   │
│          │                                                                       │
│          ▼                                                                       │
│     Enter Patient Name + Upload Files                                           │
│          │                                                                       │
│          ▼                                                                       │
│     Validate Input ────► Check name & files                                     │
│          │                                                                       │
│          ▼                                                                       │
│     Upload to GCS ─────► For each file:                                         │
│          │                Create patient_name/filename path                     │
│          │                Upload with metadata                                  │
│          │                                                                       │
│          ▼                                                                       │
│     Auto-Scan ─────────► Trigger scan_patient_folder()                          │
│          │                (same as flow 1)                                      │
│          │                                                                       │
│          ▼                                                                       │
│     Display Results                                                              │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    3. Q&A Natural Language Query Flow                   │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│     User Query                                                                   │
│          │                                                                       │
│          ▼                                                                       │
│     Enter Question ────► "What are the main concerns?"                          │
│          │                                                                       │
│          ▼                                                                       │
│     Fetch Context ─────► Get all summaries from Firestore                       │
│          │                for current patient                                   │
│          │                                                                       │
│          ▼                                                                       │
│     Build Prompt ──────► Combine query + all summaries                          │
│          │                + measurements + abnormalities                        │
│          │                                                                       │
│          ▼                                                                       │
│     Send to Gemini ────► Generate contextual answer                             │
│          │                                                                       │
│          ▼                                                                       │
│     Display Answer ────► Show in UI                                             │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────────┐
│                          DEPLOYMENT ARCHITECTURE                                 │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────┐      │
│  │                        Development Environment                        │      │
│  │                                                                        │      │
│  │  • Local Python environment (venv)                                    │      │
│  │  • Streamlit dev server (port 8501)                                   │      │
│  │  • .env file for configuration                                        │      │
│  │  • GCloud CLI authentication                                          │      │
│  │  • run_local.py script                                                │      │
│  └──────────────────────────────────────────────────────────────────────┘      │
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────┐      │
│  │                        Production Environment                         │      │
│  │                                                                        │      │
│  │  ┌─────────────────────────────────────────────────────────────┐    │      │
│  │  │                    Google Cloud Run                          │    │      │
│  │  │                                                               │    │      │
│  │  │  • Containerized deployment (Docker)                         │    │      │
│  │  │  • Auto-scaling (0 to N instances)                           │    │      │
│  │  │  • HTTPS endpoint with Cloud Load Balancer                   │    │      │
│  │  │  • Service account authentication                            │    │      │
│  │  │  • Environment variables injection                           │    │      │
│  │  │  • Memory: 2GB, CPU: 2 cores                                 │    │      │
│  │  │  • Timeout: 3600s (1 hour)                                   │    │      │
│  │  │  • Region: us-central1 (configurable)                        │    │      │
│  │  └─────────────────────────────────────────────────────────────┘    │      │
│  │                                                                        │      │
│  │  Build Process:                                                        │      │
│  │  1. Cloud Build (cloudbuild.yaml)                                     │      │
│  │  2. Docker image creation (Dockerfile)                                │      │
│  │  3. Push to Container Registry                                        │      │
│  │  4. Deploy to Cloud Run                                               │      │
│  │  5. Configure IAM permissions                                         │      │
│  └──────────────────────────────────────────────────────────────────────┘      │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────────┐
│                          SECURITY & PERMISSIONS                                  │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐       │
│  │                       Service Account                                │       │
│  │                                                                       │       │
│  │  Required Roles:                                                     │       │
│  │  • roles/storage.objectViewer      (GCS read access)                │       │
│  │  • roles/storage.objectCreator     (GCS write access)               │       │
│  │  • roles/datastore.user            (Firestore read/write)           │       │
│  │  • roles/run.admin                 (Cloud Run deployment)           │       │
│  └─────────────────────────────────────────────────────────────────────┘       │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐       │
│  │                       API Keys & Secrets                             │       │
│  │                                                                       │       │
│  │  • GEMINI_API_KEY: External API (Google AI Studio)                  │       │
│  │  • GCP credentials: Service account JSON or ADC                     │       │
│  │  • Environment variables (never committed to git)                   │       │
│  │  • Option: Google Secret Manager integration                        │       │
│  └─────────────────────────────────────────────────────────────────────┘       │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐       │
│  │                       Data Privacy                                   │       │
│  │                                                                       │       │
│  │  • Healthcare compliance (HIPAA, etc.)                              │       │
│  │  • Patient data encryption (in-transit & at-rest)                   │       │
│  │  • Audit logging enabled                                            │       │
│  │  • No client authentication (recommend adding for production)       │       │
│  └─────────────────────────────────────────────────────────────────────┘       │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────────┐
│                            ERROR HANDLING & RESILIENCE                           │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  • GCS Client: Blob existence checks, size validation, format validation        │
│  • Gemini Client: Fallback models, safety filter handling, JSON parsing         │
│  • Firestore Client: Exception handling, timestamp management                   │
│  • App Layer: Progress tracking, error display, partial success handling        │
│  • Logging: Comprehensive logging at INFO/WARNING/ERROR levels                  │
│  • User Feedback: Real-time progress bars, status messages, error details       │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────────┐
│                              TECHNOLOGY STACK                                    │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Frontend:     Streamlit 1.28+ (Python web framework)                           │
│  Backend:      Python 3.11+                                                      │
│  AI/ML:        Google Gemini Pro Vision API                                      │
│  Storage:      Google Cloud Storage                                              │
│  Database:     Cloud Firestore (NoSQL)                                           │
│  Image Proc:   PIL/Pillow                                                        │
│  Cloud:        Google Cloud Platform                                             │
│  Container:    Docker                                                            │
│  CI/CD:        Cloud Build                                                       │
│  Deploy:       Cloud Run (serverless)                                            │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘
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
