#!/usr/bin/env python3
"""Automated AI job application tool using Playwright + Zoho SMTP fallback."""

import json
import os
import re
import sys
import smtplib
import ssl
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

PROFILE_PATH = "/home/kilisan/ats_applicant_profile.json"
RESUME_PATH = "/home/kilisan/resume.pdf"
SMTP_HOST = "smtp.zoho.eu"
SMTP_PORT = 465
SMTP_USER = "bakerstreetbandit@zohomail.eu"
SMTP_PASS = "XhFm39wuR9zs"

with open(PROFILE_PATH) as f:
    profile = json.load(f)

JOBS = [
    {
        "company": "Ruby Labs",
        "url": "https://jobs.ashbyhq.com/ruby-labs/04d181c6-eb35-46c3-a474-e46e4f7b6767",
        "ats": "ashby",
        "email": None,
        "cover_letter": "/home/kilisan/cover-letter-ruby-labs.md",
    },
    {
        "company": "Unframe",
        "url": "https://job-boards.eu.greenhouse.io/unframe/jobs/4944222101",
        "ats": "greenhouse",
        "email": None,
        "cover_letter": "/home/kilisan/cover-letter-unframe.md",
    },
    {
        "company": "Poolside",
        "url": "https://poolside.ai/careers/member-of-engineering-agent-experience--3253bd83-7ae2-42e8-9ac0-56d1e9ccbc6c",
        "ats": "ashby",
        "email": None,
        "cover_letter": "/home/kilisan/cover-letter-poolside.md",
    },
    {
        "company": "Plain Concepts",
        "url": "https://apply.workable.com/plainconcepts/j/1C5A7AE862/apply/",
        "ats": "workable",
        "email": None,
        "cover_letter": "/home/kilisan/cover-letter-plain-concepts.md",
    },
    {
        "company": "Tether",
        "url": "https://careers.tether.io/o/engagement-manager-ai-implementations-19",
        "ats": "recruitee",
        "email": None,
        "cover_letter": "/home/kilisan/cover-letter-tether.md",
    },
]


def send_email(to, subject, body_text=None, body_path=None):
    msg = MIMEMultipart()
    msg["From"] = SMTP_USER
    msg["To"] = to
    msg["Subject"] = subject
    if body_path and os.path.exists(body_path):
        with open(body_path) as f:
            body_text = f.read()
    if not body_text:
        body_text = profile.get("cover_letter", "")
    msg.attach(MIMEText(body_text, "plain", "utf-8"))
    if os.path.exists(RESUME_PATH):
        with open(RESUME_PATH, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                'attachment; filename="Kiliaan_Vanvoorden_CV.pdf"',
            )
            msg.attach(part)
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
    return True


def try_submit(page):
    submit_selectors = [
        'button[type="submit"]',
        'input[type="submit"]',
        'button:has-text("Submit")',
        'button:has-text("Apply")',
        'button:has-text("Send")',
    ]
    for selector in submit_selectors:
        try:
            btn = page.locator(selector).first
            if btn.count() > 0 and btn.is_visible():
                btn.click()
                page.wait_for_timeout(3000)
                return True
        except Exception:
            pass
    return False


def try_submit_in_frame(page, iframe_locator):
    submit_selectors = [
        'button[type="submit"]',
        'input[type="submit"]',
        'button:has-text("Submit")',
        'button:has-text("Apply")',
        'button:has-text("Send")',
    ]
    for selector in submit_selectors:
        try:
            btn = iframe_locator.locator(selector).first
            if btn.count() > 0 and btn.is_visible():
                btn.click()
                page.wait_for_timeout(3000)
                return True
        except Exception:
            pass
    return False


