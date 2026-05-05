# SOW Report Agent

**Location:** `/Users/shubhamjain/Documents/Report Automation Tool/sow_report_agent/agent.py`

## Overview

The SOW Report Agent is a Phase 1 component that processes Scope of Work (SOW) documents (PDF, DOCX, Excel, or text) and generates a Google Sheets task tracker with structured task data. It extracts project metadata and tasks from the SOW, then creates a Google Sheets workbook with dropdown statuses and conditional formatting.

## Architecture

```
SOW (PDF/DOCX/TXT) → Parse → Extract Metadata & Tasks → 
Build Google Sheets Task Tracker → Return Sheet URL
```

## Pipeline (SequentialAgent)

The agent consists of 4 sequential sub-agents:

| Step | Agent | Function |
|------|-------|----------|
| 1 | `SOWParserAgent` | Ingests SOW from PDF, DOCX, Excel, or raw text |
| 2 | `PlannerAgent` | Extracts project metadata and task list |
| 3 | `ExcelBuilderAgent` | Creates Google Sheets task tracker |
| 4 | `ReportSummaryAgent` | Produces markdown summary |

## Tools

### 1. `read_pdf_sow`

Reads a PDF file and extracts text content.
- Uses `pypdf` library
- Extracts all pages and text
- Returns: `text` (extracted content), `page_count`

**Location:** Lines 262-297

### 2. `read_docx_sow`

Reads a DOCX file and extracts text content.
- Uses `python-docx` library
- Extracts paragraphs and tables
- Returns: `text`, `paragraph_count`, `table_count`

**Location:** Lines 298-339

### 3. `read_excel_sow`

Reads an Excel file and extracts text content.
- Supports .xlsx and .xls formats
- Converts .xls to .xlsx if needed
- Extracts text from all sheets
- Returns: `text`, `sheet_count`

**Location:** Lines 340-393

### 4. `store_sow_text`

Stores raw SOW text in session state for downstream agents.
- Stores in `session["sow_raw_text"]`
- Returns: `char_count`

**Location:** Lines 394-416

### 5. `save_project_metadata`

Saves project metadata extracted from SOW:
- `project_name` — Project name
- `client_name` — Client name
- `vendor_name` — Vendor name
- `spoc_name` — SPOC name
- `spoc_email` — SPOC email
- `start_date` — Start date (YYYY-MM-DD)
- `end_date` — End date (YYYY-MM-DD)
- `total_weeks` — Total duration in weeks

**Location:** Lines 417-447

### 6. `save_tasks_data`

Saves extracted task list:
- Array of tasks with fields:
  - `phase` — Phase/track name
  - `module` — Module/deliverable
  - `task_detail` — Task description
  - `assigned_to` — Assigned resource
  - `start_date` — Start date
  - `end_date` — End date
  - `status` — Status (To Do/In Progress/Completed/Delayed)
  - `remark` — Notes
- Consolidates bullets by role (max 20 tasks)
- Stores in `session["tasks_data"]`

**Location:** Lines 448-519

### 7. `create_google_task_tracker_sheet`

Creates the Google Sheets workbook:
1. Creates new spreadsheet via Drive API
2. Creates "Task Tracker" sheet
3. Writes headers with styling
4. Writes task rows with data
5. Adds data validation (dropdowns for status)
6. Applies conditional formatting (colors by status)
7. Shares with configured email (optional)
8. Returns `google_sheet_url`

**Styling:**
- Header row: gray fill, bold, centered
- Data rows: left-aligned
- Borders: thin
- Column widths: auto-calculated

**Conditional Formatting:**
- "Completed" → Green background
- "In Progress" → Orange background
- "To Do" → Red background
- "Delayed" → Gray background

**Location:** Lines 520-849

### 8. `get_report_state`

Returns final state:
- `project_name`
- `client_name`
- `vendor_name`
- `start_date`
- `end_date`
- `total_weeks`
- `task_count`
- `google_sheet_url`

**Location:** Lines 850-875

## Agent Definitions

### SOWParserAgent (Lines 876-896)

**Purpose:** Ingest SOW from any supported format

**Tools:** read_pdf_sow, read_docx_sow, read_excel_sow, store_sow_text

**Instruction:** Determines file type from message and calls appropriate reader. Stores extracted text in session.

### PlannerAgent (Lines 899-930)

**Purpose:** Extract project metadata and task list

**Tools:** save_project_metadata, save_tasks_data

**Instruction:** 
- Call 1: Extract metadata → save_project_metadata
- Call 2: Extract tasks (max 20) → save_tasks_data
- Consolidates by track/role

### ExcelBuilderAgent (Lines 933-950)

**Purpose:** Create Google Sheets task tracker

