import hashlib, json, os, re, sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data"
DATA.mkdir(exist_ok=True)
REPORT = DATA / "report.json"
STATE = DATA / "state.json"
SOURCES = [
    ("BOI Interest Rate Hub", "https://bankofindia.bank.in/interest-rate", "interest-rates"),
    ("BOI Loan Services", "https://bankofindia.bank.in/loan-services", "loans"),
    ("BOI Credit Cards", "https://bankofindia.bank.in/credit-card/", "credit-cards"),
]
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; BOI-Info-Monitor/1.0; +https://github.com/)"}
session = requests.Session()
session.headers.update(HEADERS)

def digest(content):
    return hashlib.sha256(content).hexdigest()

def main():
    old = json.loads(STATE.read_text()) if STATE.exists() else {}
    new = {}
    results = []
    changed = False
    errors = []
    for title, url, kind in SOURCES:
        try:
            resp = session.get(url, timeout=35)
            resp.raise_for_status()
            content = resp.content
            h = digest(content)
            prev = old.get(url, {}).get("sha256")
            status = "Changed since previous check" if prev and prev != h else ("First baseline captured" if not prev else "No change")
            if prev and prev != h:
                changed = True
            new[url] = {"sha256": h, "checked_at": datetime.now(timezone.utc).isoformat()}
            results.append({"title": title, "url": url, "kind": "Official BOI page", "status": status, "sha256": h})
            soup = BeautifulSoup(content, "html.parser")
            seen = set()
            for a in soup.find_all("a", href=True):
                href = urljoin(url, a["href"])
                if urlparse(href).netloc not in {"bankofindia.bank.in", "www.bankofindia.bank.in"}:
                    continue
                if not re.search(r"\.pdf(?:$|\?)", href, re.I):
                    continue
                if href in seen: continue
                seen.add(href)
                try:
                    pdf = session.get(href, timeout=35)
                    pdf.raise_for_status()
                    ph = digest(pdf.content)
                    old_pdf = old.get(href, {}).get("sha256")
                    pstatus = "Changed since previous check" if old_pdf and old_pdf != ph else ("First baseline captured" if not old_pdf else "No change")
                    if old_pdf and old_pdf != ph: changed = True
                    new[href] = {"sha256": ph, "checked_at": datetime.now(timezone.utc).isoformat()}
                    label = " ".join(a.get_text(" ", strip=True).split()) or Path(urlparse(href).path).name
                    results.append({"title": label[:140], "url": href, "kind": "BOI PDF/document", "status": pstatus, "sha256": ph})
                except Exception as ex:
                    errors.append(f"Could not inspect linked document: {href} ({ex})")
        except Exception as ex:
            errors.append(f"Could not fetch {url}: {ex}")
    # Keep the previous state for sources that temporarily failed.
    for k, v in old.items():
        new.setdefault(k, v)
    STATE.write_text(json.dumps(new, indent=2))
    now = datetime.now(timezone.utc).isoformat()
    summary = ("One or more official pages/documents changed. Open the source documents and verify the effective date and exact rate before updating any figures."
               if changed else "No changes were detected in the monitored official pages/documents, or this was the initial baseline. This is a document-change check, not a confirmation that all rate tables are unchanged.")
    if errors: summary += " Some sources could not be checked; see workflow logs."
    REPORT.write_text(json.dumps({"checked_at": now, "change_detected": changed, "summary": summary, "sources": results, "errors": errors}, indent=2))
    print(summary)
    if errors:
        print("\n".join(errors))

if __name__ == "__main__":
    main()
