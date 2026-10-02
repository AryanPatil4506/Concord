"""`python -m server [--port 8000]` — start the live console."""
import argparse

import uvicorn

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="CONCORD live console")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()
    print(f"CONCORD console -> http://{args.host}:{args.port}")
    uvicorn.run("server.app:app", host=args.host, port=args.port, log_level="warning")
