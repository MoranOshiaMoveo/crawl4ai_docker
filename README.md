# Crawl4AI Screenshot Service

A FastAPI-based web service that takes screenshots of web pages and uploads them to Google Cloud Storage.

## Features

- 📸 **Website Screenshots**: Capture full-page or viewport screenshots
- ☁️ **GCS Integration**: Automatic upload to Google Cloud Storage
- 🔐 **Signed URLs**: Secure temporary access to screenshots
- 🚀 **FastAPI**: Modern, fast web API with automatic documentation
- 🐳 **Docker Support**: Containerized for easy deployment

## API Endpoints

- `GET /` - Service status
- `GET /health` - Health check
- `POST /screenshot` - Take screenshot and upload to GCS

## Prerequisites

- Docker and Docker Compose
- Google Cloud Service Account JSON file (`service-account.json`)
- Google Cloud Storage bucket

## Quick Start with Docker

### 1. Build and Run with Docker Compose

```bash
# Build and start the service
docker-compose up --build

# Run in background
docker-compose up -d --build
```

### 2. Build and Run with Docker

```bash
# Build the image
docker build -t crawl4ai-screenshot .

# Run the container
docker run -p 8000:8000 \
  --security-opt seccomp:unconfined \
  -v /dev/shm:/dev/shm \
  crawl4ai-screenshot
```

### 3. Test the API

```bash
# Health check
curl http://localhost:8000/health

# Take a screenshot
curl -X POST "http://localhost:8000/screenshot" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "screenshot_wait_for": 20,
    "full_page": true
  }'
```

## API Documentation

Once running, visit:

- **Interactive API docs**: http://localhost:8000/docs
- **Alternative docs**: http://localhost:8000/redoc

## Configuration

### Environment Variables

- `GOOGLE_APPLICATION_CREDENTIALS` - Path to service account JSON
- `PYTHONUNBUFFERED` - Enable Python output buffering

### Request Parameters

```json
{
  "url": "https://example.com", // Required: URL to screenshot
  "screenshot_wait_for": 30, // Optional: Wait time in seconds (default: 30)
  "full_page": true, // Optional: Full page screenshot (default: true)
  "wait_for_images": true // Optional: Wait for images to load (default: true)
}
```

### Response Format

```json
{
  "success": true,
  "url": "https://storage.googleapis.com/...", // Signed URL (1 hour expiry)
  "file_size": 45632,
  "error_message": null
}
```

## Development

### Local Development (without Docker)

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Run the service:
   ```bash
   python app.py
   ```

### Development with Docker

1. Uncomment volume mounts in `docker-compose.yml`
2. Run with live reload:
   ```bash
   docker-compose up --build
   ```

## Production Deployment

### Google Cloud Run

1. Build and push to Container Registry:

   ```bash
   docker build -t gcr.io/PROJECT_ID/crawl4ai-screenshot .
   docker push gcr.io/PROJECT_ID/crawl4ai-screenshot
   ```

2. Deploy to Cloud Run:
   ```bash
   gcloud run deploy crawl4ai-screenshot \
     --image gcr.io/PROJECT_ID/crawl4ai-screenshot \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --memory 2Gi \
     --cpu 1
   ```

### Other Platforms

- **AWS ECS/Fargate**: Use the Docker image with appropriate task definitions
- **Kubernetes**: Create deployment and service manifests
- **Digital Ocean App Platform**: Deploy from Docker Hub or registry

## Troubleshooting

### Chrome Issues in Container

- Ensure `--security-opt seccomp:unconfined` is set
- Mount `/dev/shm` for shared memory
- Increase memory limits if screenshots fail

### GCS Authentication Issues

- Verify `service-account.json` is included in the container
- Check service account permissions for the GCS bucket
- Ensure `GOOGLE_APPLICATION_CREDENTIALS` environment variable is set

### Memory Issues

- Increase Docker memory limits
- Monitor resource usage with `docker stats`
- Consider reducing `screenshot_wait_for` values

## Security Notes

- Service account JSON contains sensitive credentials
- Use secrets management in production
- Signed URLs expire after 1 hour
- Consider implementing rate limiting for production use

## License

MIT License
