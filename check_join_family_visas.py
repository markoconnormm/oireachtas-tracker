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
    resp = requests.get(SEARCH_URL, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    results = []
    for item in soup.select(".result-item"):  # class used in search results
        link_tag = item.select_one("a")
        if not link_tag:
            continue
        link = "https://www.oireachtas.ie" + link_tag["href"]
        title = link_tag.get_text(strip=True)
        date_tag = item.select_one(".result-date")
        date = date_tag.get_text(strip=True) if date_tag else "Unknown date"

        # Use the PQ link as a unique ID
        pq_id = link
        results.append({"id": pq_id, "title": title, "date": date, "link": link})

    return results

def load_last_seen():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return f.read().strip()
    return None

def save_last_seen(pq_id):
    with open(STATE_FILE, "w") as f:
        f.write(pq_id)

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
    results = fetch_pqs()

    if not results:
        return

    # Assume newest is first on page
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

if __name__ == "__main__":
    main()
