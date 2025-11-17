# Project Structure

```
CareLens-360/
│
├── src/                          # Source code directory
│   ├── __init__.py              # Package initialization
│   ├── config.py                # Configuration management
│   ├── gcs_client.py            # Google Cloud Storage client
│   ├── gemini_client.py        # Gemini Pro Vision API client
│   ├── firestore_client.py     # Firestore database client
│   └── app.py                   # Main Streamlit application
│
├── tests/                       # Test directory
│   ├── __init__.py
│   └── test_config.py          # Configuration tests
│
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Docker container configuration
├── cloudbuild.yaml             # Google Cloud Build configuration
├── deploy.sh                   # Deployment script (Linux/Mac)
├── setup.bat                   # Setup script (Windows)
├── run_local.py                # Local development runner
│
├── .env.example                # Environment variables template
├── .gitignore                  # Git ignore rules
├── .dockerignore              # Docker ignore rules
│
├── README.md                   # Main documentation
├── QUICKSTART.md              # Quick start guide
└── PROJECT_STRUCTURE.md        # This file
```

## Module Descriptions

### `src/config.py`
- Manages all configuration settings
- Loads environment variables
- Validates required configuration
- Provides default values

### `src/gcs_client.py`
- Handles Google Cloud Storage operations
- Lists patient folders
- Lists images for a patient
- Downloads images from GCS
- Retrieves image metadata

### `src/gemini_client.py`
- Integrates with Gemini Pro Vision API
- Generates clinical summaries from medical images
- Extracts measurements, abnormalities, and recommendations
- Handles API errors gracefully

### `src/firestore_client.py`
- Manages Firestore database operations
- Saves clinical summaries
- Retrieves patient summaries
- Performs natural language search
- Handles query parsing and matching

### `src/app.py`
- Main Streamlit application
- Three main features:
  1. Scan Patient - Process all images for a patient
  2. Query Patient - Retrieve summaries for a patient
  3. Natural Language Search - Search across all summaries

## Data Flow

```
GCS Bucket (Patient Folders)
    ↓
GCS Client (Download Images)
    ↓
Gemini Client (Generate Summaries)
    ↓
Firestore Client (Store Summaries)
    ↓
Streamlit UI (Display & Query)
```

## Key Features

1. **Modular Design**: Each component is separated into its own module
2. **Error Handling**: Comprehensive error handling throughout
3. **Logging**: Structured logging for debugging
4. **Configuration**: Centralized configuration management
5. **Production Ready**: Docker support, Cloud Run deployment ready
6. **Documentation**: Comprehensive README and inline comments

