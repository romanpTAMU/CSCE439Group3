#!/usr/bin/env python3
"""
Main entry point for the defender application.
"""

import os
import sys
from pathlib import Path

# Ensure project root is importable
root_dir = Path(__file__).parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# Minimal Flask webserver that accepts an uploaded EXE and returns ONLY the label
try:
    from flask import Flask, request, jsonify
    app = Flask(__name__)

    @app.route('/health', methods=['GET'])
    def health():
        return 'ok', 200

    @app.route('/predict', methods=['POST'])
    def predict_route():
        # Expect a file field named 'file'
        if 'file' not in request.files:
            return jsonify({"error": "missing file"}), 400
        f = request.files['file']
        if f.filename == '':
            return jsonify({"error": "empty filename"}), 400
        # Save to a temporary path (Windows-safe: don't keep file open while saving)
        import tempfile, os
        fd, tmp_path = tempfile.mkstemp(suffix='.exe')
        os.close(fd)
        try:
            f.save(tmp_path)
            from defender.inference_service import score_exe
            res = score_exe(tmp_path)
            # Return label only to avoid leaking model details
            return jsonify({"label": int(res["label"])})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

    def run_server():
        app.run(host='0.0.0.0', port=int(os.environ.get('PORT', '8000')))
except Exception:
    # Flask might not be installed in some environments; ignore server setup
    def run_server():
        print("Flask not available. Server not started.")

if __name__ == "__main__":
    run_server()
