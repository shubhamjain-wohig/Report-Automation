"""
main.py  —  ADK Automated Weekly Report Tool
Entry point: starts the FastAPI file server + ADK web UI (or programmatic runner).

Usage:
  python main.py                          # ADK Web UI  (recommended)
  python main.py --no-ui --sow-pdf /path/to/sow.pdf
  python main.py --no-ui --sow-docx /path/to/sow.docx
  python main.py --no-ui --sow-text "paste SOW text here"
  adk web                                 # ADK native CLI (alternative)
"""

import argparse
import asyncio
import os
import subprocess
import sys
import threading
from pathlib import Path

import uvicorn
from dotenv import load_dotenv

# ── Environment ───────────────────────────────────────────────────────────────
load_dotenv()

OUTPUT_DIR       = os.environ.get("OUTPUT_DIR",           "./outputs")
FILE_SERVER_PORT = int(os.environ.get("FILE_SERVER_PORT", "8000"))
ADK_PORT         = int(os.environ.get("ADK_PORT",         "8080"))

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ══════════════════════════════════════════════════════════════════════════════
# FILE SERVER  —  serves generated .xlsx files as download links
# ══════════════════════════════════════════════════════════════════════════════

def _create_file_server():
    from fastapi import FastAPI, UploadFile, File, BackgroundTasks
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from fastapi.staticfiles import StaticFiles

    app = FastAPI(title="SOW Report File Server", version="1.0.0")

    # Allow the ADK web UI (localhost:8080) to fetch download links
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    app.mount(
        "/files",
        StaticFiles(directory=OUTPUT_DIR, html=False),
        name="files",
    )

    @app.get("/health")
    def health():
        return {
            "status": "ok",
            "output_dir": str(Path(OUTPUT_DIR).resolve()),
            "file_server_port": FILE_SERVER_PORT,
        }

    @app.get("/list")
    def list_files():
        """List all generated Excel reports available for download."""
        files = []
        for fname in sorted(os.listdir(OUTPUT_DIR), reverse=True):
            if fname.endswith(".xlsx"):
                fpath = os.path.join(OUTPUT_DIR, fname)
                files.append({
                    "name":         fname,
                    "size_kb":      round(os.path.getsize(fpath) / 1024, 2),
                    "download_url": f"http://localhost:{FILE_SERVER_PORT}/files/{fname}",
                })
        return JSONResponse({"count": len(files), "files": files})

    @app.post("/upload")
    async def upload_file(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
        """Accept file upload and return filename for processing."""
        try:
            import secrets
            ext = Path(file.filename).suffix
            safe_name = f"upload_{secrets.token_hex(4)}{ext}"
            temp_path = Path(OUTPUT_DIR) / safe_name
            
            content = await file.read()
            with open(temp_path, "wb") as f:
                f.write(content)
            
            return JSONResponse({
                "success": True,
                "filename": file.filename,
                "temp_path": str(temp_path),
                "file_type": ext.lower(),
                "size_bytes": len(content),
            })
        except Exception as exc:
            return JSONResponse(
                {"success": False, "error": str(exc)},
                status_code=400,
            )

    @app.post("/process")
    async def process_sow(data: dict):
        """Trigger SOW processing and return Google Sheet link."""
        try:
            temp_path = data.get("temp_path", "")
            file_type = data.get("file_type", "").lower()
            original_filename = data.get("filename", "")
            
            if not temp_path or not Path(temp_path).exists():
                return JSONResponse(
                    {"success": False, "error": "File not found"},
                    status_code=400,
                )
            
            # Determine file type and build command
            if file_type == ".pdf":
                message = f"Generate a weekly report from this SOW PDF: {temp_path}"
            elif file_type == ".docx":
                message = f"Generate a weekly report from this SOW DOCX: {temp_path}"
            elif file_type == ".xlsx" or file_type == ".xls":
                original_name = Path(data.get("filename", "")).stem or Path(temp_path).stem.replace("upload_", "")
                message = f"Generate a weekly report from this SOW Excel file: {temp_path} (Project Name: {original_name})"
            elif file_type == ".txt":
                with open(temp_path, "r") as f:
                    sow_text = f.read()
                message = f"Generate a weekly report from this SOW:\n\n{sow_text}"
            else:
                return JSONResponse(
                    {"success": False, "error": f"Unsupported file type: {file_type}. Supported: .pdf, .docx, .xlsx, .xls, .txt"},
                    status_code=400,
                )
            
            # Run the agent in this request's async context and capture result
            result = await _run_agent_sync(message)
            return JSONResponse(result)
        except Exception as exc:
            return JSONResponse(
                {"success": False, "error": str(exc)},
                status_code=500,
            )

    return app


def _start_file_server():
    app = _create_file_server()
    uvicorn.run(app, host="0.0.0.0", port=FILE_SERVER_PORT, log_level="warning")


# ══════════════════════════════════════════════════════════════════════════════
# AGENT PROCESSOR  —  synchronous wrapper for file processing
# ══════════════════════════════════════════════════════════════════════════════

async def _run_agent_sync(user_message: str) -> dict:
    """Run the SequentialAgent pipeline and return result dict with google_sheet_url."""
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types as genai_types

    # Import root_agent from the agent module
    from sow_report_agent.agent import root_agent

    try:
        svc     = InMemorySessionService()
        session = await svc.create_session(
            app_name="sow_report_agent",
            user_id="user_web_upload",
        )
        runner = Runner(
            agent=root_agent,
            app_name="sow_report_agent",
            session_service=svc,
        )

        google_sheet_url = None
        google_sheet_id = None
        error_msg = None

        content = genai_types.Content(
            role="user",
            parts=[genai_types.Part(text=user_message)],
        )

        async for event in runner.run_async(
            user_id="user_web_upload",
            session_id=session.id,
            new_message=content,
        ):
            # Check for final response to extract Google Sheet link
            if event.is_final_response():
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        txt = getattr(part, "text", "")
                        if txt and "docs.google.com/spreadsheets" in txt:
                            # Extract URL from response
                            import re
                            match = re.search(r'https://docs\.google\.com/spreadsheets/d/[^\s/]+', txt)
                            if match:
                                google_sheet_url = match.group(0)
                        if txt and "error" in txt.lower():
                            error_msg = txt

        if google_sheet_url:
            return {
                "success": True,
                "google_sheet_url": google_sheet_url,
                "message": "Report generated successfully!",
            }
        else:
            return {
                "success": False,
                "error": error_msg or "Failed to generate report",
            }
    except Exception as exc:
        return {
            "success": False,
            "error": f"Agent error: {str(exc)}",
        }



async def _run_agent(user_message: str):
    """Run the SequentialAgent pipeline programmatically and stream output."""
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types as genai_types

    # Import root_agent from the single agent.py file
    from agent import root_agent

    svc     = InMemorySessionService()
    session = await svc.create_session(
        app_name="sow_report_agent",
        user_id="user_001",
    )
    runner = Runner(
        agent=root_agent,
        app_name="sow_report_agent",
        session_service=svc,
    )

    _banner("SOW Report Agent  —  Running pipeline")

    content = genai_types.Content(
        role="user",
        parts=[genai_types.Part(text=user_message)],
    )

    async for event in runner.run_async(
        user_id="user_001",
        session_id=session.id,
        new_message=content,
    ):
        author = getattr(event, "author", "System")

        if event.is_final_response():
            if event.content and event.content.parts:
                for part in event.content.parts:
                    txt = getattr(part, "text", "")
                    if txt:
                        print(f"\n{'─'*64}")
                        print(f"  ✅  FINAL RESPONSE  [{author}]")
                        print(f"{'─'*64}")
                        print(txt)
        else:
            if event.content and event.content.parts:
                for part in event.content.parts:
                    txt = getattr(part, "text", "").strip()
                    if txt:
                        preview = txt[:160] + ("…" if len(txt) > 160 else "")
                        print(f"  [{author}] {preview}")


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _banner(title: str):
    line = "═" * 64
    print(f"\n{line}\n  {title}\n{line}\n")


def _print_startup_info(mode: str):
    _banner("ADK Automated Weekly Report Tool")
    print(f"  📂  Output directory : {Path(OUTPUT_DIR).resolve()}")
    print(f"  🌐  File server      : http://localhost:{FILE_SERVER_PORT}/files")
    print(f"  📋  File listing     : http://localhost:{FILE_SERVER_PORT}/list")
    if mode == "web":
        print(f"  🚀  ADK Web UI       : http://localhost:{ADK_PORT}")
    print()
    print("  Example prompts:")
    print('  • "Generate a weekly report from this SOW PDF: /path/to/sow.pdf"')
    print('  • "Generate a weekly report from this SOW DOCX: /path/to/sow.docx"')
    print('  • "Generate a weekly report from this SOW: <paste full SOW text>"')
    print()


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="ADK Automated Weekly Report Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                                   # ADK Web UI (recommended)
  python main.py --no-ui --sow-pdf ./sow.pdf       # from PDF
  python main.py --no-ui --sow-docx ./sow.docx     # from Word doc
  python main.py --no-ui --sow-text "SOW content"  # from pasted text
  adk web                                           # ADK native CLI
        """,
    )
    parser.add_argument(
        "--no-ui", action="store_true",
        help="Run programmatically without the ADK web UI.",
    )
    parser.add_argument(
        "--sow-pdf", type=str, default="", metavar="PATH",
        help="Path to a SOW PDF file (requires --no-ui).",
    )
    parser.add_argument(
        "--sow-docx", type=str, default="", metavar="PATH",
        help="Path to a SOW Word (.docx) file (requires --no-ui).",
    )
    parser.add_argument(
        "--sow-text", type=str, default="", metavar="TEXT",
        help="Raw SOW text string (requires --no-ui).",
    )
    parser.add_argument(
        "--file-server-only", action="store_true",
        help="Start only the file server (useful for serving already-generated reports).",
    )
    args = parser.parse_args()

    # ── Validate API key ──────────────────────────────────────────────────
    if not os.environ.get("GOOGLE_API_KEY"):
        print("❌  GOOGLE_API_KEY is not set.")
        print("    Add it to your .env file:  GOOGLE_API_KEY=your_key_here")
        sys.exit(1)

    # ── Always start file server in background ────────────────────────────
    print(f"📁  Starting file server → http://localhost:{FILE_SERVER_PORT}/files")
    threading.Thread(target=_start_file_server, daemon=True).start()

    # ── File-server-only mode ─────────────────────────────────────────────
    if args.file_server_only:
        _print_startup_info("files")
        print("  File server running. Press Ctrl+C to stop.\n")
        try:
            threading.Event().wait()
        except KeyboardInterrupt:
            print("\n  Stopped.")
        return

    # ── Programmatic / no-UI mode ─────────────────────────────────────────
    if args.no_ui:
        # PDF takes priority if multiple flags given
        if args.sow_pdf and args.sow_docx:
            print("⚠️   Both --sow-pdf and --sow-docx provided; using --sow-pdf.")

        if args.sow_pdf:
            path = Path(args.sow_pdf).resolve()
            if not path.exists():
                print(f"❌  PDF not found: {path}")
                sys.exit(1)
            user_msg = f"Generate a weekly report from this SOW PDF: {path}"

        elif args.sow_docx:
            path = Path(args.sow_docx).resolve()
            if not path.exists():
                print(f"❌  DOCX not found: {path}")
                sys.exit(1)
            user_msg = f"Generate a weekly report from this SOW DOCX: {path}"

        elif args.sow_text:
            user_msg = f"Generate a weekly report from this SOW:\n\n{args.sow_text}"

        else:
            parser.error(
                "--no-ui requires one of: --sow-pdf, --sow-docx, --sow-text"
            )

        _print_startup_info("programmatic")
        asyncio.run(_run_agent(user_msg))
        return

    # ── ADK Web UI mode (default) ─────────────────────────────────────────
    _print_startup_info("web")
    try:
        subprocess.run(
            [sys.executable, "-m", "google.adk.cli", "web", "--port", str(ADK_PORT)],
            check=True,
        )
    except KeyboardInterrupt:
        print("\n  ADK Web UI stopped.")
    except subprocess.CalledProcessError as exc:
        print(f"❌  ADK web UI failed: {exc}")
        print("    Try running directly: adk web")
        sys.exit(1)
    except FileNotFoundError:
        print("❌  google-adk CLI not found. Install: pip install google-adk")
        sys.exit(1)


if __name__ == "__main__":
    main()
