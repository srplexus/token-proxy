# Token Vendor

## Configuration

```shell
echo -n 'user:password' | gcloud secrets create PROXY_BASIC_AUTH --data-file=-
echo -n '1.2.3.4,5.6.7.8' | gcloud secrets create PROXY_TRUSTED_IPS --data-file=-
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