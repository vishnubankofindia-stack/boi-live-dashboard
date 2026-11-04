# BOI Live Banking Dashboard (Free GitHub Pages)

This starter project creates a mobile-friendly blue/white BOI information dashboard and a weekly official-source change monitor.

## What is automated
- Every Monday at 08:00 India time, GitHub Actions checks the official BOI interest-rate hub, loan-services page and credit-card page.
- It hashes the pages and linked BOI PDFs and records whether the source files changed since the previous check.
- The dashboard reads `data/report.json` and displays the last check, source-change status and official document links.
- Manual check: open the repository's **Actions → BOI weekly source check → Run workflow**.

## Important limitation
This first version detects page/PDF changes; it does **not** reliably extract every numerical rate or card fee from every PDF, and does not claim that a detected file change is a verified rate change. Verify effective dates and figures in the BOI source documents before relying on them. A future parser can be added for each stable BOI rate-sheet format after validation.

## Deploy to free GitHub Pages
1. Create a **public** GitHub repository named `boi-live-dashboard`.
2. Upload all files/folders from this kit to the repository root (keep `.github/workflows/` and `scripts/` folders).
3. In `index.html`, replace `YOUR_GITHUB_USERNAME/boi-live-dashboard` with your actual GitHub username and repository name.
4. Open **Settings → Pages**. Under **Build and deployment → Source**, select **GitHub Actions**.
5. Open **Actions → BOI weekly source check → Run workflow** once to create the first source report.
6. The Pages website URL will be `https://YOUR_GITHUB_USERNAME.github.io/boi-live-dashboard/`.

GitHub Pages sites in public repositories are publicly accessible. Do not put private customer data or bank credentials in this repository.

## Official sources monitored
- https://bankofindia.bank.in/interest-rate
- https://bankofindia.bank.in/loan-services
- https://bankofindia.bank.in/credit-card/

Independent reference tool. Not affiliated with or endorsed by Bank of India.
