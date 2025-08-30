import requests
from bs4 import BeautifulSoup
import smtplib
import os
from email.mime.text import MIMEText

# Config: set via GitHub Secrets or env vars
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_TO = os.getenv("EMAIL_TO")

STATE_FILE = "last_seen_id.txt"

SEARCH_URL = "https://www.oireachtas.ie/en/debates/questions/?q=join+family+visa"

def fetch_pqs():
    print(f"[DEBUG] Fetching PQs from {SEARCH_URL}")
    resp = requests.get(SEARCH_URL, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    results = []
    for item in soup.select(".result-item"):
        link_tag = item.select_one("a")
        if not link_tag:
            continue
        link = "https://www.oireachtas.ie" + link_tag["href"]
        title = link_tag.get_text(strip=True)
        date_tag = item.select_one(".result-date")
        date = date_tag.get_text(strip=True) if date_tag else "Unknown date"

        pq_id = link
        results.append({"id": pq_id, "title": title, "date": date, "link": link})

    print(f"[DEBUG] Found {len(results)} PQ results")
    return results

def load_last_seen():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            value = f.read().strip()
            print(f"[DEBUG] Loaded last_seen_id: {value}")
            return value
    print("[DEBUG] No last_seen_id file found")
    return None

def save_last_seen(pq_id):
    print(f"[DEBUG] Saving last_seen_id: {pq_id}")
    with open(STATE_FILE, "w") as f:
        f.write(pq_id)

def send_email(subject, body):
    print("[DEBUG] Preparing to send email...")
    msg = MIMEText(body, "plain")
    msg["From"] = EMAIL_USER
    msg["To"] = EMAIL_TO
    msg["Subject"] = subject

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            print(f"[DEBUG] Connecting to {SMTP_SERVER}:{SMTP_PORT}")
            server.starttls()
            print("[DEBUG] Starting TLS session")
            server.login(EMAIL_USER, EMAIL_PASS)
            print("[DEBUG] Logged in to SMTP server successfully")
            server.sendmail(EMAIL_USER, EMAIL_TO, msg.as_string())
            print(f"[DEBUG] Email sent to {EMAIL_TO} with subject '{subject}'")
    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")
        raise

def main():
    last_seen = load_last_seen()
    results = fetch_pqs()

    if not results:
        print("[DEBUG] No results found — nothing to do")
        return

    new_items = []
    for r in results:
        if r["id"] == last_seen:
            break
        new_items.append(r)

    if new_items:
        latest_id = new_items[0]["id"]
        save_last_seen(latest_id)

        body_lines = []
        for r in new_items:
            body_lines.append(f"- {r['date']}: {r['title']} ({r['link']})")

        body = "\n".join(body_lines)
        send_email("New Join Family Visa PQs", body)
    else:
        print("[DEBUG] No new PQs found since last run")

if __name__ == "__main__":
    # Always send a test mail too, to confirm email setup
    send_email("Test run", "This is a test email from GitHub Actions (debug mode).")
    main()