def fill_greenhouse(page, url, cover_letter_path=None):
    page.goto(url, wait_until="networkidle", timeout=60000)
    time.sleep(2)
    try:
        page.get_by_role("button", name=re.compile("apply", re.I)).first.click(timeout=5000)
        time.sleep(3)
    except Exception:
        pass
    page.wait_for_selector('input[type="text"], input[type="email"], textarea', timeout=30000)
    fields = page.query_selector_all('input[type="text"], input[type="email"], textarea, input[type="tel"]')
    text_map = {
        "first": profile["first_name"],
        "last": profile["last_name"],
        "email": profile["email"],
        "phone": profile["phone"],
        "location": profile["location"],
        "linkedin": profile["linkedin"],
        "github": profile["github"],
        "portfolio": profile["portfolio"],
    }
    for field in fields:
        try:
            name_attr = (field.get_attribute("name") or "").lower()
            id_attr = (field.get_attribute("id") or "").lower()
            placeholder = (field.get_attribute("placeholder") or "").lower()
            label_text = ""
            label_el = field.evaluate("""el => {
                const labels = Array.from(document.querySelectorAll('label'));
                const l = labels.find(x => x.contains(el));
                return l ? l.textContent.trim() : '';
            }""")
            blob = " ".join([name_attr, id_attr, placeholder, label_text])
            if any(k in blob for k in ["first"]) and not any(k in blob for k in ["last", "family", "surname"]):
                field.fill(text_map["first"])
            elif any(k in blob for k in ["last", "family", "surname"]):
                field.fill(text_map["last"])
            elif any(k in blob for k in ["email"]) or field.get_attribute("type") == "email":
                field.fill(text_map["email"])
            elif any(k in blob for k in ["phone", "tel"]) or field.get_attribute("type") == "tel":
                field.fill(text_map["phone"])
            elif any(k in blob for k in ["location", "city", "address"]):
                field.fill(text_map["location"])
            elif any(k in blob for k in ["linkedin"]):
                field.fill("https://" + text_map["linkedin"])
            elif any(k in blob for k in ["github"]):
                field.fill("https://" + text_map["github"])
            elif any(k in blob for k in ["portfolio", "website"]):
                field.fill("https://" + text_map["portfolio"])
            elif any(k in blob for k in ["message", "cover", "letter", "about", "introduction"]):
                if cover_letter_path and os.path.exists(cover_letter_path):
                    with open(cover_letter_path) as f:
                        field.fill(f.read())
        except Exception:
            pass
    page.keyboard.press("Tab")
    time.sleep(1)
    try:
        page.locator('input[type="file"]').first.set_input_files(RESUME_PATH)
    except Exception:
        pass
    page.screenshot(path=f"/tmp/playwright_{int(time.time())}.png", full_page=False)
    submitted = try_submit(page)
    return submitted


def fill_workable(page, url, cover_letter_path=None):
    page.goto(url, wait_until="networkidle", timeout=60000)
    time.sleep(2)
    try:
        page.get_by_role("button", name="Accept all").click(timeout=5000)
        page.wait_for_timeout(2000)
    except Exception:
        pass
    page.wait_for_selector('input[type="text"], input[type="email"], textarea', timeout=30000)
    fields = page.query_selector_all('input[type="text"], input[type="email"], textarea, input[type="tel"]')
    for field in fields:
        try:
            blob = " ".join([
                (field.get_attribute("name") or "").lower(),
                (field.get_attribute("placeholder") or "").lower(),
            ])
            if "first" in blob and "last" not in blob:
                field.fill(profile["first_name"])
            elif "last" in blob:
                field.fill(profile["last_name"])
            elif "email" in blob or field.get_attribute("type") == "email":
                field.fill(profile["email"])
            elif "phone" in blob or field.get_attribute("type") == "tel":
                field.fill(profile["phone"])
            elif any(k in blob for k in ["location", "city"]):
                field.fill(profile["location"])
            elif "linkedin" in blob:
                field.fill("https://" + profile["linkedin"])
            elif "github" in blob:
                field.fill("https://" + profile["github"])
            elif any(k in blob for k in ["website", "portfolio"]):
                field.fill("https://" + profile["portfolio"])
            elif any(k in blob for k in ["message", "cover", "letter", "about", "introduction"]):
                if cover_letter_path and os.path.exists(cover_letter_path):
                    with open(cover_letter_path) as f:
                        field.fill(f.read())
        except Exception:
            pass
    try:
        page.locator('input[type="file"]').first.set_input_files(RESUME_PATH)
    except Exception:
        pass
    page.screenshot(path=f"/tmp/playwright_{int(time.time())}.png", full_page=False)
    submitted = try_submit(page)
    return submitted


def fill_recruitee(page, url, cover_letter_path=None):
    page.goto(url, wait_until="networkidle", timeout=60000)
    time.sleep(2)
    try:
        page.get_by_role("button", name="Apply").first.click(timeout=5000)
        time.sleep(2)
    except Exception:
        pass
    page.wait_for_selector('input[type="text"], input[type="email"], textarea', timeout=30000)
    name_parts = profile["first_name"].split(" ")
    first_name = name_parts[0]
    last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else profile["last_name"]
    name_map = {
        "candidate.name": first_name + " " + last_name,
        "candidate.firstName": first_name,
        "candidate.lastName": last_name,
        "candidate.email": profile["email"],
        "candidate.phone": profile["phone"],
        "candidate.cv": None,
        "candidate.coverLetterFile": None,
    }
    for name, value in name_map.items():
        try:
            field = page.locator(f'[name="{name}"]').first
            if field.count() == 0:
                continue
            if name == "candidate.cv":
                field.set_input_files(RESUME_PATH)
            elif name == "candidate.coverLetterFile":
                if cover_letter_path and os.path.exists(cover_letter_path):
                    field.set_input_files(cover_letter_path)
            else:
                field.fill(value)
        except Exception:
            pass
    try:
        page.locator('input[type="file"]').first.set_input_files(RESUME_PATH)
    except Exception:
        pass
    page.screenshot(path=f"/tmp/playwright_{int(time.time())}.png", full_page=False)
    submitted = try_submit(page)
    return submitted


