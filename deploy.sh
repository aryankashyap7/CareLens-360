#!/bin/bash
# Deployment script for CareLens 360 to Google Cloud Run

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Deploying CareLens 360 to Cloud Run...${NC}"

# Check if required environment variables are set
if [ -z "$GCP_PROJECT_ID" ]; then
    echo -e "${RED}❌ Error: GCP_PROJECT_ID environment variable is not set${NC}"
    exit 1
fi

if [ -z "$GCS_BUCKET_NAME" ]; then
    echo -e "${RED}❌ Error: GCS_BUCKET_NAME environment variable is not set${NC}"
    exit 1
fi

if [ -z "$GEMINI_API_KEY" ]; then
    echo -e "${RED}❌ Error: GEMINI_API_KEY environment variable is not set${NC}"
    exit 1
fi

# Set default values
REGION=${REGION:-us-central1}
SERVICE_NAME=${SERVICE_NAME:-carelens-360}
IMAGE_NAME="gcr.io/${GCP_PROJECT_ID}/${SERVICE_NAME}:latest"
FIRESTORE_COLLECTION=${FIRESTORE_COLLECTION:-clinical_summaries}

echo -e "${YELLOW}📦 Building Docker image...${NC}"
docker build -t "${IMAGE_NAME}" .

echo -e "${YELLOW}📤 Pushing image to Google Container Registry...${NC}"
docker push "${IMAGE_NAME}"

echo -e "${YELLOW}🚀 Deploying to Cloud Run...${NC}"
gcloud run deploy "${SERVICE_NAME}" \
    --image "${IMAGE_NAME}" \
    --platform managed \
    --region "${REGION}" \
    --allow-unauthenticated \
    --set-env-vars "GCP_PROJECT_ID=${GCP_PROJECT_ID},GCS_BUCKET_NAME=${GCS_BUCKET_NAME},GEMINI_API_KEY=${GEMINI_API_KEY},FIRESTORE_COLLECTION=${FIRESTORE_COLLECTION}" \
    --memory 2Gi \
    --cpu 2 \
    --timeout 3600 \
    --max-instances 10

echo -e "${GREEN}✅ Deployment complete!${NC}"
echo -e "${GREEN}🌐 Your app is now running on Cloud Run${NC}"

