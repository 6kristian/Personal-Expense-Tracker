# Personal Expense Tracker

![Python](https://img.shields.io/badge/python-3.11-blue)
![Flask](https://img.shields.io/badge/web-flask-green)
![SQLite](https://img.shields.io/badge/db-sqlite-lightgrey)
![Docker](https://img.shields.io/badge/run-docker-2496ed)

Flask + SQLite web app that lets users register, log in, add/view/edit/delete expenses, see spending summaries, and back-up/restore their data.
HOSTING LIVE: https://personal-expense-tracker-enzs.onrender.com/landing
## Quick start
```bash
python -m venv venv
venv\Scripts\activate   # mac/linux: source venv/bin/activate
pip install flask flask-mail
python app.py

Browse to http://127.0.0.1:5000
```

### ✨ Core Features
- 🧾 **Report Automation** – Generate and email personalized monthly expense PDFs automatically.  
- 🛡️ **Data Integrity** – Verify database schemas and perform scheduled backups for safety.  
- ☁️ **Cloud Integration** – Seamlessly interact with Google Drive via OAuth for secure storage.  
- 🌐 **Web Interface** – Built with Flask, featuring expense entry, registration, and visualization.  
- ⚙️ **Developer Friendly** – Modular codebase, schema management, and deployment setup.  

---
## 🛠️ Getting Started

### 📋 Prerequisites
Make sure you have the following installed:  
- **Python 3.x**  
- **pip** (Python package manager)  

---
### ⚙️ Installation
Clone the repository and install dependencies:

```bash
# Clone the repo
git clone https://github.com/6kristian/Personal-Expense-Tracker

# Navigate to project folder
cd Personal-Expense-Tracker

# Install dependencies
pip install -r requirements.txt
```

Monthly PDF Report Feature – Complete Docs Pack
(copy/paste into README, wiki, or GitHub release notes)
1. What it does
Every 1-st of the month at 08:00 the app automatically:
Collects last month’s expenses for every user that has an e-mail address.
Builds a 1-page PDF (category table + total).
E-mails the PDF as attachment to the user without any human click.
<img width="778" height="443" alt="image" src="https://github.com/user-attachments/assets/7e0366e4-f3b5-4e70-8ec2-9851f44bb654" />

Q: I didn’t receive the e-mail.
A: Check spam. Ensure you added your address in Settings → Profile → E-mail.
Server logs: docker logs -f container or console where python app.py runs.
Q: Can I pick my own day?
A: Not yet UI-side; open app.py, edit the cron line, restart.
Q: PDF shows zero lines.
A: You had no expenses in that month – add one dated inside the range.
Q: Can I export older months?
A: Run manually:
```
bash
python -c "from monthly_report import job_monthly_reports; job_monthly_reports()"
```
Developer notes
WeasyPrint on Windows needs GTK3 runtime or the no-GTK wheel.
APScheduler is thread-safe with Flask context pushed inside the job.
Mail errors are printed to stdout (container / systemd journal).
PDF byte-stream is held in memory (io.BytesIO) – no temp files.
Unit-test friendly: all pure functions, no I/O in last_month_range(), generate_pdf().



