#!/usr/bin/env python3
"""Test and send applications to all companies via email."""

import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
import sys

SENDER = "bakerstreetbandit@zohomail.eu"
PASSWORD = "XhFm39wuR9zs"
RESUME = "/home/kilisan/resume.pdf"

applications = [
    {
        "to": "contact@twipemobile.com",
        "subject": "Application: Young Graduate Software Engineer - Kiliaan Vanvoorden",
        "cover": "/home/kilisan/cover-letter-twipe.md",
        "company": "Twipe",
    },
    {
        "to": "info@leadtech.com",
        "subject": "Application: AI Full Stack Developer - Kiliaan Vanvoorden",
        "cover": "/home/kilisan/cover-letter-leadtech-ai-v2.md",
        "company": "Leadtech (via info@)",
    },
    {
        "to": "info@nviso.eu",
        "subject": "Application: Software Engineer - Kiliaan Vanvoorden",
        "cover": "/home/kilisan/cover-letter-nviso.md",
        "company": "NVISO (via info@)",
    },
    {
        "to": "jobs@camco.be",
        "subject": "Application: Graduate Software Engineer - Kiliaan Vanvoorden",
        "cover": "/home/kilisan/cover-letter-camco.md",
        "company": "Camco",
    },
    {
        "to": "laurent.plasman@arcelormittal.com",
        "subject": "Application: Data Science NLP & GenAI Internship - Kiliaan Vanvoorden",
        "cover": "/home/kilisan/cover-letter-arcelormittal.md",
        "company": "ArcelorMittal (via Laurent Plasman)",
    },
    {
        "to": "barbara.bulius@ericsson.com",
        "subject": "Application: Technology & Systems Summer Internship - Kiliaan Vanvoorden",
        "cover": "/home/kilisan/cover-letter-ericsson.md",
        "company": "Ericsson (via Barbara Bulius)",
    },
    {
        "to": "bakerstreetbandit@zohomail.eu",
        "subject": "TEST - Please ignore",
        "cover": None,
        "company": "SELF TEST",
    },
]


def send_email(to, subject, body_path=None, body_text=None):
    msg = MIMEMultipart()
    msg["From"] = SENDER
    msg["To"] = to
    msg["Subject"] = subject

    if body_path:
        with open(body_path) as f:
            body = f.read()
    elif body_text:
        body = body_text
    else:
        body = ""

    msg.attach(MIMEText(body, "plain", "utf-8"))

    if os.path.exists(RESUME):
        with open(RESUME, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f'attachment; filename="Kiliaan_Vanvoorden_CV.pdf"',
            )
            msg.attach(part)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.zoho.eu", 465, context=context) as server:
        server.login(SENDER, PASSWORD)
        server.send_message(msg)


def test_email(to):
    """Test if email address is deliverable by sending a minimal test."""
    try:
        send_email(
            to=to,
            subject="TEST from bakerstreetbandit@zohomail.eu",
            body_text="This is a connectivity test. Please ignore.",
        )
        return True
    except Exception as e:
        return False


print("=" * 60)
print("SENDING APPLICATIONS VIA ZOHO SMTP")
print("=" * 60)

# Step 1: Test connection with self
print("\n[1/2] Testing SMTP connection...")
try:
    send_email(
        to=SENDER,
        subject="Test - SMTP connection check",
        body_text="If you receive this, SMTP is working.",
    )
    print("  ✓ SMTP connection OK (self-test sent)")
except Exception as e:
    print(f"  ✗ SMTP connection FAILED: {e}")
    sys.exit(1)

# Step 2: Send applications
print("\n[2/2] Sending applications...")
results = []
for app in applications:
    if app["to"] == SENDER:
        continue  # skip self-test in actual send

    company = app["company"]
    to = app["to"]
    subject = app["subject"]
    cover = app.get("cover")

    print(f"\n  → {company} <{to}>")
    print(f"    Subject: {subject}")

    # Check cover letter exists
    if cover and not os.path.exists(cover):
        print(f"    ✗ SKIPPED: cover letter not found at {cover}")
        results.append((company, to, "skipped - no cover letter"))
        continue

    try:
        send_email(to=to, subject=subject, body_path=cover)
        print(f"    ✓ SENT")
        results.append((company, to, "sent"))
    except smtplib.SMTPRecipientsRefused as e:
        print(f"    ✗ REJECTED: recipient refused - {e}")
        results.append((company, to, f"rejected: {e}"))
    except smtplib.SMTPResponseException as e:
        print(f"    ✗ SMTP ERROR: {e.smtp_code} - {e.smtp_error}")
        results.append((company, to, f"smtp error: {e.smtp_code}"))
    except Exception as e:
        print(f"    ✗ FAILED: {e}")
        results.append((company, to, f"failed: {e}"))

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
for company, to, status in results:
    icon = "✓" if status == "sent" else "✗"
    print(f"  {icon} {company}: {to} → {status}")
print("=" * 60)
