# Agent Context — Report Automation Tool

## Project purpose
This project is a Google ADK multi-agent system that turns SOW input (PDF path or pasted text) into a weekly Excel report and a natural-language summary.

## Runtime context
- Python virtual environment: `venv/`
- Activate before running:
  ```bash
  source "/Users/shubhamjain/Documents/Report Automation Tool/venv/bin/activate"
  ```
- Main entry point: `main.py`
- Core dependencies are in `requirements.txt` (Google ADK, openpyxl, pypdf, FastAPI, uvicorn, dotenv).

## Agent architecture
- `agents/orchestrator.py` defines `root_agent` as a `SequentialAgent`.
- Execution flow:
  1. `SOWParserAgent` (`agents/sow_parser.py`)
  2. `PlannerAgent` (`agents/planner.py`)
  3. `ExcelBuilderAgent` (`agents/excel_builder.py`)
  4. `ReportSummaryAgent` (`agents/report_summary.py`)

## Tools and utilities
- `tools/pdf_reader.py`: reads PDF into text.
- `tools/docx_reader.py`: reads DOCX into text.
- `tools/excel_writer.py`: creates Excel output and returns path.
- `tools/gantt_chart.py`: generates a Gantt chart image from the Excel file.
- `tools/google_sheets_writer.py`: uploads Excel to Google Sheets and returns link.
- `tools/file_server.py`: serves generated files for download.
- `utils/excel_styles.py`: shared Excel styling helpers.

## Running the app
```bash
pip install -r requirements.txt

# Optional: Google Sheets export (service account)
# export GOOGLE_SHEETS_CREDENTIALS_JSON=/absolute/path/to/service_account.json
# export GOOGLE_SHEETS_SHARE_WITH=you@company.com

adk web
```

Alternative:
```bash
python main.py
```

Programmatic mode (no UI):
```bash
python main.py --no-ui --sow-pdf /path/to/sow.pdf
```
