import requests
import smtplib
import os
from email.mime.text import MIMEText
from datetime import date

# Config: set these as GitHub Secrets or env vars
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_TO = os.getenv("EMAIL_TO")

STATE_FILE = "last_seen_id.txt"

API_URL = "https://api.oireachtas.ie/v1/parliamentaryquestions"
SEARCH_TERM = "join family visa"

def get_latest_questions():
    today = date.today().isoformat()
    url = f"{API_URL}?q={SEARCH_TERM}&date_start={today}&date_end={today}"
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()
    return data.get("results", [])

def load_last_seen():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return f.read().strip()
    return None

def save_last_seen(q_id):
    with open(STATE_FILE, "w") as f:
        f.write(q_id)

def send_email(subject, body):
    msg = MIMEText(body, "plain")
    msg["From"] = EMAIL_USER
    msg["To"] = EMAIL_TO
    msg["Subject"] = subject

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, EMAIL_TO, msg.as_string())

def main():
    last_seen = load_last_seen()
    new_items = []

    questions = get_latest_questions()
    for item in questions:
        pq_id = item.get("parliamentaryQuestionId")
        if last_seen is None or pq_id != last_seen:
            new_items.append(item)

    if new_items:
        latest_id = new_items[0].get("parliamentaryQuestionId")
        save_last_seen(latest_id)

        body_lines = []
        for q in new_items:
            pq_id = q.get("parliamentaryQuestionId")
            pq_date = q.get("date")
            title = q.get("parliamentaryQuestionType", "")
            link = f"https://www.oireachtas.ie/en/debates/question/{pq_id}"
            body_lines.append(f"- {pq_date}: {title} ({link})")

        body = "\n".join(body_lines)
        send_email("New Join Family Visa PQs", body)

if __name__ == "__main__":
    main()
