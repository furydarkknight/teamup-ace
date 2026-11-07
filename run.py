import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure UTF-8 console output on Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

# Load .env
load_dotenv(PROJECT_ROOT / ".env")

import uvicorn

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    print("\n" + "="*60)
    print(">>> Starting TeamUp by ACE Web Server...")
    print(f">> Web Application URL: http://localhost:{port} (or http://127.0.0.1:{port})")
    print(f">> Swagger API Docs:    http://localhost:{port}/docs")
    print(f">> ReDoc API Docs:      http://localhost:{port}/redoc")
    print("="*60 + "\n")
    uvicorn.run("app.main:app", host=host, port=port, reload=False)
