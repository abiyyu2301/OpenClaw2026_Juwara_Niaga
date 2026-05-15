# Deploy Niaga to Cloud Run (project niaga-496405)
# Usage: .\scripts\deploy-gcp.ps1

$ErrorActionPreference = "Stop"
$Project = "niaga-496405"
$Region = "asia-southeast2"
$Service = "niaga"
$Bucket = "niaga-496405-assets"
$Sa = "niaga-backend@niaga-496405.iam.gserviceaccount.com"

Write-Host "Enabling APIs (Maps, Places, Storage)..."
gcloud services enable `
  maps-backend.googleapis.com `
  places-backend.googleapis.com `
  geocoding-backend.googleapis.com `
  storage.googleapis.com `
  --project=$Project

if (-not (gcloud storage buckets describe "gs://$Bucket" --project=$Project 2>$null)) {
  Write-Host "Creating GCS bucket gs://$Bucket ..."
  gcloud storage buckets create "gs://$Bucket" --location=$Region --project=$Project --uniform-bucket-level-access
  gcloud storage buckets add-iam-policy-binding "gs://$Bucket" `
    --member=allUsers --role=roles/storage.objectViewer --project=$Project
}

Write-Host "Granting storage access to service account..."
gcloud projects add-iam-policy-binding $Project `
  --member="serviceAccount:$Sa" `
  --role=roles/storage.objectAdmin `
  --quiet | Out-Null

$MapsKey = $env:GOOGLE_MAPS_API_KEY
if (-not $MapsKey) {
  Write-Host "WARN: GOOGLE_MAPS_API_KEY not set — Maps autocomplete will use manual geography only."
}

$EnvVars = "GCS_BUCKET=$Bucket,PAYMENT_PROVIDER=mock"
if ($MapsKey) { $EnvVars += ",GOOGLE_MAPS_API_KEY=$MapsKey" }

Write-Host "Deploying to Cloud Run..."
gcloud run deploy $Service `
  --source . `
  --region $Region `
  --project $Project `
  --service-account $Sa `
  --allow-unauthenticated `
  --memory 1Gi `
  --timeout 600 `
  --max-instances 2 `
  --port 8080 `
  --set-env-vars $EnvVars `
  --quiet

Write-Host "Done. URL:"
gcloud run services describe $Service --region $Region --project $Project --format="value(status.url)"
