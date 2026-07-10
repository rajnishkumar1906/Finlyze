# backend/run.py
import os
import sys

# Configure UTF-8 encoding for standard outputs to prevent unicode print crashes on Windows
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except AttributeError:
    pass

from app import app

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    # Run server binding to all interfaces on the designated port
    app.run(debug=True, host='0.0.0.0', port=port)
