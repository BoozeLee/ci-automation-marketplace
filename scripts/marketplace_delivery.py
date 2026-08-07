#!/usr/bin/env python3
"""GitHub Marketplace webhook handler - sends download link via email."""

import json
import smtplib
import ssl
from email.mime.text import MIMEText
from http.server import HTTPServer, BaseHTTPRequestHandler

SMTP_HOST = "smtp.zoho.eu"
SMTP_PORT = 465
SMTP_USER = "bakerstreetbandit@zohomail.eu"
SMTP_PASS = "XhFm39wuR9zs"
DOWNLOAD_URL = "https://github.com/BoozeLee/ci-automation-marketplace/releases/download/v1.0.0/ci-automation-package-v1.zip"


class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get('content-length', 0))
        body = self.rfile.read(length).decode('utf-8')
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            return

        action = data.get('action', '')
        if action == 'purchased':
            email = data.get('sender', {}).get('email') or data.get('email')
            if email:
                self.send_download_link(email)
                print(f"Sent download link to {email}")
            else:
                print("No email found in payload")

        self.send_response(200)
        self.end_headers()

    def send_download_link(self, to_email):
        msg = MIMEText(
            f"Thanks for purchasing CI/CD Automation Toolkit!\n\nDownload: {DOWNLOAD_URL}\n\nCheers,\nBaker Street Labs",
            "plain",
            "utf-8",
        )
        msg["Subject"] = "Your CI/CD Automation Toolkit download"
        msg["From"] = SMTP_USER
        msg["To"] = to_email
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8080), WebhookHandler)
    print("Webhook listener on :8080")
    server.serve_forever()
