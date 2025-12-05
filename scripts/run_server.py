#!/usr/bin/env python3
"""Simple server runner for TPS."""
import os
import sys

# Change to project directory
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, "src")

if __name__ == "__main__":
    import uvicorn
    from tps.config import settings
    
    print(f"Starting TPS server on http://{settings.api_host}:{settings.api_port}")
    print("Press Ctrl+C to stop")
    
    uvicorn.run(
        "tps.app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
        log_level="info"
    )
