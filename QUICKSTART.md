# Quick Start Guide

Get CareLens 360 up and running in 5 minutes!

## Prerequisites Checklist

- [ ] Python 3.11+ installed
- [ ] Google Cloud Project created
- [ ] GCS bucket with patient folders
- [ ] Gemini API key
- [ ] Google Cloud credentials configured

## Step 1: Install Dependencies

### Windows
```bash
setup.bat
```

### Linux/Mac
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Step 2: Configure Environment

1. Copy the example environment file:
   ```bash
   cp env.example .env
   ```

2. Edit `.env` and add your credentials:
   ```env
   GCP_PROJECT_ID=your-actual-project-id
   GCS_BUCKET_NAME=your-actual-bucket-name
   GEMINI_API_KEY=your-actual-api-key
   ```

## Step 3: Set Up Google Cloud Authentication

```bash
gcloud auth application-default login
```

Or set the service account:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account.json"
```

## Step 4: Run the Application

```bash
streamlit run src/app.py
```

The app will open at `http://localhost:8501`

## Step 5: Test the Application

1. **Scan & Analyze a Patient**  
   - Select a patient from the dropdown (each corresponds to a folder in your GCS bucket)  
   - Click **"🔍 Scan and Analyze"**  
   - Wait for processing to complete – you’ll see:
     - A success banner
     - Metrics (Total Images / Processed / Failed)
     - An **Overview** section
     - **File‑wise Analysis** (one expander per image/report)
     - A **Final Combined Report** with prescriptions, exercise, dietary and general recommendations

2. **Ask Questions About the Report**  
   - Scroll to **"💬 Ask Questions About This Report"**  
   - Ask questions like:
     - "What are the main clinical concerns for this patient?"
     - "Summarize the key lab abnormalities."
     - "What dietary changes are recommended?"  
   - Click **"🔍 Get Answer"** to get an AI‑powered response based only on the patient’s reports

## Troubleshooting

### "Bucket not found"
- Verify `GCS_BUCKET_NAME` in `.env`
- Check bucket exists: `gsutil ls gs://your-bucket-name`

### "Permission denied"
- Run: `gcloud auth application-default login`
- Check service account has required roles

### "API key invalid"
- Verify `GEMINI_API_KEY` in `.env`
- Get new key from: https://makersuite.google.com/app/apikey

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Deploy to Cloud Run using [deploy.sh](deploy.sh) or [cloudbuild.yaml](cloudbuild.yaml)

