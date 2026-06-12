# backend/notifier.py

import os
import smtplib
import requests
import schedule
import time
from email.mime.text import MIMEText
from datetime import datetime
from dotenv import load_dotenv

from gmail_connect import fetch_recent_emails
from scorer import get_final_priority

# Load environment variables from .env file in project root
current_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(current_dir, '..', '.env'))

# Configuration variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_APP_PASSWORD = os.getenv("SENDER_APP_PASSWORD")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")


# ── Function 1: Email digest notification ────────────────────
def send_digest(important_emails, to_email=None):
    if not to_email:
        to_email = RECEIVER_EMAIL or SENDER_EMAIL

    if not SENDER_EMAIL or not SENDER_APP_PASSWORD or not to_email:
        print("⚠️ Email credentials or recipient not configured in .env. Skipping email digest.")
        return

    body = "Your important emails today:\n\n"
    for em in important_emails:
        body += f"• [{em['priority']}] {em['subject']}\n"
        if em['deadline']:
            body += f"  ⚠️ Deadline: {em['deadline'].strftime('%d %b %Y')}\n"
        body += "\n"

    msg = MIMEText(body)
    msg['Subject'] = f"📬 Smart Filter: {len(important_emails)} important emails"
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_email

    try:
        # Send via Gmail SMTP
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
            smtp.send_message(msg)
        print("✅ Email digest sent!")
    except Exception as e:
        print(f"❌ Failed to send email digest: {e}")


# ── Function 2: Telegram notification ────────────────────────
def send_telegram_alert(message):
    if not TELEGRAM_BOT_TOKEN or not CHAT_ID:
        print("⚠️ Telegram Bot Token or Chat ID not configured in .env. Skipping Telegram alert.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        response = requests.post(url, json={
            "chat_id": CHAT_ID,
            "text": message
        }, timeout=10)
        if response.status_code == 200:
            print("✅ Telegram alert sent!")
        else:
            print(f"❌ Failed to send Telegram alert: HTTP {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error sending Telegram alert: {e}")


# ── Function 3: Format the alert message ─────────────────────
def format_alert(important_emails):
    msg = "📬 Smart Email Filter Alert!\n\n"
    for em in important_emails:
        msg += f"🔴 [{em['priority']}] {em['subject']}\n"
        msg += f"   From: {em['from']}\n"
        if em['deadline']:
            msg += f"   ⚠️ Deadline: {em['deadline'].strftime('%d %b %Y')}\n"
        msg += "\n"
    return msg


# ── Function 4: Main email check job ─────────────────────────
def run_email_check():
    print(f"🔍 Checking emails at {datetime.now().strftime('%H:%M')}...")
    try:
        emails = fetch_recent_emails()
    except Exception as e:
        print(f"❌ Error fetching emails: {e}")
        return

    important = []
    for em in emails:
        try:
            result = get_final_priority(em)
            if result['priority'] in ['HIGH', 'MEDIUM']:
                important.append({**em, **result})
        except Exception as e:
            print(f"⚠️ Error scoring email '{em.get('subject', 'Unknown')}': {e}")

    if important:
        alert_msg = format_alert(important)
        send_telegram_alert(alert_msg)
        
        # Optionally send email digest if configured
        if SENDER_EMAIL and SENDER_APP_PASSWORD and (RECEIVER_EMAIL or SENDER_EMAIL):
            send_digest(important)
            
        print(f"📨 Found {len(important)} important emails!")
    else:
        print("✅ No important emails right now.")


# ── Scheduler: runs every 2 hours automatically ──────────────
if __name__ == "__main__":
    print("🚀 Smart Email Filter running...")
    run_email_check()  # run once immediately on start

    schedule.every(2).hours.do(run_email_check)

    while True:
        schedule.run_pending()
        time.sleep(60)