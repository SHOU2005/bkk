# FinSight AI - Quick Start Guide

## Prerequisites

- Python 3.11+
- Node.js 18+
- npm or yarn

## Installation & Running

### 1. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Backend will run on: http://localhost:8000

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend will run on: http://localhost:5173

### 3. Using Docker (Alternative)

```bash
docker-compose up --build
```

## Usage

1. Open http://localhost:5173 in your browser
2. Click "Launch Fraud Analysis Tool"
3. Upload a PDF bank statement
4. Wait for analysis (usually takes a few seconds)
5. View results with fraud flags, categories, and download PDF report

## API Endpoints

- `GET /` - API info
- `GET /health` - Health check
- `POST /api/analyze` - Upload PDF and analyze (multipart/form-data)

## Notes

- Only PDF files are supported
- PDF should contain readable bank statement data
- Analysis includes fraud detection, categorization, and risk scoring
- Results include QR code for sharing
- PDF reports can be downloaded

## Troubleshooting

**Backend won't start:**
- Check Python version: `python --version` (should be 3.11+)
- Install dependencies: `pip install -r requirements.txt`
- Check port 8000 is available

**Frontend won't start:**
- Check Node version: `node --version` (should be 18+)
- Install dependencies: `npm install`
- Check port 5173 is available

**PDF upload fails:**
- Ensure PDF is not corrupted
- PDF should contain text (not just images)
- Check backend is running
- Verify CORS is configured

**No transactions extracted:**
- PDF format might not be recognized
- Ensure PDF contains standard bank statement format
- Check backend logs for extraction errors

