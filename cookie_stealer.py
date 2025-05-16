import os
import platform
import shutil
import sqlite3
import tempfile
import json
from datetime import datetime, timezone 
import re

# --- Configuration ---
TARGET_DOMAINS = [
    "canvas.tue.nl",
    "sso.canvaslms.com",
    ".login.microsoftonline.com", 
    "login.microsoftonline.com",  
    ".microsoftonline.com"        
]
# Set to True to get ALL cookies for the TARGET_DOMAINS,
FILTER_SESSION_COOKIES_ONLY = False
JSON_OUTPUT_FILENAME = "cookies_filtered.json"

def get_firefox_profile_dir():
    """
    Finds the Firefox profile directory
    """
    system = platform.system()
    if system == "Windows":
        app_data = os.getenv("APPDATA")
        if not app_data:
            print("app data not found")
            return None
        firefox_path = os.path.join(app_data, "Mozilla", "Firefox", "Profiles")
    elif system == "Linux":
        firefox_path = os.path.expanduser("~/.mozilla/firefox")

    if not os.path.exists(firefox_path):
        print(f"Firefox profile path not found: {firefox_path}")
        return None

    profiles = [d for d in os.listdir(firefox_path) if os.path.isdir(os.path.join(firefox_path, d))]
    
    default_release_profile = next((p for p in profiles if "default-release" in p.lower()), None)

    if default_release_profile:
        return os.path.join(firefox_path, default_release_profile)

def copy_cookie_file(profile_dir):
    """
    Copies the cookies.sqlite file to a temporary location.
    """
    cookie_db_path = os.path.join(profile_dir, "cookies.sqlite")
    if not os.path.exists(cookie_db_path):
        print("cookies.sqlite not found in profile")
        return None

    try:
        temp_db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".sqlite")
        temp_db_path = temp_db_file.name
        temp_db_file.close()

        shutil.copy2(cookie_db_path, temp_db_path)
        print(f"Copied cookies.sqlite to temporary file: {temp_db_path}")
        return temp_db_path
    except Exception as e:
        print(f"Error copying cookie file: {e}")
        if 'temp_db_path' in locals() and os.path.exists(temp_db_path): 
            os.remove(temp_db_path)
        return None

def extract_cookies_from_db(db_path, target_domains_list=None, session_only=False):
    """
    Extracts cookies from the Firefox SQLite database, filtering by a list of domains
    """
    cookies_list = []
 
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    query = "SELECT name, value, host, path, expiry, isSecure, isHttpOnly, sameSite, originAttributes FROM moz_cookies"
    
    conditions = []
    params = []

    if target_domains_list and len(target_domains_list) > 0:
        domain_conditions_group = [] 
        for domain_pattern in target_domains_list:
            if domain_pattern.startswith('.'):
                domain_conditions_group.append("host LIKE ?")
                params.append(f"%{domain_pattern}") 
                domain_conditions_group.append("host = ?")
                params.append(domain_pattern[1:])
            else:
                domain_conditions_group.append("host = ?")
                params.append(domain_pattern)
                domain_conditions_group.append("host LIKE ?")
                params.append(f"%.{domain_pattern}") 
        
        if domain_conditions_group: 
            conditions.append("(" + " OR ".join(domain_conditions_group) + ")")

    if session_only:
        conditions.append("expiry = 0")

    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    # For debugging:
    print(f"Executing query: {query}") 
    print(f"With params: {params}")    

    cursor.execute(query, tuple(params))

    for row in cursor.fetchall():
        name, value, host, path, expiry_timestamp, is_secure_val, is_http_only_val, same_site_val, origin_attributes_val = row
        
        cookies_list.append({
            "db_name": name,
            "db_value": value, 
            "db_host": host,
            "db_path": path,
            "db_expiry_raw": expiry_timestamp,
            "db_isSecure": bool(is_secure_val),
            "db_isHttpOnly": bool(is_http_only_val),
            "db_sameSite_raw_val": same_site_val,
            "db_originAttributes": origin_attributes_val if origin_attributes_val else ""
        })
    
    conn.close()
    return cookies_list

