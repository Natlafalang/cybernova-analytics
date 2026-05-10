import hashlib, json, os, datetime, urllib.request
import psycopg2
import psycopg2.extras
from functools import wraps
from flask import (Flask, render_template, request, redirect, url_for,
                   session, jsonify, flash, g)

app = Flask(__name__)
app.secret_key = "cybernova_secret_key_2026"

DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "dbname":   "cybernova",
    "user":     "postgres",
    "password": "Leojosh@2203"
}

# ── DATABASE ───────────────────────────────────────────────────────────────────
def get_db():
    db = getattr(g, "_db", None)
    if db is None:
        db = g._db = psycopg2.connect(**DB_CONFIG)
        db.autocommit = False
    return db

def query(sql, params=None, fetchone=False, fetchall=False, commit=False):
    """Central helper — always uses a fresh cursor with RealDictCursor."""
    db = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(sql, params or ())
    result = None
    if fetchone:
        result = cur.fetchone()
    elif fetchall:
        result = cur.fetchall()
    if commit:
        db.commit()
    cur.close()
    return result

@app.teardown_appcontext
def close_db(exc):
    db = getattr(g, "_db", None)
    if db:
        if exc:
            db.rollback()
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        cur = db.cursor()

        # Create all tables
        cur.execute("""
            CREATE TABLE IF NOT EXISTS security_requests (
                id SERIAL PRIMARY KEY,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT,
                organisation TEXT,
                country TEXT,
                job_title TEXT,
                issue_type TEXT,
                description TEXT,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS testimonials (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                organisation TEXT,
                rating INTEGER NOT NULL,
                message TEXT NOT NULL,
                approved INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS blog_posts (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                author TEXT DEFAULT 'CyberNova Team',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS gallery_items (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                image_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS admins (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT DEFAULT ''
            );
        """)
        db.commit()

        # Create the three default admin accounts
        admins_list = [
            ("joshua_marapo",      "JMarapo", "Joshua Marapo"),
            ("natlafalang_marapo", "NMarapo", "Natlafalang Marapo"),
            ("thabitha_masemola",  "Ntonitoni", "Thabitha Masemola"),
        ]
        for uname, pw, fname in admins_list:
            cur.execute("SELECT id FROM admins WHERE username=%s", (uname,))
            if not cur.fetchone():
                cur.execute(
                    "INSERT INTO admins (username, password_hash, full_name) VALUES (%s, %s, %s)",
                    (uname, hashlib.sha256(pw.encode()).hexdigest(), fname)
                )
        db.commit()

        # Seed blogs
        cur.execute("SELECT COUNT(*) FROM blog_posts")
        if cur.fetchone()[0] == 0:
            blogs = [
                ("Understanding Ransomware: What Every SME Needs to Know",
                 "Ransomware attacks have surged across Southern Africa, targeting SMEs with limited cybersecurity budgets. This article explains how ransomware works, common entry points such as phishing emails and unpatched software, and practical mitigation steps including regular backups, network segmentation, and staff awareness training. CyberNova Analytics has assisted over 30 organisations in ransomware recovery and prevention planning."),
                ("Phishing Threats in the Financial Sector",
                 "Financial institutions remain the top target for phishing campaigns across Africa. Attackers use spoofed emails, fake login pages, and social engineering to harvest credentials. This post outlines the latest phishing techniques and how CyberNova's AI Cyber Assistant can detect anomalous behaviour in real time."),
                ("Top 5 Cyber Hygiene Practices for Government Agencies",
                 "Government agencies handle sensitive citizen data, making them prime targets. CyberNova recommends: multi-factor authentication, zero-trust network architecture, regular vulnerability assessments, incident response planning, and employee cybersecurity training."),
            ]
            for title, content in blogs:
                cur.execute("INSERT INTO blog_posts (title, content) VALUES (%s, %s)", (title, content))
            db.commit()

        # Seed testimonials
        cur.execute("SELECT COUNT(*) FROM testimonials")
        if cur.fetchone()[0] == 0:
            tdata = [
                ("Thabo Mokoena", "First National Bank Botswana", 5,
                 "CyberNova identified a critical vulnerability in our network within 48 hours. Their AI assistant guided our team through remediation clearly and efficiently.", 1),
                ("Naledi Sithole", "Ministry of Finance, Lesotho", 5,
                 "Outstanding service. The AI breach report gave us a complete picture of the incident within minutes. We felt fully supported throughout.", 1),
                ("James Oduya", "AfriTech SME Solutions", 4,
                 "The contact form was simple and the response was immediate. Our issue was logged and acted upon same day. Highly recommended.", 1),
            ]
            for n, o, r, m, a in tdata:
                cur.execute(
                    "INSERT INTO testimonials (name, organisation, rating, message, approved) VALUES (%s, %s, %s, %s, %s)",
                    (n, o, r, m, a)
                )
            db.commit()

        # Seed gallery
        cur.execute("SELECT COUNT(*) FROM gallery_items")
        if cur.fetchone()[0] == 0:
            gdata = [
                ("Cybersecurity Awareness Workshop — Gaborone 2025",
                 "Full-day workshop for 80 SME representatives covering phishing defence and secure password practices.",
                 "https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=600&q=80"),
                ("Network Security Training — Francistown",
                 "Two-day training for IT officers from regional government departments.",
                 "https://images.unsplash.com/photo-1573164713714-d95e436ab8d6?w=600&q=80"),
                ("AI Cyber Defence Seminar — Johannesburg",
                 "CyberNova presented at the Southern Africa Cyber Summit.",
                 "https://images.unsplash.com/photo-1591115765373-5207764f72e7?w=600&q=80"),
                ("Incident Response Simulation — Harare",
                 "Live ransomware scenario simulation and recovery exercise.",
                 "https://images.unsplash.com/photo-1504384308090-c894fdcc538d?w=600&q=80"),
            ]
            for t, d, u in gdata:
                cur.execute(
                    "INSERT INTO gallery_items (title, description, image_url) VALUES (%s, %s, %s)",
                    (t, d, u)
                )
            db.commit()

        cur.close()
        print("Database initialised successfully.")

