# Local Network Deployment Plan for AcuTrace

## Objective
Deploy AcuTrace application for access from other devices on the local network

## Tasks

### 1. Update docker-compose.yml
 services to listen on 0.0.- [ ] Configure0.0
- [ ] Add proper network configuration
- [ ] Configure restart policies
- [ ] Add health checks for reliability

### 2. Create Production Frontend Dockerfile with Nginx
- [ ] Create Dockerfile.prod for frontend
- [ ] Configure Nginx for production serving
- [ ] Set up proper API proxy configuration

### 3. Update Backend Configuration
- [ ] Update CORS for local network access
- [ ] Configure environment variables
- [ ] Add production-ready settings

### 4. Create Deployment Scripts
- [ ] Create deploy-local.sh script
- [ ] Create stop-services.sh script
- [ ] Add network IP detection helper

### 5. Update Documentation
- [ ] Update DEPLOYMENT.md with local network instructions
- [ ] Add troubleshooting section for network issues

## Deployment Steps

### Option 1: Docker Compose (Recommended)
```bash
# Start services
docker-compose up -d --build

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Option 2: Manual Deployment
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000

# Frontend (in another terminal)
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

## Access URLs
- Frontend: http://YOUR_IP:3000
- Backend API: http://YOUR_IP:8000
- API Health: http://YOUR_IP:8000/health

## Finding Your Local IP
```bash
# macOS
ipconfig getifaddr en0

# Linux
hostname -I

# Windows
ipconfig
```

## Troubleshooting
- Port already in use: Change ports in docker-compose.yml
- Connection refused: Check firewall settings
- CORS errors: Verify CORS configuration in backend
- Slow performance: Use production build instead of dev mode

