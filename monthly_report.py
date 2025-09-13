
import datetime, pathlib, sqlite3, io
from weasyprint import HTML
from flask_mail import Message
from app import app, mail, get_conn   # reuse Flask app context

def last_month_range():
    """Return (first_day, last_day) of previous month."""
    today = datetime.date.today()
    first_this = today.replace(day=1)
    last_prev  = first_this - datetime.timedelta(days=1)
    first_prev = last_prev.replace(day=1)
    return first_prev, last_prev

def fetch_summary(user_id, d_from, d_to):
    sql = """
        SELECT category, SUM(amount) as total, COUNT(*) as cnt
        FROM expenses
        WHERE user_id = ? AND date BETWEEN ? AND ?
        GROUP BY category
        ORDER BY total DESC
    """
    with get_conn() as conn:
        return conn.execute(sql, (user_id, d_from, d_to)).fetchall()

def generate_pdf(username, rows, period):
    """Return bytes of a simple PDF."""
    total = sum(r["total"] for r in rows)
    html = f"""
    <html>
    <head><style>
        body{{font-family:Arial,Helvetica,sans-serif;margin:2cm}}
        h1{{color:#0d6efd}}table{{width:100%;border-collapse:collapse}}th,td{{padding:8px;border:1px solid #ccc}}
        .right{{text-align:right}}.bold{{font-weight:bold}}
    </style></head>
    <body>
        <h1>Monthly expense report – {period}</h1>
        <p>Hello {username},</p>
        <p>Here is your spending summary for {period}:</p>
        <table>
          <thead><tr><th>Category</th><th class=right>Amount</th><th class=right>Transactions</th></tr></thead>
          <tbody>
            {''.join(f"<tr><td>{r['category']}</td><td class=right>${r['total']:.2f}</td><td class=right>{r['cnt']}</td></tr>" for r in rows)}
          </tbody>
          <tfoot><tr class=bold><td>TOTAL</td><td class=right>${total:.2f}</td><td class=right>{sum(r['cnt'] for r in rows)}</td></tr></tfoot>
        </table>
    </body></html>"""
    return HTML(string=html).write_pdf()

def send_report(user, pdf_bytes, period):
    subject = f"Your expense report – {period}"
    msg = Message(subject=subject,
                  recipients=[user["email"]],
                  body=f"Hi {user['username']},\n\nPlease find your monthly expense report attached.\n\nBest regards,\nPersonal Expense Tracker")
    msg.attach("expense_report.pdf", "application/pdf", pdf_bytes)
    mail.send(msg)

def job_monthly_reports():
    first, last = last_month_range()
    period = f"{first:%B %Y}"
    print(f"[DEBUG] checking period {first} → {last}")
    with app.app_context():
        users = get_conn().execute("SELECT id, username, email FROM users WHERE email IS NOT NULL").fetchall()
        print(f"[DEBUG] users with e-mail: {len(users)}")
        for u in users:
            rows = fetch_summary(u["id"], first, last)
            print(f"[DEBUG] {u['username']} has {len(rows)} categories")
            if not rows:
                continue
            pdf = generate_pdf(u["username"], rows, period)
            print(f"[DEBUG] PDF size {len(pdf)} bytes for {u['email']}")

            # --- temp: let mail errors show ---------------------------------
            try:
                send_report(u, pdf, period)
                print(f"[monthly-report] sent to {u['email']}")
            except Exception as e:
                print(f"[ERROR] mail to {u['email']} failed: {e}")