#!/usr/bin/env python3
"""
Main entry point for the defender application.
Competition format: POST / with Content-Type: application/octet-stream
Returns {"result": 0} for benign, {"result": 1} for malicious
"""

import os
import sys
from pathlib import Path

# Ensure project root is importable
root_dir = Path(__file__).parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# Competition-compliant Flask webserver
try:
    from flask import Flask, request, jsonify
    app = Flask(__name__)

    @app.route('/', methods=['POST'])
    def predict_route():
        """
        Competition endpoint: POST / with Content-Type: application/octet-stream
        Returns {"result": 0} for benign, {"result": 1} for malicious
        """
        # Check content type
        if request.content_type != 'application/octet-stream':
            return jsonify({"result": 0}), 400  # Default to benign on error
        
        # Get raw bytes from request body
        pe_bytes = request.get_data()
        if not pe_bytes:
            return jsonify({"result": 0}), 400  # Default to benign on error
        
        # Save to temporary file
        import tempfile
        fd, tmp_path = tempfile.mkstemp(suffix='.exe')
        os.close(fd)
        try:
            with open(tmp_path, 'wb') as f:
                f.write(pe_bytes)
            
            from defender.inference_service import score_exe
            res = score_exe(tmp_path)
            # Return competition format: {"result": 0|1}
            return jsonify({"result": int(res["label"])})
        except Exception as e:
            # Default to benign on any error (competition requirement)
            return jsonify({"result": 0}), 500
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

    def run_server():
        # Competition requirement: listen on port 8080
        app.run(host='0.0.0.0', port=int(os.environ.get('PORT', '8080')))
except Exception:
    # Flask might not be installed in some environments; ignore server setup
    def run_server():
        print("Flask not available. Server not started.")

if __name__ == "__main__":
    run_server()