**Tools:** create_google_task_tracker_sheet

**Instruction:** Creates task tracker with dropdowns and conditional formatting from session state.

### ReportSummaryAgent (Lines 953-982)

**Purpose:** Generate markdown summary

**Tools:** get_report_state

**Instruction:** Reads final state and outputs markdown table with project info and sheet links.

## Excel Styling Functions

### `_thin_border()` (Line 87)

Creates thin border for cells.

### `_hdr(cell, value, size)` (Lines 92-97)

Styles header cell:
- Bold font
- Gray fill (FFD9D9D9)
- Centered alignment
- Wrapped text
- Thin border

### `_data(cell, value, align_h, fmt)` (Lines 100-109)

Styles data cell:
- Font size 12
- Left/center alignment
- Optional date formatting
- Thin border

### `_set_col_width(ws, col_letter, width)` (Lines 110-116)

Sets column width.

## Date Handling

### `_parse_date(value)` (Lines 128-142)

Parses various date formats:
- "%Y-%m-%d"
- "%d-%m-%Y"
- "%d/%m/%Y"
- "%d %b %Y"

### Status Normalization

### `_normalize_status(status)` (Lines 167-188)

Maps status variations to standard values:
- "done", "complete", "finished" → "Completed"
- "ongoing", "in progress", "wip" → "In Progress"
- "todo", "to do", "pending", "not started" → "To Do"
- "delayed", "blocked", "on hold" → "Delayed"

## Google Authentication

### `_load_google_credentials()` (Lines 197-254)

Supports two authentication methods:

1. **Service Account** (via `GOOGLE_SHEETS_CREDENTIALS_JSON`)
   - JSON credentials file
   - Used for institutional accounts

2. **OAuth2** (via `GOOGLE_OAUTH_CLIENT_SECRET_JSON`)
   - User-based authentication
   - Token caching in `google_oauth_token.json`
   - Used for personal Drive access

## Environment Variables

| Variable | Description |
|----------|-------------|
| `OUTPUT_DIR` | Local output directory (default: ./outputs) |
| `FILE_SERVER_BASE_URL` | File server URL |
| `GEMINI_MODEL` | Model (default: gemini-2.5-flash) |
| `RETRY_ATTEMPTS` | Retry attempts (default: 5) |
| `RETRY_INITIAL_DELAY` | Retry delay in seconds (default: 2) |
| `GOOGLE_SHEETS_CREDENTIALS_JSON` | Service account JSON path |
| `GOOGLE_SHEETS_CREDENTIALS_B64` | Base64-encoded service account (optional) |
| `GOOGLE_SHEETS_PARENT_FOLDER_ID` | Drive folder for spreadsheets |
| `GOOGLE_SHEETS_SHARE_WITH` | Email to share with |
| `GOOGLE_SHEETS_SHARE_ROLE` | Share role (default: writer) |
| `GOOGLE_SHEETS_MAKE_PUBLIC` | Make sheet public (default: no) |
| `GOOGLE_OAUTH_CLIENT_SECRET_JSON` | OAuth client secret path |
| `GOOGLE_OAUTH_TOKEN_JSON` | OAuth token path |
| `GOOGLE_OAUTH_AUTH_MODE` | Auth mode (default: local_server) |

## Output

Returns:
- `google_sheet_url` — Link to Google Sheets
- `task_count` — Number of tasks
- `project_name` — Project name

## Flow Diagram

```
User Input: PDF/DOCX/TXT file or text
    ↓
SOWParserAgent
    ↓ (read_pdf_sow / read_docx_sow / read_excel_sow / store_sow_text)
    ↓ Session: sow_raw_text
    ↓
PlannerAgent
    ↓ (save_project_metadata, save_tasks_data)
    ↓ Session: project_data, tasks_data
    ↓
ExcelBuilderAgent
    ↓ (create_google_task_tracker_sheet)
    ↓ Session: google_sheet_url
    ↓
ReportSummaryAgent
    ↓ (get_report_state)
    ↓
Final Output: Google Sheet URL, summary
```

## Task Tracker Sheet Structure

| Column | Header | Example |
|-------|--------|--------|
| A | Phase | Phase 1 |
| B | Module | Documentation |
| C | Task | Create SRS |
| D | Assigned To | John |
| E | Start Date | 01/01/2024 |
| F | End Date | 15/01/2024 |
| G | Status | In Progress |
| H | Remark | On track |

## Constants

| Constant | Value |
|----------|-------|
| `HEADER_FILL` | FFD9D9D9 |
| `BLACK` | FF000000 |
| `GOOGLE_SCOPES` | [drive, spreadsheets] |
| `MAX_TASKS` | 20 |