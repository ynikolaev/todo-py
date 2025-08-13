# Garage Payment Tracker

This project automates **garage rental payment tracking** and generates **overdue notifications**.  
It consists of two services running via **Docker Compose**:

1. **garage-backend** - FastAPI service for:

- Fetching garage payment data from Google Sheets
- Parsing Sberbank statements
- Calculating payment statuses (Received / Overdue / Pending)
- Generating XLSX reports

2. **garage-ui** - React-based frontend for:

- Triggering payment checks
- Displaying payment statuses
- Downloading XLSX reports

---

## Prerequisites

- **Docker** >= 20.10
- **Docker Compose** >= 1.29
- **Make** utility installed
- Google Sheets API credentials for accessing the rental table
- Sberbank statement file (CSV, XLSX, or PDF)

---

## How to Run in Development

1. Start all services in detached mode using **Makefile**:

```
make run
```

This will execute:

```
docker-compose up -d
```

2. Access the services:

- **Backend API:** http://localhost:8000
- **Frontend UI:** http://localhost:3000

3. To stop the services:

```
docker-compose down
```

---

## Backend API Overview

**Base URL:** `http://localhost:8000`

Example endpoints:

- `GET /` - Health check
- `GET /payments/status` - Placeholder endpoint for payment status check

The backend will later provide endpoints for:

- Uploading Sberbank statements
- Checking garage payment statuses
- Generating XLSX reports

---

## Environment Variables

`garage-backend` requires a Google API credential file for Sheets access:

```
GOOGLE_CREDENTIALS=/app/credentials.json
```

---

## Development Notes

- **Hot reload** is enabled for both backend (via `uvicorn --reload`) and frontend (`npm start`).
- To add new garages or payment sums, update the Google Sheet. The backend will fetch the latest data on each request.
- The system is designed to handle:
- Changing garage count
- Different Sberbank statement formats
- End-of-month date adjustments

---

## Next Steps

- Implement full XLSX report generation
- Integrate Google Sheets API to fetch real data
- Add file upload support for Sberbank statements
- Display statuses in the frontend
- Add Telegram or email notifications for overdue payments
