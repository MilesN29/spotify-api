# Spotify Flask Server Deployment Guide

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Health check |
| `GET /now-playing` | Currently playing track |
| `GET /recently-played` | Last 5 tracks played |
| `GET /top-artists` | Top 5 artists (last 4 weeks) |
| `GET /top-tracks` | Top 5 tracks (last 4 weeks) |
| `GET /all` | All data in one request |

---

## Run Locally (for testing)

```powershell
cd gcp-spotify-function

# install dependencies
pip install -r requirements.txt

# set environment variables
$env:SPOTIFY_CLIENT_ID="client_id"
$env:SPOTIFY_CLIENT_SECRET="client_secret"
$env:SPOTIFY_REFRESH_TOKEN="refresh_token"

# run the server
python main.py
```

Server will run at `http://localhost:5000`

---

## Deploy to GCP Cloud Run with Artifact Registry

### Prerequisites
1. Install [Google Cloud CLI](https://cloud.google.com/sdk/docs/install)
2. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/)
3. Have a GCP project with billing enabled

### Step 1: Authenticate with GCP

```powershell
gcloud auth login
gcloud config set project PROJECT_ID
```

### Step 2: Enable Required APIs

```powershell
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### Step 3: Create Artifact Registry Repository

```powershell
gcloud artifacts repositories create spotify-api `
  --repository-format=docker `
  --location=us-central1 `
  --description="Spotify API Docker images"
```

### Step 4: Configure Docker Authentication

```powershell
gcloud auth configure-docker us-central1-docker.pkg.dev
```

### Step 5: Build the Docker Image

```powershell
cd gcp-spotify-function

docker build -t us-central1-docker.pkg.dev/PROJECT_ID/spotify-api/spotify-flask:v1 .
```

### Step 6: Push to Artifact Registry

```powershell
docker push us-central1-docker.pkg.dev/PROJECT_ID/spotify-api/spotify-flask:v1
```

### Step 7: Deploy to Cloud Run

```powershell
gcloud run deploy spotify-api `
  --image us-central1-docker.pkg.dev/PROJECT_ID/spotify-api/spotify-flask:v1 `
  --region us-central1 `
  --platform managed `
  --allow-unauthenticated `
  --set-env-vars="SPOTIFY_CLIENT_ID=client_id,SPOTIFY_CLIENT_SECRET=client_secret,SPOTIFY_REFRESH_TOKEN=refresh_token"
```

### Step 8: Get The Service URL

After deployment, output like:
```
Service URL: https://spotify-api-xxxxxxxxxx-uc.a.run.app
```

---

## Updating Deployment

When making changes to `main.py`:

```powershell
# build new version
docker build -t us-central1-docker.pkg.dev/PROJECT_ID/spotify-api/spotify-flask:v2 .

# push new version
docker push us-central1-docker.pkg.dev/PROJECT_ID/spotify-api/spotify-flask:v2

# deploy new version
gcloud run deploy spotify-api `
  --image us-central1-docker.pkg.dev/PROJECT_ID/spotify-api/spotify-flask:v2 `
  --region us-central1
```

---

## Updating Environment Variables

If need to update the Spotify tokens:

```powershell
gcloud run services update spotify-api `
  --region us-central1 `
  --set-env-vars="SPOTIFY_CLIENT_ID=new_id,SPOTIFY_CLIENT_SECRET=new_secret,SPOTIFY_REFRESH_TOKEN=new_token"
```

---

## Test Deployment

Visit `SERVICE_URL/all` in a browser. Should see JSON like:

```json
{
  "currentlyPlaying": { "name": "Song", "artist": "Artist", ... },
  "recentlyPlayed": [...],
  "topArtists": [...],
  "topTracks": [...]
}
```

---

## Troubleshooting

### View Logs
```powershell
gcloud run logs read --service spotify-api --region us-central1
```

### Check Service Status
```powershell
gcloud run services describe spotify-api --region us-central1
```

### List Images in Artifact Registry
```powershell
gcloud artifacts docker images list us-central1-docker.pkg.dev/PROJECT_ID/spotify-api
```
