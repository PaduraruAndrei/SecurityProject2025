## SecurityProject2025 Group 16

Use `CVE-2023-45866` to connect to a victim's outdated `linux` os, disguised as a bluetooth keyboard, and inject keystrokes, to spoof the victim's `firefox` and steal the victim's browswer cookies. We specifically aimed for cookies related to `canvas.tue.nl` in the initial approaved idea, but any cookie can be stolen. 

## Cookie Stealer

Launch `server.py`, make sure `setup.sh` and `firefox` (executable version) is under the directory `script/`, wait for the victim to log into canvas, and receive a cookie file in JSON. You can load the cookies into your own browser using an extention called "Cookie Quick Manager".

#### `server.py`:

This Python script runs a simple HTTP server with two main functions: hosting the payload files for the victim to download, and receiving the stolen cookie data sent from the victim's machine. The server is started with the command `python3 server.py`, which by default runs on port 8000 and serves files from a local `./scripts` directory. These settings can be overridden using the `--port` and `--directory` command-line arguments. When the fake firefox sends the stolen data, the server saves it as a JSON file in a `received/` directory for the attacker to use.

#### `scripts/setup.sh`:

This is a bash script that will be downloaded to the victim's computer and executed. The precondition to run this script is that the fake `firefox` is already downloaded under the same directory. Normally, the `firefox` executable is located under `/usr/bin/` or `/snap/bin/`. We create a directory `$HOME/bin/`, and copy the fake `firefox` there. Then we append this directory to the front of the `$PATH` environment variable, defined in shell configuration files such as `.bashrc` or `.zshrc`, so that this `firefox` will be found first and called whenever the command `firefox` is initiated. If a `Desktop` folder exists under `$HOME`, then the victim also has a desktop environment, so we add a desktop shortcut to the fake `firefox` to increase the chance of success.

#### `scripts/firefox.py`

This is the script to launch a playwright `firefox` instance using the victim's profile, and whenever `canvas.tue.nl` is logged into, we send all the cookies in that browser back to our server.  Here are some notes and caveats: 

  - Playwright is an open-source automation library and framework developed by Microsoft for testing and automating browser interactions. 
  - We don't know which profile the victim uses for university work. For this project, we assume it is any default profile.
  - This file is intended to run as a bundled executable, running it with `python` requires commenting out lines 12 - 16.

To bundle the script into an executable, it would be convenient to know the victim's `linux` distro / version. If we know that, we can bundle the script on that specific verion and distro of `linux`, to avoid version mismatch problems. The script requires: 

```bash
pip install playwright aiohttp pyinstaller
playwright install firefox
```

Once the required packages are ready, you can execute: 

```bash
pyinstaller firefox.py --onefile --add-data "$(realpath ~/.cache/ms-playwright):ms-playwright"
```

And this will bundle an executable into `./dist/firefox`. Make sure this firefox is placed at `scripts/firefox` for server.py to send to the victim's computer. 

## BluetoothDucky

To connect to the victim's outdated `linux` os disguised as a bluetooth keyboard, we use an existing repository that performs this hack: [Link to repo](https://github.com/Eason-zz/BluetoothDucky.git). We provide our own `BluetoothDucky.py` and `client.py` to replace that with the same names inside the repo. Our changes fix some minor bugs and speed up the attack. 

#### `BluetoothDucky.py`:

The code file `BluetoothDucky.py` pulled from the github has a small bug in the main function. We fix it in our `BluetoothDucky.py`. We also change our "disguised bluetooth keyboard"'s name to "Earphones" to lower the chance of detection. 

#### `client.py`:

The delay between keystrokes is defined in `injector/client.py`. We decrease that delay in our `client.py` to speed up the attack. 

#### `Payload.txt`

To perform this hack, we must inject our own custom key strokes. This is included in `payload.txt`. Below are the general steps we perform in payload:

  - Open the terminal
  - Go to user directory
  - Make a directory called `ToolBox`
  - Download the firefox executable using a wget command that also extracts the server's dynamic URL from a custom X-Server-Config header and saves it to `config.json`, and give the firefox executable permissions to execute. 
  - Download `setup.sh` and make it also executable.
  - Call `setup.sh`
  - Exit terminal
