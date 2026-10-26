print("✅ STARTING: Dual-Engine Extraction Bot (Gemini + Groq)...")
import requests
import smtplib
import json
import pandas as pd
import time
import re 
import os 
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication 

# ================= CONFIGURATION =================
# ⚠️ WARNING: Please replace these with freshly generated keys for security!
import os
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

import os
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Email Configuration
SENDER_EMAIL = "heyyyashwini@gmail.com"
APP_PASSWORD = "hsxt akio cgdw xdoa" 

RESUME_FILENAME = "resume.pdf" 
YOUR_NAME = "Ashwini Kumar"
YOUR_PHONE = "+91 6207658257"

# File Settings
TARGET_FILE = "jobs.txt" 
SENT_HISTORY_FILE = "sent_history.txt"
# =================================================

def get_sent_emails():
    if not os.path.exists(SENT_HISTORY_FILE):
        return set()
    with open(SENT_HISTORY_FILE, "r") as f:
        return set(line.strip().lower() for line in f if line.strip())

def log_sent_email(email):
    with open(SENT_HISTORY_FILE, "a") as f:
        f.write(f"{email.lower()}\n")

def force_flatten(data):
    out = []
    if isinstance(data, list):
        for item in data: out.extend(force_flatten(item))
    elif isinstance(data, dict):
        if 'email' in data:
            out.append(data)
        else:
            for v in data.values(): out.extend(force_flatten(v))
    return out

# --- AI ENGINES ---
def call_gemini(chunk):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    prompt = "EXTRACT ALL EMAILS. Return a JSON list: [{'email': '...', 'name': '...', 'co': '...', 'role': '...'}]"
    payload = {
        "contents": [{"parts": [{"text": f"{prompt}\n\nTEXT:\n{chunk}"}]}],
        "generationConfig": {"response_mime_type": "application/json", "temperature": 0.1}
    }
    try:
        response = requests.post(url, json=payload, timeout=15)
        if response.status_code == 200:
            return json.loads(response.json()['candidates'][0]['content']['parts'][0]['text'])
    except: return None
    return None

def call_groq(chunk):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    prompt = "Extract every email lead from text into a JSON list. Keys: email, name, co, role."
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": f"{prompt}\n\nTEXT:\n{chunk}"}],
        "response_format": {"type": "json_object"}
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        if response.status_code == 200:
            content = json.loads(response.json()['choices'][0]['message']['content'])
            return content
    except: return None
    return None

def manual_regex_fallback(text):
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    return [{"email": e, "name": "Team", "co": "Company", "role": "Opening"} for e in set(emails)]

def send_email(data):
    to_email = str(data.get('email') or '').strip().lower()
    if "@" not in to_email: return "Invalid Email"

    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_email
    
    role = data.get('role') or "Remote Sales Representative"
    company = data.get('co') or "your team"
    
    # --- HIGH-IMPACT SUBJECT LINE ---
    msg['Subject'] = f"Imagine your sales workflow, fully automated | {role} Application"

    name = str(data.get('name') or 'there').split()[0]
    if name.lower() in ["founder", "hiring", "manager", "team"]: name = "there"

    # --- SCENARIO-BASED SALES EMAIL BODY ---
    body = (
        f"Hi {name},\n\n"
        f"Imagine this scenario:\n\n"
        f"All the tedious, manual admin work in your sales pipeline completely disappears. "
        f"Instead of spending hours hunting down prospects, you have an abundance of targeted, high-intent leads sitting in your CRM every morning. "
        f"Your sales reps focus 100% of their energy on high-value conversations, and as a result, your close rate jumps significantly week over week.\n\n"
        f"How would that impact to your company's revenue this quarter?\n\n"
        f"You can make that scenario a reality by bringing me onto your team.\n\n"
        f"I blend relentless sales execution with technical AI automation. In fact, I built the multi-engine AI bot "
        f"that extracted your contact details and sent this email to demonstrate my ability to generate pipeline on autopilot.\n\n"
        f"Here is what I bring to your team:\n"
        f"• Automated Pipeline Generation: Eliminating manual prospect hunting so every day starts with warm outreach.\n"
        f"• Higher Close Rates: Combining data-backed targeting with sharp objection handling to turn conversations into closed deals.\n"
        f"• Full Remote Efficiency: Self-sufficient execution ready to plug into your stack from Day 1.\n\n"
        f"If you're ready to see how this works in practice, I'd love to book a quick meeting whenever it's most convenient for you.\n\n"
        f"Are you open to a brief 5-minute call this week?\n\n"
        f"Best regards,\n\n"
        f"{YOUR_NAME}\n"
        f"Remote Sales & Automation Specialist\n"
        f"Phone/WhatsApp: {YOUR_PHONE}\n"
        f"Email: {SENDER_EMAIL}"
    )
    msg.attach(MIMEText(body, 'plain'))

    if os.path.exists(RESUME_FILENAME):
        with open(RESUME_FILENAME, "rb") as f:
            part = MIMEApplication(f.read(), _subtype="pdf")
            part.add_header('Content-Disposition', 'attachment', filename=RESUME_FILENAME)
            msg.attach(part)

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        server.quit()
        log_sent_email(to_email)
        return "Sent"
    except Exception as e:
        return f"SMTP Error: {e}"

# ================= MAIN =================
if __name__ == "__main__":
    if not os.path.exists(TARGET_FILE):
        print(f"❌ Error: {TARGET_FILE} not found!"); exit()

    with open(TARGET_FILE, "r", encoding="utf-8") as f:
        bulk_text = f.read()

    chunk_size = 6000 
    chunks = [bulk_text[i:i+chunk_size] for i in range(0, len(bulk_text), chunk_size)]
    
    all_leads = []
    print(f"📦 Processing {len(chunks)} batches...")

    for i, chunk in enumerate(chunks):
        print(f"🔄 Scanning Batch {i+1}/{len(chunks)}...", end="\r")
        
        # Try Gemini first, then Groq
        leads = call_gemini(chunk)
        if not leads:
            leads = call_groq(chunk)
        
        leads = force_flatten(leads)
        
        # Always run Regex to be safe
        regex_leads = manual_regex_fallback(chunk)
        
        all_leads.extend(leads + regex_leads)
        time.sleep(1)

    # De-duplicate
    unique_leads = {l['email'].lower(): l for l in all_leads if l.get('email')}.values()
    print(f"\n✅ Found {len(unique_leads)} unique email leads.")

    sent_history = get_sent_emails()
    results = []

    for job in unique_leads:
        email = job['email'].strip().lower()
        if email in sent_history: continue
            
        print(f"📧 Sending to: {email}...")
        status = send_email(job)
        job['status'] = status
        print(f"   Result: {status}")
        
        if status == "Sent":
            sent_history.add(email)
            time.sleep(3) 
        
        results.append(job)

    pd.DataFrame(results).to_excel("Final_Report_Dual_Engine.xlsx", index=False)
    print("\n🎉 Done! Report saved.")