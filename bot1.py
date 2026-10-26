import os
import smtplib
import time
import pandas as pd
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ================= CONFIGURATION =================
# Email Configuration
SENDER_EMAIL = "heyyashwini@gmail.com"
APP_PASSWORD = "ccdv xvzi mgqg pdmk"  # Remember to keep app passwords secure!

YOUR_NAME = "Ashwini"
YOUR_PHONE = "+916207658257"

# File Settings
EXCEL_FILE = "Dentist_Prospecting_Database_Phoenix_Dallas (1).xlsx"
SENT_HISTORY_FILE = "sent_history.txt"
OUTPUT_REPORT_FILE = "Final_Cafe_Outreach_Report.xlsx"
# =================================================


def get_sent_emails():
    """Load previously sent email addresses to avoid sending duplicate emails."""
    if not os.path.exists(SENT_HISTORY_FILE):
        return set()
    with open(SENT_HISTORY_FILE, "r") as f:
        return set(line.strip().lower() for line in f if line.strip())


def log_sent_email(email):
    """Append sent email to the history file."""
    with open(SENT_HISTORY_FILE, "a") as f:
        f.write(f"{email.lower()}\n")


def format_followers(followers_val):
    """Format numeric follower counts into a clean readable string (e.g., 28,500 or 28.5K)."""
    try:
        val = int(followers_val)
        if val >= 1000:
            return f"{val:,}"  # Formats as 28,500
        return str(val)
    except (ValueError, TypeError):
        return str(followers_val) if pd.notna(followers_val) else "a growing number of"


def clean_owner_name(name_val):
    """Extract a friendly first name or default if generic title is present."""
    if pd.isna(name_val) or not str(name_val).strip():
        return "there"

    name_str = str(name_val).strip()

    # Handle generic placeholders in dataset like 'Local Leadership' or 'Local Management'
    if name_str.lower() in [
        "local leadership",
        "local management",
        "team",
        "owner",
        "manager",
    ]:
        return "there"

    # Take first name if multiple names are present (e.g. "Jason & Amy" -> "Jason")
    first_name = name_str.split()[0]
    return first_name


def send_personalized_email(row):
    to_email = str(row.get("Business Email") or "").strip().lower()
    if "@" not in to_email:
        return "Invalid Email"

    cafe_name = str(row.get("Practice Name") or "Practice Name").strip()
    raw_owner = row.get("Owner / Decision Maker")
    owner_name = clean_owner_name(raw_owner)

    raw_followers = row.get("Followers")
    formatted_followers = format_followers(raw_followers)

    # --- EMAIL SUBJECT LINE ---
    subject = f"Brand Outreach for {cafe_name}"

    # --- PERSONALIZED EMAIL BODY ---
    body = (
        f"Hi {cafe_name},\n\n"
        f"I came across {cafe_name} recently and spent some time looking through your Instagram and website.\n\n"
        f"First of all, you're doing a great job. You've built a community of around {formatted_followers} followers, "
        f"and it's clear people genuinely enjoy what you're creating. That said, I also noticed something.\n\n"
        f"Your brand is growing, but at a slow and steady pace. While consistency is important, in today's market "
        f"that often means competitors with stronger content and better marketing end up capturing customers that could have been yours.\n\n"
        f"I believe {cafe_name} has much more potential.\n\n"
        f"Here's how I can help:\n"
        f"• Create high-quality, engaging social media content that people actually want to share.\n"
        f"• Maintain a consistent posting strategy to keep your audience engaged and attract new customers.\n"
        f"• Redesign and optimize your website to make it look modern, professional, and conversion-focused.\n"
        f"• Run personalized advertising campaigns that target people most likely to visit your café.\n"
        f"• Build a stronger online brand presence that turns viewers into loyal customers.\n\n"
        f"My goal isn't just to make your social media look better—it's to help bring more people through your doors and scale your business.\n\n"
        f"If you're open to it, I'd love to audit your current online presence and share a few ideas specific to {cafe_name}—completely free, with no obligation.\n\n"
        f"Would you be available for a quick 15-minute call sometime this week?\n\n"
        f"Looking forward to hearing from you.\n\n"
        f"Best regards,\n"
        f"{YOUR_NAME} ({YOUR_PHONE})"
    )

    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        server.quit()

        log_sent_email(to_email)
        return "Sent"
    except Exception as e:
        return f"SMTP Error: {e}"


# ================= MAIN EXECUTION =================
if __name__ == "__main__":
    if not os.path.exists(EXCEL_FILE):
        print(f"❌ Error: File '{EXCEL_FILE}' not found in the current directory.")
        exit()

    print(f"📖 Reading leads from '{EXCEL_FILE}'...")
    df = pd.read_excel(EXCEL_FILE)

    if "Business Email" not in df.columns:
        print("❌ Error: 'Business Email' column not found in Excel sheet!")
        exit()

    sent_history = get_sent_emails()
    results = []

    total_leads = len(df)
    print(f"✅ Found {total_leads} entries in sheet.\n")

    for index, row in df.iterrows():
        email = str(row.get("Business Email") or "").strip().lower()
        cafe_name = row.get("Cafe Name", "Unknown Cafe")

        if not email or "@" not in email:
            print(f"⚠️ [{index+1}/{total_leads}] Skipping {cafe_name}: Invalid email address.")
            row_dict = row.to_dict()
            row_dict["Send Status"] = "Invalid Email"
            results.append(row_dict)
            continue

        if email in sent_history:
            print(f"⏩ [{index+1}/{total_leads}] Skipping {cafe_name} ({email}): Already sent.")
            row_dict = row.to_dict()
            row_dict["Send Status"] = "Already Sent Previously"
            results.append(row_dict)
            continue

        print(f"📧 [{index+1}/{total_leads}] Sending to {cafe_name} ({email})...")
        status = send_personalized_email(row)

        row_dict = row.to_dict()
        row_dict["Send Status"] = status
        results.append(row_dict)

        print(f"   └── Result: {status}")

        if status == "Sent":
            sent_history.add(email)
            time.sleep(3)  # Rate limiting delay to avoid spam filters

    report_df = pd.DataFrame(results)
    report_df.to_excel(OUTPUT_REPORT_FILE, index=False)
    print(f"\n🎉 Campaign finished! Report saved to '{OUTPUT_REPORT_FILE}'.")