# ── AUTH ───────────────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_logged_in"):
            flash("Please log in to access the admin panel.", "warning")
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated

# ── AI ASSISTANT ───────────────────────────────────────────────────────────────
OPENAI_KEY = ""

def ask_ai(messages, system_prompt):
    if OPENAI_KEY:
        try:
            payload = json.dumps({
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "system", "content": system_prompt}] + messages,
                "max_tokens": 500,
                "temperature": 0.7
            }).encode()
            req = urllib.request.Request(
                "https://api.openai.com/v1/chat/completions",
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {OPENAI_KEY}"
                }
            )
            with urllib.request.urlopen(req, timeout=15) as r:
                return json.loads(r.read())["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"OpenAI API Error: {e}")
    return fallback_ai(messages[-1]["content"] if messages else "", system_prompt)

def fallback_ai(msg, system_prompt):
    m = msg.lower()
    if "incident report generator" in system_prompt.lower():
        return None
    if any(w in m for w in ["ransomware", "ransom", "encrypted files", "files locked"]):
        return ("Ransomware encrypts your files and demands payment. Here is what to do immediately:\n"
                "1. Isolate the device — disconnect from the network and Wi-Fi\n"
                "2. Do NOT pay the ransom\n"
                "3. Do NOT restart the machine\n"
                "4. Submit a security request to CyberNova\n"
                "5. Restore from your last clean backup\n"
                "Would you like me to guide you to the Contact Security Team form?")
    if any(w in m for w in ["phishing", "suspicious email", "fake email", "clicked a link"]):
        return ("Phishing attacks use deceptive emails to steal credentials. Immediate steps:\n"
                "1. Do NOT click any links or open attachments\n"
                "2. Report the email to your IT department\n"
                "3. Change your password immediately\n"
                "4. Enable multi-factor authentication\n"
                "CyberNova can conduct a full phishing assessment for your organisation.")
    if any(w in m for w in ["data breach", "data leak", "data stolen", "information leaked"]):
        return ("A data breach requires immediate containment:\n"
                "1. Identify what data was exposed\n"
                "2. Revoke compromised credentials immediately\n"
                "3. Notify affected individuals and regulatory authorities\n"
                "4. Preserve all logs and evidence\n"
                "5. Submit a formal incident report to CyberNova for analysis")
    if any(w in m for w in ["password", "credentials", "account hacked", "account compromised", "breach"]):
        return ("Compromised credentials are a common attack vector:\n"
                "1. Change the affected password immediately on all accounts\n"
                "2. Enable multi-factor authentication\n"
                "3. Check account activity logs for unauthorised access\n"
                "4. Use a password manager for strong unique passwords\n"
                "CyberNova recommends a full Identity and Access Management review.")
    if any(w in m for w in ["malware", "virus", "trojan", "spyware", "infected", "suspicious software"]):
        return ("Malware is software designed to damage or gain unauthorised access:\n"
                "1. Disconnect the infected device from the network immediately\n"
                "2. Run a full scan using reputable antivirus software\n"
                "3. Do not use the device for sensitive tasks until cleared\n"
                "4. Check for recently installed unfamiliar programs\n"
                "5. Contact CyberNova for professional malware analysis and removal")
    if any(w in m for w in ["hack", "hacked", "intrusion", "unauthorised", "unauthorized", "suspicious activity"]):
        return ("A suspected intrusion requires immediate containment:\n"
                "1. Disconnect the system from the internet and internal network\n"
                "2. Do NOT shut down or wipe the system\n"
                "3. Preserve all system and event logs\n"
                "4. Change all passwords from a separate clean device\n"
                "5. Submit a formal security request to CyberNova immediately")
    if any(w in m for w in ["ddos", "denial of service", "network flooded", "website down", "server overloaded"]):
        return ("A DDoS attack floods your network to cause downtime:\n"
                "1. Contact your ISP to apply upstream traffic filtering\n"
                "2. Enable rate limiting on your web server and firewall\n"
                "3. Activate cloud DDoS protection if available\n"
                "4. Consider a CDN with built-in DDoS mitigation\n"
                "CyberNova can assist with network hardening and protection strategies.")
    if any(w in m for w in ["what can you do", "how can you help", "what are you", "capabilities"]):
        return ("I can help you with the following:\n"
                "- Explain cybersecurity threats like ransomware, phishing, DDoS and malware\n"
                "- Guide you through reporting a security incident to CyberNova\n"
                "- Provide immediate advice if your systems are under attack\n"
                "- Answer general cybersecurity questions in plain language\n"
                "What would you like help with?")
    if any(w in m for w in ["cybernova", "who are you", "about you", "services"]):
        return ("CyberNova Analytics Ltd is an AI-driven cybersecurity company based in Gaborone, Botswana. "
                "We provide threat monitoring, incident response, risk assessments and digital transformation "
                "solutions for SMEs, financial institutions and government agencies across Southern Africa. "
                "Contact our team using the Contact Security Team form on this website.")
    if any(w in m for w in ["report", "submit", "contact", "form", "how do i", "get help"]):
        return ("To report a security incident, click Contact Security Team in the navigation menu. "
                "Fill in your name, email, organisation and a description of the problem. "
                "No account is required and your request is stored immediately.")
    if any(w in m for w in ["thank", "thanks", "thank you", "appreciate"]):
        return "You are welcome! If you experience any further security concerns, do not hesitate to reach out. Stay safe!"
    if m.strip() in ["yes", "yes please", "sure", "okay", "ok", "yep"]:
        return ("You can submit your request by clicking Contact Security Team in the navigation bar. "
                "Fill in your details and describe the incident — no account is needed.")
    if m.strip() in ["no", "no thanks", "not now", "nope"]:
        return "Understood. I am always here if you need assistance later. Stay safe!"
    if any(w in m for w in ["hello", "hi", "hey", "good morning", "good afternoon", "start", "greetings"]):
        return ("Hello! I am CyberNova's AI Cyber Assistant. I can help you with cybersecurity questions, "
                "guide you through reporting an incident, or explain threats in plain language. "
                "What can I help you with today?")
    if len(m) < 12:
        return ("Could you tell me a bit more about your situation? "
                "Are you experiencing a specific threat or do you have a general cybersecurity question?")
    return ("Thank you for reaching out. Based on what you described, I recommend submitting a formal "
            "security request so an analyst can provide tailored guidance. Click Contact Security Team "
            "in the navigation bar. If you are under active attack, isolate the affected system from "
            "the network immediately and preserve all logs.")

def generate_incident_report(db):
    cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT issue_type, country, submitted_at FROM security_requests ORDER BY submitted_at DESC")
    rows = cur.fetchall()
    cur.close()
    total = len(rows)
    if total == 0:
        return "No security incidents are currently recorded in the database."
    types, countries = {}, {}
    for r in rows:
        t = r["issue_type"] or "Unspecified"
        c = r["country"] or "Unknown"
        types[t] = types.get(t, 0) + 1
        countries[c] = countries.get(c, 0) + 1
    top_t = max(types, key=types.get)
    top_c = max(countries, key=countries.get)
    now = datetime.datetime.now().strftime("%d %B %Y, %H:%M")
    lines = [
        "CYBERNOVA ANALYTICS — AI INCIDENT SUMMARY REPORT",
        f"Generated: {now}", "",
        "EXECUTIVE SUMMARY",
        f"Total incidents recorded: {total}",
        f"Most recent submission: {rows[0]['submitted_at']}", "",
        "INCIDENT TYPE BREAKDOWN",
    ]
    for k, v in sorted(types.items(), key=lambda x: -x[1]):
        lines.append(f"  {k}: {v} incident{'s' if v > 1 else ''}")
    lines += ["", "GEOGRAPHIC DISTRIBUTION"]
    for k, v in sorted(countries.items(), key=lambda x: -x[1]):
        lines.append(f"  {k}: {v} incident{'s' if v > 1 else ''}")
    lines += [
        "", "KEY FINDINGS",
        f"  Highest incident type: {top_t} ({types[top_t]} cases)",
        f"  Most affected region: {top_c} ({countries[top_c]} cases)",
        "", "RECOMMENDATIONS",
        f"  Priority focus should be placed on {top_t} threats in {top_c}.",
        "  CyberNova recommends targeted awareness training, vulnerability assessments,",
        "  and enhanced monitoring for these incident categories.",
        "", "Report generated by CyberNova AI Assistant."
    ]
    return "\n".join(lines)

# ── PUBLIC ROUTES ──────────────────────────────────────────────────────────────
@app.route("/")
def index():
    testimonials = query("SELECT * FROM testimonials WHERE approved=1 ORDER BY created_at DESC LIMIT 3", fetchall=True)
    posts = query("SELECT id,title,content,created_at FROM blog_posts ORDER BY created_at DESC LIMIT 3", fetchall=True)
    return render_template("index.html", testimonials=testimonials, posts=posts)

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        fields = ["full_name", "email", "phone", "organisation", "country", "job_title", "issue_type", "description"]
        vals = [request.form.get(f, "").strip() for f in fields]
        if not vals[0] or not vals[1]:
            flash("Full Name and Email are required.", "danger")
        else:
            query(
                "INSERT INTO security_requests (full_name,email,phone,organisation,country,job_title,issue_type,description) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                vals, commit=True
            )
            flash("Your security request has been submitted. Our team will respond shortly.", "success")
            return redirect(url_for("contact"))
    return render_template("contact.html")

@app.route("/testimonials", methods=["GET", "POST"])
def testimonials_page():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        org  = request.form.get("organisation", "").strip()
        try:
            rating = max(1, min(5, int(request.form.get("rating", 5))))
        except:
            rating = 5
        msg = request.form.get("message", "").strip()
        if name and msg:
            query(
                "INSERT INTO testimonials (name,organisation,rating,message,approved) VALUES (%s,%s,%s,%s,0)",
                (name, org, rating, msg), commit=True
            )
            flash("Thank you! Your testimonial has been submitted for review.", "success")
            return redirect(url_for("testimonials_page"))
        else:
            flash("Name and message are required.", "danger")
    items = query("SELECT * FROM testimonials WHERE approved=1 ORDER BY created_at DESC", fetchall=True)
    return render_template("testimonials.html", testimonials=items)

@app.route("/blog")
def blog():
    posts = query("SELECT * FROM blog_posts ORDER BY created_at DESC", fetchall=True)
    return render_template("blog.html", posts=posts)

@app.route("/blog/<int:pid>")
def blog_post(pid):
    post = query("SELECT * FROM blog_posts WHERE id=%s", (pid,), fetchone=True)
    return render_template("blog_post.html", post=post) if post else redirect(url_for("blog"))

@app.route("/gallery")
def gallery():
    items = query("SELECT * FROM gallery_items ORDER BY created_at DESC", fetchall=True)
    return render_template("gallery.html", items=items)

@app.route("/chat")
def chat():
    return render_template("chat.html")

@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json()
    messages = data.get("messages", [])
    system = ("You are CyberNova Analytics AI Cyber Assistant. Help public clients with cybersecurity questions, "
              "guide them to report incidents, and explain threats in plain non-technical language. "
              "Be concise, professional, and helpful. Always suggest submitting the Contact Security Team form for active incidents.")
    reply = ask_ai(messages, system) or "Ready to help. Please describe your security concern."
    return jsonify({"reply": reply})

# ── ADMIN ROUTES ───────────────────────────────────────────────────────────────
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("admin_logged_in"):
        return redirect(url_for("admin_dashboard"))
    error = None
    if request.method == "POST":
        u = request.form.get("username", "")
        p = request.form.get("password", "")
        admin = query("SELECT * FROM admins WHERE username=%s", (u,), fetchone=True)
        if admin and admin["password_hash"] == hashlib.sha256(p.encode()).hexdigest():
            session["admin_logged_in"] = True
            session["admin_username"] = u
            return redirect(url_for("admin_dashboard"))
        error = "Invalid username or password."
    return render_template("admin/login.html", error=error)

@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))
@app.route("/admin/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    msg = None
    if request.method == "POST":
        current = request.form.get("current_password", "")
        new_pw  = request.form.get("new_password", "")
        confirm = request.form.get("confirm_password", "")
        
        # Check current password is correct
        uname = session.get("admin_username")
        admin = query("SELECT * FROM admins WHERE username=%s", (uname,), fetchone=True)
        
        if admin["password_hash"] != hashlib.sha256(current.encode()).hexdigest():
            msg = ("danger", "Current password is incorrect.")
        elif new_pw != confirm:
            msg = ("danger", "New passwords do not match.")
        elif len(new_pw) < 6:
            msg = ("danger", "Password must be at least 6 characters.")
        else:
            query(
                "UPDATE admins SET password_hash=%s WHERE username=%s",
                (hashlib.sha256(new_pw.encode()).hexdigest(), uname), commit=True
            )
            msg = ("success", "Password changed successfully.")
    
    return render_template("admin/change_password.html", msg=msg)

@app.route("/admin")
@login_required
def admin_dashboard():
    total_req    = query("SELECT COUNT(*) FROM security_requests", fetchone=True)["count"]
    pending_t    = query("SELECT COUNT(*) FROM testimonials WHERE approved=0", fetchone=True)["count"]
    total_blogs  = query("SELECT COUNT(*) FROM blog_posts", fetchone=True)["count"]
    recent       = query("SELECT * FROM security_requests ORDER BY submitted_at DESC LIMIT 5", fetchall=True)
    type_data    = query("SELECT issue_type, COUNT(*) as cnt FROM security_requests GROUP BY issue_type ORDER BY cnt DESC", fetchall=True)
    country_data = query("SELECT country, COUNT(*) as cnt FROM security_requests GROUP BY country ORDER BY cnt DESC LIMIT 8", fetchall=True)
    return render_template("admin/dashboard.html",
        total_req=total_req, pending_t=pending_t, total_blogs=total_blogs,
        recent=recent, type_data=type_data, country_data=country_data)

@app.route("/admin/requests")
@login_required
def admin_requests():
    it = request.args.get("issue_type", "")
    co = request.args.get("country", "")
    df = request.args.get("date_from", "")
    dt = request.args.get("date_to", "")
    sql = "SELECT * FROM security_requests WHERE 1=1"
    params = []
    if it: sql += " AND issue_type=%s"; params.append(it)
    if co: sql += " AND country ILIKE %s"; params.append(f"%{co}%")
    if df: sql += " AND DATE(submitted_at)>=%s"; params.append(df)
    if dt: sql += " AND DATE(submitted_at)<=%s"; params.append(dt)
    sql += " ORDER BY submitted_at DESC"
    reqs  = query(sql, params, fetchall=True)
    types = query("SELECT DISTINCT issue_type FROM security_requests WHERE issue_type!=''", fetchall=True)
    return render_template("admin/requests.html", requests=reqs, issue_types=types,
        filters={"issue_type": it, "country": co, "date_from": df, "date_to": dt})

@app.route("/admin/breach-report")
@login_required
def admin_breach():
    incidents = query("SELECT * FROM security_requests ORDER BY submitted_at DESC", fetchall=True)
    monthly   = query("SELECT TO_CHAR(submitted_at,'YYYY-MM') as month, COUNT(*) as cnt FROM security_requests GROUP BY month ORDER BY month", fetchall=True)
    type_cnt  = query("SELECT issue_type, COUNT(*) as cnt FROM security_requests GROUP BY issue_type ORDER BY cnt DESC", fetchall=True)
    return render_template("admin/breach_report.html", incidents=incidents, monthly=monthly, type_cnt=type_cnt)

@app.route("/admin/analytics")
@login_required
def admin_analytics():
    type_data    = query("SELECT issue_type, COUNT(*) as cnt FROM security_requests GROUP BY issue_type ORDER BY cnt DESC", fetchall=True)
    country_data = query("SELECT country, COUNT(*) as cnt FROM security_requests GROUP BY country ORDER BY cnt DESC LIMIT 10", fetchall=True)
    monthly      = query("SELECT TO_CHAR(submitted_at,'YYYY-MM') as month, COUNT(*) as cnt FROM security_requests GROUP BY month ORDER BY month", fetchall=True)
    total        = query("SELECT COUNT(*) FROM security_requests", fetchone=True)["count"]
    return render_template("admin/analytics.html",
        type_data=type_data, country_data=country_data, monthly=monthly, total=total)

@app.route("/admin/content", methods=["GET", "POST"])
@login_required
def admin_content():
    msg = None
    if request.method == "POST":
        act = request.form.get("action")
        if act == "add_blog":
            t = request.form.get("title", "").strip()
            c = request.form.get("content", "").strip()
            if t and c:
                query("INSERT INTO blog_posts (title,content) VALUES (%s,%s)", (t, c), commit=True)
                msg = ("success", "Blog post published.")
        elif act == "approve_t":
            query("UPDATE testimonials SET approved=1 WHERE id=%s", (request.form.get("tid"),), commit=True)
            msg = ("success", "Testimonial approved.")
        elif act == "delete_t":
            query("DELETE FROM testimonials WHERE id=%s", (request.form.get("tid"),), commit=True)
            msg = ("warning", "Testimonial deleted.")
        elif act == "add_gallery":
            t = request.form.get("title", "").strip()
            d = request.form.get("description", "").strip()
            u = request.form.get("image_url", "").strip()
            if t:
                query("INSERT INTO gallery_items (title,description,image_url) VALUES (%s,%s,%s)", (t, d, u), commit=True)
                msg = ("success", "Gallery item added.")
        elif act == "delete_blog":
            query("DELETE FROM blog_posts WHERE id=%s", (request.form.get("bid"),), commit=True)
            msg = ("warning", "Blog post deleted.")
    blogs    = query("SELECT * FROM blog_posts ORDER BY created_at DESC", fetchall=True)
    pending  = query("SELECT * FROM testimonials WHERE approved=0 ORDER BY created_at DESC", fetchall=True)
    approved = query("SELECT * FROM testimonials WHERE approved=1 ORDER BY created_at DESC", fetchall=True)
    gal      = query("SELECT * FROM gallery_items ORDER BY created_at DESC", fetchall=True)
    return render_template("admin/content.html", blogs=blogs, pending=pending, approved=approved, gallery=gal, msg=msg)

@app.route("/admin/ai-report", methods=["GET", "POST"])
@login_required
def admin_ai_report():
    report = None
    if request.method == "POST":
        db = get_db()
        report = generate_incident_report(db)
    return render_template("admin/ai_report.html", report=report)

import os

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)