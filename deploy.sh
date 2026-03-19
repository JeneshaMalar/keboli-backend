#!/bin/bash

PROJECT_ID="gwx-internship-01"
REGION="us-east1"
SERVICE_NAME="keboli-backend"
GAR_REPO="us-east1-docker.pkg.dev/$PROJECT_ID/gwx-gar-intern-01"
IMAGE="$GAR_REPO/backend:latest"

DB_USER="jeneshas"
DB_PASS="8S3qfVy7A6t6QfzM%23tD"
DB_NAME="keboli"
DB_HOST="34.23.138.181"
CONN_NAME="gwx-internship-01:us-east1:gwx-csql-intern-01"
DB_URL="postgresql+asyncpg://$DB_USER:$DB_PASS@/$DB_NAME?host=/cloudsql/$CONN_NAME"

echo "Fetching Agent URLs..."
INTERVIEW_URL=$(gcloud run services describe keboli-interview-agent --region=$REGION --format='value(status.url)' --project=$PROJECT_ID)
EVALUATION_URL=$(gcloud run services describe evaluation-agent --region=$REGION --format='value(status.url)' --project=$PROJECT_ID)
FRONTEND_URL=$(gcloud run services describe keboli-frontend --region=$REGION --format='value(status.url)' --project=$PROJECT_ID)

echo "Interview Agent URL: $INTERVIEW_URL"
echo "Evaluation Agent URL: $EVALUATION_URL"
echo "Frontend URL: $FRONTEND_URL"
# echo "Running DB migrations..."
# export DATABASE_URL=$DB_URL
# uv sync
# uv run python -m alembic upgrade head


echo "Building Backend..."
docker build -t $IMAGE .
docker push $IMAGE

echo "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image=$IMAGE \
  --region=$REGION \
  --allow-unauthenticated \
  --project=$PROJECT_ID \
  --platform=managed \
  --port=8000 \
  --max-instances=2 \
  --min-instances=0 \
  --min=0 \
  --max=2 \
  --service-account gwx-cloudrun-sa-01@gwx-internship-01.iam.gserviceaccount.com \
  --add-cloudsql-instances gwx-internship-01:us-east1:gwx-csql-intern-01 \
  --set-env-vars="DATABASE_URL=$DB_URL,FRONTEND_URL=$FRONTEND_URL,INTERVIEW_AGENT_URL=$INTERVIEW_URL,EVALUATION_SERVICE_URL=$EVALUATION_URL,DB_HOST=$DB_HOST,DB_USER=$DB_USER,DB_PASSWORD=$DB_PASS,DB_NAME=$DB_NAME"
  
# echo "Backend is live!"