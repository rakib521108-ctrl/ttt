"""
panel_forward_full_sms.py
Manual login version with:
 - Duplicate prevention (no same OTP multiple times)
 - Telegram flood control (429 error handling)
 - New message format with quoted SMS content
 - Country flag emojis
 - Copyable OTP code
 - Firefox browser instead of Chrome
"""

import time
import requests
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup
import re

# --------------------------
# CONFIG
# --------------------------
OTP_PAGE = "http://45.82.67.20/ints/client/SMSCDRStats"

BOT_TOKEN = "8483391342:AAEPvIt-43g7DTr5HXOpNCzpal96VNVmq5c"
GROUP_CHAT_ID = "-1002717336822"

POLL_INTERVAL_SECONDS = 5
# --------------------------

TELEGRAM_SEND_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

def send_telegram_message(chat_id: str, text: str):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    while True:
        r = requests.post(TELEGRAM_SEND_URL, data=payload, timeout=15)
        if r.ok:
            return r
        elif r.status_code == 429:
            try:
                retry_after = r.json().get("parameters", {}).get("retry_after", 5)
            except Exception:
                retry_after = 5
            print(f"⚠️ Telegram rate limit, waiting {retry_after}s...")
            time.sleep(retry_after)
            continue
        else:
            print("Telegram send failed:", r.status_code, r.text)
            return r

def open_driver():
    firefox_options = Options()
    # headless বাদ → Firefox উইন্ডো দেখা যাবে
    driver = webdriver.Firefox(options=firefox_options)
    driver.set_page_load_timeout(30)
    driver.implicitly_wait(8)
    return driver

def get_sms_rows(html: str):
    """Extract SMS records (Date, Number, CLI, SMS) from HTML table."""
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    table = soup.find("table", {"id": "dt"})
    if not table:
        return rows
    tbody = table.find("tbody")
    if not tbody:
        return rows
    for tr in tbody.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) >= 5:
            date = tds[0].get_text(strip=True)
            number = tds[2].get_text(strip=True)
            cli = tds[3].get_text(strip=True)
            sms = tds[4].get_text("\n", strip=True)
            # skip garbage row (যেমন 0,0,0,25)
            if number == "0" or sms == "0":
                continue
            rows.append((date, number, cli, sms))
    return rows

def get_otp_page_html(driver):
    driver.get(OTP_PAGE)
    time.sleep(1)
    return driver.page_source

def get_country_with_flag(number):
    """নম্বর থেকে দেশ সনাক্ত করে এবং ইমোজি পতাকা রিটার্ন করে"""
    # দেশ কোড অনুযায়ী পতাকা ইমোজি
    country_flags = {
        '98': '🇮🇷',  # Iran
        '91': '🇮🇳',  # India
        '1': '🇺🇸',   # USA
        '44': '🇬🇧',  # UK
        '86': '🇨🇳',  # China
        '81': '🇯🇵',  # Japan
        '82': '🇰🇷',  # South Korea
        '65': '🇸🇬',  # Singapore
        '60': '🇲🇾',  # Malaysia
        '63': '🇵🇭',  # Philippines
        '84': '🇻🇳',  # Vietnam
        '66': '🇹🇭',  # Thailand
        '62': '🇮🇩',  # Indonesia
        '92': '🇵🇰',  # Pakistan
        '880': '🇧🇩', # Bangladesh
        '93': '🇦🇫',  # Afghanistan
        '94': '🇱🇰',  # Sri Lanka
        '95': '🇲🇲',  # Myanmar
        '975': '🇧🇹', # Bhutan
        '977': '🇳🇵', # Nepal
        '971': '🇦🇪', # UAE
        '966': '🇸🇦', # Saudi Arabia
        '974': '🇶🇦', # Qatar
        '973': '🇧🇭', # Bahrain
        '968': '🇴🇲', # Oman
        '964': '🇮🇶', # Iraq
        '963': '🇸🇾', # Syria
        '962': '🇯🇴', # Jordan
        '961': '🇱🇧', # Lebanon
        '20': '🇪🇬',  # Egypt
        '90': '🇹🇷',  # Turkey
    }
    
    # নম্বর থেকে দেশ কোড বের করা
    for code, flag in country_flags.items():
        if number.startswith(code):
            return f"{flag} {get_country_name(code)}"
    
    return "🌐 Unknown Country"