def save_cookies_to_new_json_format(cookies_data, output_filename):
    """
    Saves the extracted cookie data to a JSON file in the new specified format.
    """
    json_output_cookies = []
    for cookie in cookies_data:
        scheme = "https://" if cookie['db_isSecure'] else "http://"
        host_raw_val = scheme + cookie['db_host'] + cookie['db_path']
        expires_raw_str = str(cookie['db_expiry_raw'])
        expiry_dt = datetime.fromtimestamp(cookie['db_expiry_raw'], tz=timezone.utc)
        expires_str = expiry_dt.strftime('%d-%m-%Y %H:%M:%S') 
            
        send_for_str = "Encrypted connections only" if cookie['db_isSecure'] else "Any type of connection"
        send_for_raw_str = "true" if cookie['db_isSecure'] else "false"

        http_only_raw_str = "true" if cookie['db_isHttpOnly'] else "false"
        db_same_site_val = cookie.get('db_sameSite_raw_val')
        if db_same_site_val == 1:
            same_site_raw_str = "lax"
        elif db_same_site_val == 2:
            same_site_raw_str = "strict"
        else:
            same_site_raw_str = "no_restriction"

        is_host_only = not cookie['db_host'].startswith('.')
        this_domain_only_str = "Valid for host only" if is_host_only else "Valid for subdomains"
        this_domain_only_raw_str = "true" if is_host_only else "false"

        store_raw_str = "firefox-default"
        origin_attrs = cookie.get("db_originAttributes", "")
        if origin_attrs:
            match = re.search(r'userContextId=(\d+)', origin_attrs)
            if match:
                container_id = match.group(1)
                store_raw_str = f"firefox-container-{container_id}"

        json_cookie = {
            "Host raw": host_raw_val,
            "Name raw": cookie['db_name'],
            "Path raw": cookie['db_path'],
            "Content raw": cookie['db_value'],
            "Expires": expires_str,
            "Expires raw": expires_raw_str,
            "Send for": send_for_str,
            "Send for raw": send_for_raw_str,
            "HTTP only raw": http_only_raw_str,
            "SameSite raw": same_site_raw_str,
            "This domain only": this_domain_only_str,
            "This domain only raw": this_domain_only_raw_str,
            "Store raw": store_raw_str,
            "First Party Domain": cookie.get("db_originAttributes", "")
        }
        json_output_cookies.append(json_cookie)

    try:
        with open(output_filename, 'w', encoding='utf-8') as f: 
            json.dump(json_output_cookies, f, indent="\t")
        print(f"\nSuccessfully saved {len(json_output_cookies)} cookies to {output_filename}")
    except IOError as e:
        print(f"Error writing JSON to file {output_filename}: {e}")


def main():
    if TARGET_DOMAINS:
        print(f"Filtering for domains: {', '.join(TARGET_DOMAINS)}")
    else:
        print("No specific domains targeted, will extract all cookies.")
        
    profile_dir = get_firefox_profile_dir()
    if not profile_dir:
        print("Could not find Firefox profile")
        return

    print(f"Found Firefox profile: {profile_dir}")
    
    temp_cookie_db_path = copy_cookie_file(profile_dir)
    if not temp_cookie_db_path:
        print("Could not copy cookie file")
        return

    print(f"Extracting cookies from: {temp_cookie_db_path}")
    
    extracted_cookies = extract_cookies_from_db(
        temp_cookie_db_path,
        target_domains_list=TARGET_DOMAINS,
        session_only=FILTER_SESSION_COOKIES_ONLY
    )

    save_cookies_to_new_json_format(extracted_cookies, JSON_OUTPUT_FILENAME)
   
    if temp_cookie_db_path and os.path.exists(temp_cookie_db_path):
        try:
            os.remove(temp_cookie_db_path)
            print(f"\Temp cookie file {temp_cookie_db_path} removed.")
        except Exception as e:
            print(f"Error removing temp file {temp_cookie_db_path}: {e}")

if __name__ == "__main__":
    main()
