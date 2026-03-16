# Token Vending Machine

## Initial configuration

This application exchanges a simple username/password for a real Google OAuth 2.0 Access Token, while keeping your infrastructure secure and hidden from the public.

### Phase 1: Identity & Security Setup (The Foundation)
Create a Service Account and two Secrets. This ensures that even if someone sees this code, they don't have the credentials or know which systems are trusted.

The `PROXY_BASIC_AUTH` secret is a full credential in the form `user:password`. **Do not share this credential** with any other application or system.
The `PROXY_TRUSTED_IPS` secret is a comma-separated list of IP addresses and/or CIDR blocks. **Access must be limited** to internal networks.

Modify the defaults in step 1 below to match your specific circumstances.

Run the following commands in Google Cloud Console:

```shell
# 1. Configuration variables
PROJECT_ID=$(gcloud config get-value project)
REGION="us-central1"
SA_NAME="token-vending-sa"
SA_EMAIL="$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com"
PROXY_BASIC_AUTH="user:password"
PROXY_TRUSTED_IPS="1.2.3.4,5.6.7.0/24"

# 2. Enable APIs
gcloud services enable aiplatform.googleapis.com \
    run.googleapis.com \
    secretmanager.googleapis.com

# 3. Create the Service Account (The Proxy's Identity)
gcloud iam service-accounts create $SA_NAME \
    --display-name="Token Vending Proxy"

# 4. Grant Permissions
# This allows the proxy to generate tokens for Vertex AI
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/aiplatform.user"

# 5. Create the basic auth and trusted IP secrets in Secret Manager
echo -n "$PROXY_BASIC_AUTH" | gcloud secrets create PROXY_BASIC_AUTH --data-file=-
echo -n "$PROXY_TRUSTED_IPS" | gcloud secrets create PROXY_TRUSTED_IPS --data-file=-

# 6. Allow the Proxy to read the basic auth and trusted IP secrets
gcloud secrets add-iam-policy-binding PROXY_BASIC_AUTH \
  --member="serviceAccount:$SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
gcloud secrets add-iam-policy-binding PROXY_TRUSTED_IPS \
  --member="serviceAccount:$SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

## Deployment

```shell
gcloud run deploy token-vending-machine \
    --source app/ \
    --region $REGION \
    --service-account $SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com \
    --set-secrets "PROXY_BASIC_AUTH=PROXY_BASIC_AUTH:latest" \
    --set-secrets "PROXY_TRUSTED_IPS=PROXY_TRUSTED_IPS:latest" \
    --allow-unauthenticated
```