def fill_ashby(page, url, cover_letter_path=None):
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    time.sleep(2)
    try:
        apply_btn = page.get_by_role("button", name=re.compile("apply", re.I)).first
        if apply_btn.count() > 0:
            apply_btn.click(timeout=5000)
            time.sleep(3)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    try:
        iframe = None
        try:
            iframe = page.frame_locator('iframe[src*="ashbyhq.com"]')
            if iframe.locator('input, textarea').count() == 0:
                iframe = None
        except Exception:
            iframe = None
        
        if iframe is None:
            if page.locator('input, textarea').count() == 0:
                print("  ✗ Ashby form not found")
                return False
            target = page
        else:
            target = iframe
        
        name_field = target.locator('[name="_systemfield_name"]').first
        email_field = target.locator('[name="_systemfield_email"]').first
        if name_field.count() > 0:
            name_field.fill(profile["first_name"] + " " + profile["last_name"])
        if email_field.count() > 0:
            email_field.fill(profile["email"])
        try:
            target.locator('input[type="file"]').first.set_input_files(RESUME_PATH)
        except Exception:
            pass
        page.screenshot(path=f"/tmp/playwright_{int(time.time())}.png", full_page=False)
        if iframe is not None:
            submitted = try_submit_in_frame(page, iframe)
        else:
            submitted = try_submit(page)
        return submitted
    except Exception as e:
        print(f"  ✗ Ashby error: {e}")
        return False


def fill_custom(page, url, cover_letter_path=None):
    page.goto(url, wait_until="networkidle", timeout=60000)
    time.sleep(2)
    try:
        apply_btn = page.get_by_role("link", name=re.compile("apply", re.I)).first
        if apply_btn.count() == 0:
            apply_btn = page.get_by_role("button", name=re.compile("apply", re.I)).first
        if apply_btn.count() > 0:
            apply_btn.click()
            time.sleep(3)
    except Exception:
        pass
    page.wait_for_selector('input[type="text"], input[type="email"], textarea', timeout=30000)
    fields = page.query_selector_all('input[type="text"], input[type="email"], textarea, input[type="tel"]')
    for field in fields:
        try:
            blob = " ".join([
                (field.get_attribute("name") or "").lower(),
                (field.get_attribute("placeholder") or "").lower(),
            ])
            if "name" in blob and "email" not in blob:
                field.fill(profile["first_name"] + " " + profile["last_name"])
            elif "email" in blob or field.get_attribute("type") == "email":
                field.fill(profile["email"])
            elif "phone" in blob or field.get_attribute("type") == "tel":
                field.fill(profile["phone"])
            elif any(k in blob for k in ["message", "cover", "letter", "about"]):
                if cover_letter_path and os.path.exists(cover_letter_path):
                    with open(cover_letter_path) as f:
                        field.fill(f.read())
                else:
                    field.fill(profile.get("cover_letter", ""))
        except Exception:
            pass
    try:
        page.locator('input[type="file"]').first.set_input_files(RESUME_PATH)
    except Exception:
        pass
    page.screenshot(path=f"/tmp/playwright_{int(time.time())}.png", full_page=False)
    submitted = try_submit(page)
    return submitted


def main():
    print("=" * 60)
    print("AUTOMATED AI JOB APPLICATIONS")
    print("=" * 60)
    print(f"Profile: {profile['first_name']} {profile['last_name']} | {profile['email']}")
    print(f"Resume: {RESUME_PATH}")
    print()

    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path="/usr/lib/chromium/chromium")
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        page = context.new_page()

        for job in JOBS:
            company = job["company"]
            url = job["url"]
            ats = job["ats"]
            cover_letter_path = job.get("cover_letter")
            print(f"\n→ {company}: {url}")
            try:
                if ats == "greenhouse":
                    ok = fill_greenhouse(page, url, cover_letter_path=cover_letter_path)
                elif ats == "workable":
                    ok = fill_workable(page, url, cover_letter_path=cover_letter_path)
                elif ats == "recruitee":
                    ok = fill_recruitee(page, url, cover_letter_path=cover_letter_path)
                elif ats == "ashby":
                    ok = fill_ashby(page, url, cover_letter_path=cover_letter_path)
                else:
                    ok = fill_custom(page, url, cover_letter_path=cover_letter_path)
                if ok:
                    print(f"  ✓ Form filled and submitted")
                    results.append((company, "submitted"))
                else:
                    print(f"  ✓ Form filled. Screenshot saved to /tmp/playwright_*.png")
                    results.append((company, "form_filled"))
            except PlaywrightTimeout:
                print(f"  ✗ Timeout loading page")
                results.append((company, "timeout"))
            except Exception as e:
                print(f"  ✗ Error: {e}")
                results.append((company, f"error: {e}"))

        browser.close()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for company, status in results:
        print(f"  {company}: {status}")
    print("=" * 60)


if __name__ == "__main__":
    main()
