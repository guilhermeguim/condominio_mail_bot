# Operations & Deployment Manual

This manual covers container management, production cloud provisioning, and continuous maintenance playbooks for Google Cloud Run.

## 1. Local Containerization (Testing the Docker Package)
Before shipping versions to production, you can test the application inside a localized container to simulate cloud behavior.

### Step A: Building the Image
Run the build command at the application root level to process the Dockerfile ruleset:
```bash
docker build -t mail-bot-app .
```

### Step B: Initializing Local Container Instances
Boot the container while securely injecting your local `.env` configurations:
```bash
docker run --rm -p 8080:8080 --env-file .env mail-bot-app
```
Confirm the console states reflect stable instances initialized on port 8080. You can re-route your Ngrok tunnel to point to port 8080 to test the container end-to-end.

## 2. Infrastructure Setup (GCP Initial Provisioning)
Execute this sequence when preparing a brand new environment or setting up a clean GCP project from scratch.

### Authentication and Project Setup
Log into your Google Cloud CLI context:
```bash
gcloud init
```
Generate an isolated infrastructure project and set it as active (replace with a unique project ID):
```bash
gcloud projects create condominio-mail-bot-prod --name="Condominio Mail Bot"
gcloud config set project condominio-mail-bot-prod
```

### Enable APIs and Provision Registry
Enable essential serverless and image management APIs:
```bash
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com
```
Create an isolated Artifact Registry workspace repository to store your Docker images:
```bash
gcloud artifacts repositories create mail-bot-repo \
    --repository-format=docker \
    --location=us-central1 \
    --description="Production Registry"
```
Configure local Docker authentication to allow pushing to Google Cloud:
```bash
gcloud auth configure-docker us-central1-docker.pkg.dev
```

### Initial Production Deploy
The first deployment requires injecting the environment variables into Cloud Run. Tag, push, and deploy:
```bash
docker tag mail-bot-app us-central1-docker.pkg.dev/condominio-mail-bot-prod/mail-bot-repo/mail-bot-app:latest
docker push us-central1-docker.pkg.dev/condominio-mail-bot-prod/mail-bot-repo/mail-bot-app:latest

gcloud run deploy mail-bot-service \
  --image=us-central1-docker.pkg.dev/condominio-mail-bot-prod/mail-bot-repo/mail-bot-app:latest \
  --region=us-central1 \
  --allow-unauthenticated \
  --set-env-vars="TELEGRAM_BOT_TOKEN=YOUR_TOKEN,MICROSOFT_CLIENT_ID=YOUR_ID,MICROSOFT_TENANT_ID=consumers,MICROSOFT_REFRESH_TOKEN=YOUR_REFRESH"
```
Once the command finishes, it will return a secure Service URL. You must register this URL in Telegram to point the live webhook to production:
```text
[https://api.telegram.org/bot](https://api.telegram.org/bot)<YOUR_TELEGRAM_TOKEN>/setWebhook?url=<YOUR_CLOUD_RUN_URL>/webhook
```

## 3. Shipping Code Updates (Maintenance Lifecycle)
Whenever you modify the source code (e.g., changing the email text, adjusting internal validation structures) and want to deploy the update to production, execute these three commands sequentially in your terminal:

### Step A: Rebuild the Container
Recompile the application package locally to incorporate your recent code modifications:
```bash
docker build -t mail-bot-app .
```

### Step B: Push the New Version to the Registry
Update the image tracking pointer and upload the revised package to the Artifact Registry vault:
```bash
docker tag mail-bot-app us-central1-docker.pkg.dev/condominio-mail-bot-prod/mail-bot-repo/mail-bot-app:latest
docker push us-central1-docker.pkg.dev/condominio-mail-bot-prod/mail-bot-repo/mail-bot-app:latest
```

### Step C: Trigger the Cloud Run Update
Command Cloud Run to fetch the new image tag and perform a zero-downtime service restart:
```bash
gcloud run deploy mail-bot-service \
  --image=us-central1-docker.pkg.dev/condominio-mail-bot-prod/mail-bot-repo/mail-bot-app:latest \
  --region=us-central1
```
Note: You do not need to re-pass the configuration variables (`--set-env-vars`). Cloud Run stores these parameters safely and automatically reuses them across new image deployments unless explicitly instructed to overwrite them.