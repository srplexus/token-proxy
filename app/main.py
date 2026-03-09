import os
import base64
import json
import requests
import ipaddress
import secrets
from flask import Flask, request, jsonify

app = Flask(__name__)

# Config
PROXY_BASIC_AUTH = os.environ.get("PROXY_BASIC_AUTH", "")
PROXY_TRUSTED_IPS = os.environ.get("PROXY_TRUSTED_IPS", "").split(',')

def log_event(level, message, **kwargs):
    """Helper to print structured JSON logs for Cloud Logging"""
    entry = {
        "severity": level,
        "message": message,
        **kwargs
    }
    print(json.dumps(entry))

def is_ip_allowed(client_ip, trusted_list):
    """Checks if the client_ip is an individual entry or falls within a CIDR block."""
    try:
        ip_obj = ipaddress.ip_address(client_ip)
        for entry in trusted_list:
            # ip_network(entry) handles both '1.2.3.4' and '1.2.3.0/24'
            if ip_obj in ipaddress.ip_network(entry, strict=False):
                return True
    except ValueError:
        log_event(
            "ERROR", "Invalid IP format in request or trusted list", client_ip=client_ip)
    return False

@app.route("/get-token", methods=["GET"])
def get_token():
    # Capture metadata for logs
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
    auth_header = request.headers.get('Authorization', "")

    # Initialize variables for logging
    provided_user = "None"

    # 1. Debug: Extract User for Logging
    if auth_header.startswith('Basic '):
        try:
            credential = base64.b64decode(auth_header.split(' ')[1]).decode('utf-8')
            provided_user = credential.split(':')[0]
        except Exception:
            provided_user = "Malformed-Auth"

    log_event("INFO", "Token request received", client_ip=client_ip, provided_user=provided_user)

    # 2. Security Checks
    if not is_ip_allowed(client_ip, PROXY_TRUSTED_IPS):
        log_event("WARNING", "Access Denied: IP/CIDR block not trusted", ip=client_ip)
        return "Forbidden", 403

    # Use constant time comparison to mitigate timing attacks
    if not secrets.compare_digest(credential, PROXY_BASIC_AUTH):
        log_event("WARNING", "Auth failed", client_ip=client_ip, provided_user=provided_user)
        return "Unauthorized", 401

    # 3. Fetch Access Token
    try:
        token_url = "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token"
        response = requests.get(token_url, headers={"Metadata-Flavor": "Google"})
        log_event("INFO", "Token successfully vended", user=provided_user)
        return jsonify(response.json())
    except Exception as e:
        log_event("ERROR", f"Metadata server error: {str(e)}")
        return "Internal Error", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))