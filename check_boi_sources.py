import hashlib, json, re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

BASE = Path(__file__).resolve().parent
REPORT, STATE = BASE / "report.json", BASE / "state.json"
SOURCES = [
    ("BOI Interest Rate Hub", "https://bankofindia.bank.in/interest-rate"),
    ("BOI Loan Services", "https://bankofindia.bank.in/loan-services"),
    ("BOI Credit Cards", "https://bankofindia.bank.in/credit-card/"),
]
session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0 (compatible; BOI-Info-Monitor/1.0)"})

def sha(data): return hashlib.sha256(data).hexdigest()

def main():
    old = json.loads(STATE.read_text()) if STATE.exists() else {}
    new, rows, errors, changed = {}, [], [], False
    for title, url in SOURCES:
        try:
            r = session.get(url, timeout=35); r.raise_for_status()
            h = sha(r.content); prev = old.get(url, {}).get("sha256")
            status = "Changed since previous check" if prev and prev != h else ("First baseline captured" if not prev else "No change")
            changed |= bool(prev and prev != h)
            new[url] = {"sha256": h}
            rows.append({"title": title, "url": url, "kind": "Official BOI page", "status": status})
            soup = BeautifulSoup(r.content, "html.parser")
            seen = set()
            for a in soup.find_all("a", href=True):
                pdfurl = urljoin(url, a["href"])
                if urlparse(pdfurl).netloc not in {"bankofindia.bank.in", "www.bankofindia.bank.in"}: continue
                if not re.search(r"\.pdf(?:$|\?)", pdfurl, re.I) or pdfurl in seen: continue
                seen.add(pdfurl)
                try:
                    pr = session.get(pdfurl, timeout=35); pr.raise_for_status()
                    ph = sha(pr.content); op = old.get(pdfurl, {}).get("sha256")
                    ps = "Changed since previous check" if op and op != ph else ("First baseline captured" if not op else "No change")
                    changed |= bool(op and op != ph); new[pdfurl] = {"sha256": ph}
                    label = " ".join(a.get_text(" ", strip=True).split()) or Path(urlparse(pdfurl).path).name
                    rows.append({"title": label[:140], "url": pdfurl, "kind": "BOI PDF/document", "status": ps})
                except Exception as e: errors.append(f"PDF check failed: {pdfurl}: {e}")
        except Exception as e: errors.append(f"Page check failed: {url}: {e}")
    for k,v in old.items(): new.setdefault(k,v)
    STATE.write_text(json.dumps(new, indent=2))
    summary = ("BOI source page/document changes detected. Verify the exact figures and effective date in the official source."
               if changed else "No source changes detected, or this is the first baseline. This monitor detects document changes; it does not certify all interest rates.")
    if errors: summary += " Some sources could not be checked; see GitHub Actions logs."
    REPORT.write_text(json.dumps({"checked_at": datetime.now(timezone.utc).isoformat(), "change_detected": changed,
                                  "summary": summary, "sources": rows, "errors": errors}, indent=2))
    print(summary)
    for e in errors: print(e)

if __name__ == "__main__": main()
