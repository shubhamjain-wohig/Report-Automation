# Report Generator Agent

**Location:** `/Users/shubhamjain/Documents/Report Automation Tool/Report_generator/agent.py`

## Overview

The Report Generator Agent is a Phase 2 component that transforms a weekly report Excel file into a polished Google Slides presentation. It takes an already-generated Excel file (from the SOW Report Agent), extracts metadata and task data, renders the Timeline sheet as a Gantt chart, and generates a Google Slides presentation with the chart embedded.

## Architecture

```
Excel → Extract Metadata → Render Timeline to PNG → Upload to Drive → 
Build Slides (template + placeholders) → Embed PNG → Return Slides URL
```

## Pipeline (SequentialAgent)

The agent consists of 4 sequential sub-agents:

| Step | Agent | Function |
|------|-------|----------|
| 1 | `ExcelReaderAgent` | Parses Excel file, extracts metadata, placeholders, and detects Timeline sheet range |
| 2 | `ScreenshotAgent` | Renders Timeline sheet to PNG, uploads to Google Drive |
| 3 | `SlidesBuilderAgent` | Duplicates template, injects placeholders, embeds PNG image |
| 4 | `CleanupAgent` | Cleans up temporary Drive image, returns final slides URL |

## Tools

### 1. `extract_excel_data`

Parses the Excel weekly report to extract:
- Project metadata (project name, client, dates)
- Placeholder values ({{PROJECT_NAME}}, {{CLIENT_NAME}}, etc.)
- Dynamic Timeline sheet range (e.g., A1:M32)

**Location:** Lines 313-507

### 2. `capture_timeline_screenshot`

Renders the Timeline sheet range to a high-resolution PNG image:
- Uses `_get_dynamic_range()` to detect sheet bounds dynamically
- Renders via `_render_table_to_png()` for simple tables
- Renders via `_render_gantt_chart()` for Gantt-style timelines
- Uses matplotlib for chart visualization (lines 1374-1483)
- Uploads the PNG to Google Drive
- Returns `drive_image_id`, `width_px`, `height_px`

**Location:** Lines 1122-1295

### 3. `build_slides_report`

Builds the Google Slides presentation:
1. Duplicates the template presentation (`GOOGLE_SLIDES_TEMPLATE_ID`)
2. Extracts placeholders from session state (`{{TAG}}` → replacement)
3. Replaces placeholders case-insensitively via Slides API
4. Finds timeline placeholder shape (named "timeline" or "gantt")
5. Injects the PNG with smart scaling to fit the placeholder
6. Returns final `slides_url`

**Location:** Lines 1637-2010

### 4. `cleanup_temp_assets`

Deletes the temporary Drive image after embedding:
- Removes the uploaded PNG from Google Drive
- Returns final state with slides URL

**Location:** Lines 2164-2221

## Key Functions

### Gantt Chart Rendering

`_render_gantt_chart()` (lines 1374-1483):
- Creates a matplotlib figure with phases on Y-axis, dates on X-axis
- Uses FancyBboxPatch for rounded bar styling
- Renders module/task names on bars
- Color-codes by status (Completed/In Progress/To Do)
- Returns PIL Image

**Configurable parameters:**
- Title fontsize: Line 1459 (currently 17)
- Bar label fontsize: Line 1452 (currently 8) — bold removed
- Chart stretches to fill placeholder (lines 2106-2109, changed from aspect-fit)

### Excel Extraction

`_extract_metadata()` (lines 890-983):
- Parses sheet headers dynamically
- Extracts project name from workbook properties or cells
- Detects date range from Timeline sheet

`_extract_tasks()` (lines 1004-1043):
- Detects header row dynamically
- Extracts task rows with columns: phase, module, task_detail, assigned_to, start_date, end_date, status, remark

### Placeholder Detection

`_build_placeholder_map()` (lines 1045-1120):
- Builds {{TAG}} → value map from metadata and tasks
- Handles placeholders: PROJECT_NAME, CLIENT_NAME, VENDOR_NAME, SPOC_NAME, SPOC_EMAIL, START_DATE, END_DATE, TOTAL_WEEKS, etc.
- Task counts: TOTAL_TASKS, DONE_TASKS, IN_PROGRESS_TASKS, TODO_TASKS

### Slides Injection

`_inject_timeline_image()` (lines 2011-2162):
- Finds placeholder shape named "timeline" or "gantt"
- Gets shape dimensions (translateX, translateY, scaleX, scaleY)
- Smart-scales image to fit (now uses exact dimensions)
- Centers image within placeholder bounds
- Deletes original placeholder shape
- Inserts new image

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GOOGLE_SLIDES_TEMPLATE_ID` | ID of master Google Slides template |
| `TIMELINE_SHEET_NAME` | Name of Timeline sheet in Excel (default: "Timeline 1") |
| `GOOGLE_OAUTH_CLIENT_SECRET_JSON` | OAuth2 client secret path |
| `GOOGLE_OAUTH_TOKEN_JSON` | Cached OAuth token path |
| `GOOGLE_SLIDES_PARENT_FOLDER_ID` | Drive folder for output (optional) |
| `GEMINI_MODEL` | Model (default: gemini-2.5-flash) |
| `OUTPUT_DIR` | Local output directory (default: ./outputs) |

## Output

Returns:
- `slides_url` — Final Google Slides URL
- `placeholder_count` — Number of placeholders replaced
- `timeline_range` — Detected Timeline sheet range
- `image_dimensions` — PNG dimensions (width_px x height_px)

## Flow Diagram

```
User Input: Excel file path
    ↓
ExcelReaderAgent → extract_excel_data
    ↓ Session: excel_data, placeholder_map, timeline_range
    ↓
ScreenshotAgent → capture_timeline_screenshot
    ↓ Session: drive_image_id, image_dimensions
    ↓
SlidesBuilderAgent → build_slides_report
    ↓ Session: slides_url
    ↓
CleanupAgent → cleanup_temp_assets
    ↓
Final Output: slides_url
```

## Key Constants

| Constant | Value | Location |
|----------|-------|----------|
| `EMU_PER_INCH` | 914400 | Line 2083 |
| `SLIDE_W_IN` | 13.333 | Line 102 |
| `SLIDE_H_IN` | 7.5 | Line 102 |
| `GEMINI_MODEL` | gemini-2.5-flash | Line 100 |