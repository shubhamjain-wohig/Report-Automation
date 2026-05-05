# Report Automation Tool

A Google ADK-based multi-agent system that extracts Scope of Work (SOW) data from PDF, DOCX, or text files and automatically generates weekly project status reports with:
- Task Tracker spreadsheet
- Gantt/Timeline chart visualization
- Google Sheets export

## Project Structure

```
/Users/shubhamjain/Documents/Report Automation Tool/
├── main.py                    # Backend server (FastAPI + ADK runner)
├── requirements.txt           # Python dependencies
├── .env                       # API keys and configuration
├── agent.md                  # Agent context/reference
├── frontend/                  # Drag-and-drop web UI
│   ├── index.html
│   ├── app.js
│   └── styles.css
├── Report_generator/          # Core report generation logic
│   └── agent.py              # Main agent with Gantt chart rendering
└── sow_report_agent/          # SOW parsing agents
    └── agent.py              # Legacy SOW parser
```

## How It Works

### 1. File Upload
- User drops a SOW file (PDF, DOCX, or TXT) onto the frontend or drags it to the upload zone
- File is sent to the backend via `/upload` endpoint

### 2. Processing Pipeline
The backend processes the file through multiple agents:

1. **SOWParserAgent** - Extracts structured data from the SOW document
2. **PlannerAgent** - Organizes tasks, phases, and timelines
3. **ExcelBuilderAgent** - Generates the Excel workbook with:
   - Task Tracker sheet with tasks, status, dates, owners
   - Timeline sheet for Gantt chart generation
4. **ReportSummaryAgent** - Creates a natural language summary

### 3. Output
- Excel file with Task Tracker + Gantt chart
- Google Sheets link (auto-published to Drive)
- Local download link

## Key Files

| File | Purpose |
|------|---------|
| `main.py` | FastAPI server, handles upload/processing endpoints |
| `Report_generator/agent.py` | Generates Excel files + Gantt chart images |
| `frontend/app.js` | Frontend JavaScript for drag-drop upload |
| `frontend/index.html` | Frontend HTML with styled upload UI |

## Dependencies

Key packages from `requirements.txt`:
- `google-adk` - Google's Agent Development Kit
- `openpyxl` - Excel file generation
- `matplotlib` - Gantt chart rendering
- `pypdf` / `python-docx` - PDF/DOCX parsing
- `google-auth` / `google-api-python-client` - Google Sheets API
- `fastapi` / `uvicorn` - Backend server

## Setup

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure API keys in .env
# GOOGLE_API_KEY=your_key_here
# GOOGLE_OAUTH_CLIENT_SECRET_JSON=./client_secret.json
# GOOGLE_OAUTH_TOKEN_JSON=./google_oauth_token.json
```

## Running the Application

### Option 1: Backend Only (API)
```bash
python main.py
```
Backend runs at `http://localhost:8000`

### Option 2: Full Stack (Backend + Frontend)
```bash
# Terminal 1: Backend
python main.py

# Terminal 2: Frontend
cd frontend
python3 -m http.server 3000
```
Open `http://localhost:3000` in browser

### Option 3: ADK Web UI (Legacy)
```bash
adk web
```

## Configuration (.env)

| Variable | Description |
|----------|-------------|
| `GOOGLE_API_KEY` | Gemini API key |
| `GOOGLE_OAUTH_CLIENT_SECRET_JSON` | OAuth client secret |
| `GOOGLE_OAUTH_TOKEN_JSON` | OAuth token |
| `GOOGLE_SHEETS_CREDENTIALS_JSON` | Service account (optional) |

## Gantt Chart

The Gantt chart is rendered in `Report_generator/agent.py`:
- `_render_gantt_chart()` function creates the timeline visualization
- Title fontsize: 17 (configurable at line 1459)
- Bar label fontsize: 8 (line 1452)
- Chart stretches to fill the timeline placeholder shape in Google Slides

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/upload` | POST | Upload SOW file |
| `/process` | POST | Process uploaded file |
| `/list` | GET | List generated reports |
| `/download` | GET | Download report file |