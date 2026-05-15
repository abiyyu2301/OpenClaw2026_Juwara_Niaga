# Deploy Niaga to Cloud Run (project niaga-496405)
# Usage: .\scripts\deploy-gcp.ps1
# Requires: committed + pushed main.
# Optional shell env before deploy: GOOGLE_MAPS_API_KEY, GMAIL_ADDRESS, GMAIL_APP_PASSWORD
# Existing Cloud Run env vars are preserved; shell env overrides win.

$ErrorActionPreference = "Stop"

$Project = "niaga-496405"
$Region = "asia-southeast2"
$Service = "niaga"
$Bucket = "niaga-496405-assets"
$Sa = "niaga-backend@niaga-496405.iam.gserviceaccount.com"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $RepoRoot
try {
  $dirty = git status --porcelain
  if ($dirty) {
    throw "Uncommitted changes. Commit and push to GitHub before deploying."
  }
  git fetch origin main 2>$null | Out-Null
  $ahead = [int](git rev-list --count origin/main..HEAD 2>$null)
  if ($ahead -gt 0) {
    Write-Host "Pushing $ahead commit(s) to origin/main..."
    git push origin main
  }

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

  # Preserve env already on Cloud Run (Gmail, Maps, etc.)
  $pairs = @{}
  $existing = gcloud run services describe $Service `
    --region $Region --project $Project --format=json 2>$null
  if ($existing) {
    $doc = $existing | ConvertFrom-Json
    foreach ($e in $doc.spec.template.spec.containers[0].env) {
      if ($null -ne $e.value) {
        $pairs[$e.name] = [string]$e.value
      }
    }
  }

  $pairs["GCS_BUCKET"] = $Bucket
  # Default to mock only if nothing is set — preserve an existing `doku`
  # (or other) setting across deploys.
  if (-not $pairs.ContainsKey("PAYMENT_PROVIDER")) {
    $pairs["PAYMENT_PROVIDER"] = "mock"
  }

  if ($env:GOOGLE_MAPS_API_KEY) {
    $pairs["GOOGLE_MAPS_API_KEY"] = $env:GOOGLE_MAPS_API_KEY
  } elseif (-not $pairs.ContainsKey("GOOGLE_MAPS_API_KEY")) {
    Write-Host "WARN: GOOGLE_MAPS_API_KEY not set - Maps autocomplete uses manual geography only."
  }

  if ($env:GMAIL_ADDRESS) { $pairs["GMAIL_ADDRESS"] = $env:GMAIL_ADDRESS }
  if ($env:GMAIL_APP_PASSWORD) { $pairs["GMAIL_APP_PASSWORD"] = $env:GMAIL_APP_PASSWORD }
  if (($env:GMAIL_ADDRESS -or $env:GMAIL_APP_PASSWORD) -and -not ($env:GMAIL_ADDRESS -and $env:GMAIL_APP_PASSWORD)) {
    Write-Host "WARN: Set both GMAIL_ADDRESS and GMAIL_APP_PASSWORD in shell to override email creds."
  }

  $envLine = ($pairs.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value)" }) -join ","
  Write-Host "Deploying to Cloud Run (env keys: $($pairs.Keys -join ', '))..."

  gcloud run deploy $Service `
    --source . `
    --region $Region `
    --project $Project `
    --service-account $Sa `
    --allow-unauthenticated `
    --memory 1Gi `
    --timeout 600 `
    --min-instances 1 `
    --max-instances 2 `
    --port 8080 `
    --set-env-vars $envLine `
    --quiet

  Write-Host "Done. URL:"
  gcloud run services describe $Service --region $Region --project $Project --format='value(status.url)'
}
finally {
  Pop-Location
}
