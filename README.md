## SecurityProject2025 Gruop 16
Use CVE-2023-45866 to connect to a "victim"'s outdated linux os, disguised as a bluetooth keyboard, and inject keystrokes, to spoof the victim's firefox and steal the victim's browswer cookies. We specifically aimed for cookies related to "canvas.tue.nl" in the initial approaved idea, but any cookie can be stolen. 

The Cookie Stealer set up is under the main branch; the bluetooth hack set up is under the ducky branch. However, all the functionalities are explained under this README file. 

## Cookie Stealer

#### server.py:

#### scripts/setup.sh:
This is a bash script that will be downloaded to the "victim"'s computer and executed. The precondition to run this script is that the fake firefox is already downloaded under the same directory. Normally, firefox executable is located under /usr/bin/ or /snap/bin/. We create a directory $HOME/bin/, and copy the fake firefox there. Then we append this directory to the front of the path environment variable, defined shell configuration files such as .bashrc or .zshrc, so that this firefox will be found first and called when every the command "firefox" is initiated. If a Desktop folder exists under $HOME, then the "victim" also has a desktop environment, so we add a desktop shortcut to the fake firefox to increase the chance of success.

#### scripts/firefox.py
This is the script to launch a playwright firefox instance using the "victim"'s profile, and whenever "canvas.tue.nl" is logged into, we send all the cookies in that browser back to our server.  Here are some notes and caveats: 
- Playwright is an open-source automation library and framework developed by Microsoft for testing and automating browser interactions. 
- We don't know which profile the "victim" uses for university work. For this project, we assume it is any default profile.
- This file is intended to run as a bundled executable, running it with python, comment out line 12 - 16.

To make bundle the script into an executable, it would be convenient to know the "victim"'s linux distro / version. If we know that, we can bundle the script on that specific verion and distro of linux, to avoid version mismatch problems. The script requires: 
$ pip install playwright aiohttp pyinstaller
$ playwright install firefox
Once the required packages are ready, you can execute: 
$ pyinstaller firefox.py --onefile --add-data "$(realpath ~/.cache/ms-playwright):ms-playwright"
And this will bundle an executable into ./dist/firefox

## BluetoothDucky
