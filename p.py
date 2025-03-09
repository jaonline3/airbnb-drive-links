import json
import os
import requests
import time
import subprocess
import psutil
import csv
import re
from io import BytesIO
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from duckduckgo_search import DDGS

# Load credentials from JSON
with open('file.json', 'r') as f:
    key_data = json.load(f)

# Tor Proxy Settings
TOR_PROXY = "socks5h://127.0.0.1:9050"
TOR_LOG_FILE = "tor_log.txt"

# Google Drive API Credentials
SERVICE_ACCOUNT_FILE = "file.json"  # Ensure this is a valid file path
DRIVE_FOLDER_ID = "1MP5GR_GFxe8x4eEE-A-uOLaLPeq37Yg1"



CITIES=[
    "Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide", "Canberra", "Hobart", "Darwin",
    "Newcastle", "Wollongong", "Geelong", "Cairns", "Alice Springs", "Bendigo", "Ballarat",
    "Albury", "Wagga Wagga", "Launceston", "Devonport", "Burnie", "Rockhampton", "Geraldton",
    "Kalgoorlie", "Mildura", "Shepparton", "Coffs Harbour", "Dubbo", "Tamworth", "Orange",
    "Bathurst", "Nowra", "Lismore", "Port Macquarie", "Mount Gambier", "Goulburn", "Armidale",
    "Broken Hill", "Grafton", "Taree", "Port Augusta", "Whyalla", "Mount Gambier", "Warrnambool",
    "Traralgon", "Wangaratta", "Horsham", "Echuca", "Bairnsdale", "Sale", "Ballina", "Forster",
    "Maitland", "Singleton", "Muswellbrook", "Lithgow", "Young", "Cooma", "Parkes", "Forbes",
    "Narrabri", "Moree", "Griffith", "Swan Hill", "Wodonga", "Katherine", "Tennant Creek",
    "Port Hedland", "Karratha", "Esperance", "Albany", "Busselton", "Margaret River", "Manjimup",
    "Northam", "Bunbury", "Geraldton", "Broome", "Exmouth", "Carnarvon", "Kununurra", "Derby",
    "Port Lincoln", "Victor Harbor", "Murray Bridge", "Gawler", "Mount Barker", "Renmark",
    "Bordertown", "Naracoorte", "Strathalbyn", "Kadina", "Clare", "Yorketown", "Peterborough",
    "Streaky Bay", "Ceduna", "Coober Pedy", "Tumut", "Deniliquin", "Yass", "Batemans Bay",
    "Merimbula", "Ulladulla", "Gosford", "Wyong", "Tweed Heads", "Casino", "Bowral", "Mittagong",
    "Queanbeyan", "Cootamundra", "West Wyalong", "Nyngan", "Bourke", "Lightning Ridge",
    "Charters Towers", "Mount Isa", "Longreach", "Emerald", "Blackwater", "Biloela",
    "Gladstone", "Bundaberg", "Hervey Bay", "Maryborough", "Roma", "Goondiwindi", "Dalby",
    "Kingaroy", "Stanthorpe", "Warwick", "Cunnamulla", "Birdsville", "Weipa", "Cooktown",
    "Thursday Island", "Yulara", "Alice Springs", "Jabiru", "Nhulunbuy", "Howard Springs"]
def is_tor_running():
    """Check if Tor process is running."""
    return any("tor" in process.info["name"].lower() for process in psutil.process_iter(["name"]))

def restart_tor():
    """Restart Tor to get a new IP address."""
    print("\n🔄 Restarting Tor...")
    subprocess.run(["pkill", "tor"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(5)
    
    tor_process = subprocess.Popen(
        ["tor"], stdout=open(TOR_LOG_FILE, "a"), stderr=subprocess.STDOUT
    )
    time.sleep(20)
    
    if is_tor_running():
        print("✅ Tor is running successfully!")
    else:
        print("❌ Failed to start Tor. Check tor_log.txt.")

def perform_search_with_tor(query, retries=5):
    """Perform DuckDuckGo search using Tor, with retries."""
    results = []
    
    for attempt in range(retries):
        try:
            # Check Tor IP
            ip_response = requests.get("http://httpbin.org/ip", proxies={"http": TOR_PROXY, "https": TOR_PROXY})
            print(f"🌍 Your IP via Tor: {ip_response.json()['origin']}")

            with DDGS(proxy=TOR_PROXY) as ddgs:
                search_results = list(ddgs.text(query, max_results=70))

            if isinstance(search_results, list):
                return search_results
            else:
                print("⚠️ Warning: Unexpected search result format. Retrying...")

        except Exception as e:
            print(f"⚠️ Error during search (Attempt {attempt+1}/{retries}): {e}")
            time.sleep(10)  # Wait before retrying
    
    return []

def extract_emails_and_phone(text):
    """Extract emails and phone numbers from text."""
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    phone_numbers = re.findall(r'\+?\d{1,3}?[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}', text)
    return emails, phone_numbers

def save_to_csv(results, filename="search_results.csv"):
    """Save search results to a CSV file."""
    if not results:
        print("⚠️ No data to save.")
        return
    
    with open(filename, mode="w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(["Title", "Link", "Snippet", "Emails", "Phone Numbers"])
        
        for result in results:
            if isinstance(result, dict):  # Ensure result is a dictionary
                writer.writerow([
                    result.get("title", ""), 
                    result.get("href", ""), 
                    result.get("body", ""), 
                    
                ])
            else:
                print(f"⚠️ Skipping invalid result: {result}")

    print(f"📁 Results saved to {filename}")

def upload_to_drive(filename, folder_id):
    """Upload a file to Google Drive."""
    try:
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=["https://www.googleapis.com/auth/drive"]
        )
        service = build("drive", "v3", credentials=credentials)

        file_metadata = {"name": filename, "parents": [folder_id]}
        media = MediaIoBaseUpload(open(filename, "rb"), mimetype="text/csv")
        file = service.files().create(body=file_metadata, media_body=media, fields="id").execute()

        print(f"✅ File uploaded to Google Drive: {file.get('id')}")
        return file.get("id")

    except Exception as e:
            print(f"⚠️ Google Drive upload failed (Attempt {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                print("⏳ Retrying in 20 seconds...")
                time.sleep(20)  # Wait before retrying
    

# Main execution loop
all_results = []
for city in CITIES:
    try:
        print(f"\n🔍 Searching in: {city}")
        restart_tor()  # Restart Tor for each search

        query = f'site:facebook.com ("@gmail.com" OR "@yahoo.com" OR "@outlook.com" OR "@hotmail.com" OR "@icloud.com" OR "@protonmail.com" OR "@aol.com" OR "@zoho.com" OR "@gmx.com" OR "@yandex.com" OR "@mail.com") "crypto" {city}'
        search_results = perform_search_with_tor(query)

        if search_results and isinstance(search_results, list):
            all_results.extend(search_results)

    except Exception as e:
        print(f"⚠️ Error while searching {city}: {e}")
        continue

# Save and upload results
if all_results:
    save_to_csv(all_results)
    upload_to_drive("search_results.csv", DRIVE_FOLDER_ID)
else:
    print("⚠️ No results found.")