def get_country_name(country_code):
    """কান্ট্রি কোড থেকে কান্ট্রির নাম রিটার্ন করে"""
    country_names = {
        '98': 'Iran',
        '91': 'India',
        '1': 'USA',
        '44': 'UK',
        '86': 'China',
        '81': 'Japan',
        '82': 'South Korea',
        '65': 'Singapore',
        '60': 'Malaysia',
        '63': 'Philippines',
        '84': 'Vietnam',
        '66': 'Thailand',
        '62': 'Indonesia',
        '92': 'Pakistan',
        '880': 'Bangladesh',
        '93': 'Afghanistan',
        '94': 'Sri Lanka',
        '95': 'Myanmar',
        '975': 'Bhutan',
        '977': 'Nepal',
        '971': 'UAE',
        '966': 'Saudi Arabia',
        '974': 'Qatar',
        '973': 'Bahrain',
        '968': 'Oman',
        '964': 'Iraq',
        '963': 'Syria',
        '962': 'Jordan',
        '961': 'Lebanon',
        '20': 'Egypt',
        '90': 'Turkey',
    }
    return country_names.get(country_code, 'Unknown')

def detect_service(sms_text):
    """SMS টেক্সট থেকে সার্ভিস সনাক্ত করে"""
    text_lower = sms_text.lower()
    
    services = {
        'whatsapp': 'WhatsApp',
        'telegram': 'Telegram',
        'facebook': 'Facebook',
        'google': 'Google',
        'apple': 'Apple',
        'instagram': 'Instagram',
        'twitter': 'Twitter',
        'amazon': 'Amazon',
        'microsoft': 'Microsoft',
        'netflix': 'Netflix',
        'bank': 'Bank',
        'paypal': 'PayPal',
        'binance': 'Binance',
        'grab': 'Grab',
        'gojek': 'Gojek',
        'line': 'Line',
        'wechat': 'WeChat',
        'viber': 'Viber',
        'signal': 'Signal',
        'discord': 'Discord'
    }
    
    for keyword, service_name in services.items():
        if keyword in text_lower:
            return service_name
    
    return "Unknown Service"

def extract_otp(sms_text):
    """SMS থেকে OTP এক্সট্র্যাক্ট করে"""
    # সংখ্যা অনুসন্ধান (4-8 ডিজিটের OTP)
    numbers = re.findall(r'\b\d{4,8}\b', sms_text)
    if numbers:
        return numbers[0]
    
    # হাইফেনযুক্ত OPT (যেমন: 331-430)
    hyphen_otp = re.findall(r'\b\d{3,4}-\d{3,4}\b', sms_text)
    if hyphen_otp:
        return hyphen_otp[0]
    
    return None

def format_message(date, number, cli, sms):
    """আপনার চাহিদা অনুযায়ী মেসেজ ফরম্যাট করুন"""
    # নম্বর মাস্ক করা (প্রথম 6 এবং শেষ 3 ডিজিট দেখাবে)
    masked_number = '***' + number[3:]
    # দেশ ও পতাকা ইমোজি
    country_with_flag = get_country_with_flag(number)
    
    # সার্ভিস ডিটেক্ট করা
    service = detect_service(sms)
    
    # OTP এক্সট্র্যাক্ট করা
    otp_code = extract_otp(sms)
    
    # বর্তমান সময়
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
    
    # নতুন মেসেজ ফরমেট তৈরি (HTML ফরম্যাটে)
    message = f"""🔥 <b>{service} {get_country_name('98') if '98' in number else 'Unknown'}</b>🇮🇷RECEIVED! ✨

⏰ <b>Time:</b> {current_time}
🌍 <b>Country:</b> {country_with_flag}
⚙️ <b>Service:</b> {service}
☎️ <b>Number:</b> {masked_number}
🔑 <b>OTP:</b> <code>{otp_code if otp_code else 'N/A'}</code>
📩 <b>Full Message:</b> 

<blockquote>{sms}</blockquote>"""
    
    return message

def main_loop():
    driver = open_driver()
    print("✅ Firefox ওপেন হয়েছে। ম্যানুয়ালি লগইন করুন।")
    input("👉 লগইন শেষে Enter চাপুন ফরওয়ার্ড শুরু করতে...")

    sent_ids = set()
    print("🚀 এখন থেকে নতুন SMS এলে ফরওয়ার্ড হবে (ডুপ্লিকেট যাবে না)।")

    try:
        while True:
            try:
                html = get_otp_page_html(driver)
                rows = get_sms_rows(html)
            except Exception as e:
                print("Error fetching OTP page:", e)
                time.sleep(POLL_INTERVAL_SECONDS)
                continue

            for date, number, cli, sms in rows:
                unique_id = f"{date}|{number}|{sms[:20]}"  # ID বানালাম
                if unique_id not in sent_ids:
                    msg = format_message(date, number, cli, sms)
                    print(f"📩 নতুন SMS: {number} - {sms[:30]}...")
                    resp = send_telegram_message(GROUP_CHAT_ID, msg)
                    if resp.ok:
                        sent_ids.add(unique_id)

            time.sleep(POLL_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("❌ Stopped by user.")
    finally:
        driver.quit()

if __name__ == "__main__":
    main_loop()
