# FinSight AI - Deployment Guide

## Quick Start (Development)

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000 --host 0.0.0.0
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 3000
```

The application will be available at:
- **Frontend**: http://localhost:3000 or http://YOUR_IP:3000
- **Backend API**: http://localhost:8000 or http://YOUR_IP:8000

## Docker Deployment

### Using Docker Compose (Recommended)

#### Development Mode
```bash
# Build and start all services
docker-compose up --build

# Run in detached mode
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

#### Production Mode
```bash
# Build and start production services
docker-compose -f docker-compose.prod.yml up -d --build

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Stop services
docker-compose -f docker-compose.prod.yml down
```

### Using the Deployment Script

The easiest way to deploy for local network access:

#### Development Mode
```bash
# Make script executable
chmod +x deploy-local.sh

# Start services
./deploy-local.sh start

# View status
./deploy-local.sh status

# Stop services
./deploy-local.sh stop

# Show access URLs
./deploy-local.sh ip
```

#### Production Mode
```bash
# Start with production configuration
./deploy-local.sh start --prod

# Or using short flag
./deploy-local.sh start -p

# Stop production services
./deploy-local.sh stop --prod
```

### Individual Docker Builds

#### Backend
```bash
cd backend
docker build -t finsight-backend .
docker run -p 8000:8000 finsight-backend
```

#### Frontend (Development)
```bash
cd frontend
docker build -t finsight-frontend .
docker run -p 3000:3000 finsight-frontend
```

#### Frontend (Production)
```bash
cd frontend
docker build -f Dockerfile.prod -t finsight-frontend-prod .
docker run -p 3000:3000 finsight-frontend-prod
```

## Local Network Deployment

### Finding Your Local IP Address

**macOS:**
```bash
ipconfig getifaddr en0
# or
ipconfig getifaddr en1
```

**Linux:**
```bash
hostname -I
# or
ip addr show | grep "inet " | awk '{print $2}' | head -1
```

**Windows:**
```bash
ipconfig | findstr /i "IPv4 Address"
```

### Accessing from Other Devices

Once the application is running, other devices on your local network can access it at:

- **Frontend**: `http://YOUR_MACHINE_IP:3000`
- **Backend API**: `http://YOUR_MACHINE_IP:8000`
- **Health Check**: `http://YOUR_MACHINE_IP:8000/health`

Example:
```
Machine IP: 192.168.1.100

Access from another device:
Frontend: http://192.168.1.100:3000
API: http://192.168.1.100:8000/api/analyze
```

### Firewall Considerations

If other devices cannot connect, you may need to allow the ports:

**macOS:**
```bash
# Allow port 3000
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /path/to/node
# Or disable firewall temporarily (not recommended for production)
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --set globalstate off
```

**Linux (ufw):**
```bash
sudo ufw allow 3000
sudo ufw allow 8000
sudo ufw reload
```

**Windows:**
- Go to Windows Defender Firewall > Advanced Settings > Inbound Rules
- Add rules for ports 3000 and 8000

## Production Deployment

### Environment Variables

Create `.env` files in both backend and frontend directories:

**backend/.env:**
```
SECRET_KEY=your-strong-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ENCRYPTION_KEY=your-32-byte-encryption-key-base64
```

**frontend/.env:**
```
VITE_API_URL=https://your-api-domain.com
```

### Backend Production

1. Use a production WSGI server:
```bash
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

2. Or use uvicorn with production settings:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Frontend Production Build

```bash
cd frontend
npm run build
```

The production build will be in the `dist/` directory. Serve it with:
- Nginx
- Apache
- Any static file server
- Or use a CDN

### Nginx Configuration Example

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Cloud Deployment Options

### AWS
- **EC2**: Deploy backend and frontend on EC2 instances
- **Elastic Beanstalk**: Use for backend API
- **S3 + CloudFront**: Host frontend static files
- **ECS/Fargate**: Containerized deployment

### Google Cloud
- **Cloud Run**: Serverless containers
- **App Engine**: Managed platform
- **Compute Engine**: VM instances
- **Cloud Storage + CDN**: Static frontend hosting

### Azure
- **App Service**: Managed web apps
- **Container Instances**: Containerized deployment
- **Static Web Apps**: Frontend hosting
- **Virtual Machines**: Traditional VM deployment

### Heroku
```bash
# Backend
cd backend
heroku create finsight-backend
git push heroku main

# Frontend
cd frontend
heroku create finsight-frontend
heroku buildpacks:set heroku/nodejs
git push heroku main
```

## Security Checklist

- [ ] Change all default secret keys
- [ ] Use HTTPS in production
- [ ] Enable CORS only for trusted domains
- [ ] Implement rate limiting
- [ ] Set up authentication (JWT tokens)
- [ ] Enable encryption for data at rest
- [ ] Set up audit logging
- [ ] Regular security updates
- [ ] Use environment variables for sensitive data
- [ ] Enable firewall rules
- [ ] Regular backups

## Monitoring & Logging

- Set up application monitoring (e.g., Sentry, Datadog)
- Enable structured logging
- Set up health check endpoints
- Monitor API response times
- Track error rates
- Set up alerts for critical issues

## Scaling Considerations

- Use load balancers for multiple backend instances
- Implement database for storing analysis results
- Use Redis for caching
- Consider message queues for async processing
- Set up CDN for frontend assets
- Implement horizontal scaling for ML models

## Troubleshooting

### Backend Issues
- Check Python version (3.11+)
- Verify all dependencies are installed
- Check port 8000 is not in use
- Review logs for errors
- Verify environment variables

### Frontend Issues
- Clear node_modules and reinstall
- Check Node.js version (18+)
- Verify API URL is correct
- Check browser console for errors
- Ensure CORS is configured correctly

### PDF Processing Issues
- Verify PDF is not corrupted
- Check PDF contains readable text (not just images)
- Ensure PDF structure is standard bank statement format
- Review OCR/extraction logs

