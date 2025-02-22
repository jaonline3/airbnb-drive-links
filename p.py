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
  "Berlin", "Hamburg", "Munich", "Cologne", "Frankfurt",
    "Stuttgart", "Düsseldorf", "Leipzig", "Dortmund", "Essen",
    "Bremen", "Dresden", "Hanover", "Nuremberg", "Duisburg",
    "Bochum", "Wuppertal", "Bielefeld", "Bonn", "Münster",
    "Karlsruhe", "Mannheim", "Augsburg", "Wiesbaden", "Gelsenkirchen",
    "Mönchengladbach", "Braunschweig", "Kiel", "Aachen", "Chemnitz",
    "Halle (Saale)", "Magdeburg", "Freiburg im Breisgau", "Krefeld", "Lübeck",
    "Oberhausen", "Erfurt", "Mainz", "Rostock", "Kassel",
    "Hagen", "Saarbrücken", "Hamm", "Potsdam", "Ludwigshafen",
    "Oldenburg", "Leverkusen", "Osnabrück", "Solingen", "Heidelberg",
    "Herne", "Neuss", "Darmstadt", "Paderborn", "Regensburg",
    "Ingolstadt", "Würzburg", "Wolfsburg", "Ulm", "Heilbronn",
    "Offenbach", "Göttingen", "Bottrop", "Recklinghausen", "Pforzheim",
    "Bremerhaven", "Fürth", "Reutlingen", "Remscheid", "Moers",
    "Koblenz", "Bergisch Gladbach", "Erlangen", "Trier", "Jena",
    "Siegen", "Gütersloh", "Salzgitter", "Hildesheim", "Cottbus",
    "Gera", "Schwerin", "Witten", "Zwickau", "Iserlohn",
    "Gießen", "Düren", "Esslingen", "Flensburg", "Kleve",
    "Bamberg", "Nordhorn", "Neumünster", "Ludwigsburg", "Landshut",
    "Villingen-Schwenningen", "Rosenheim", "Wilhelmshaven", "Ravensburg", "Lüneburg", "Bayreuth", "Aschaffenburg", "Neuwied", "Lingen", "Sindelfingen",
    "Neubrandenburg", "Frankfurt (Oder)", "Hanau", "Minden", "Worms",
    "Baden-Baden", "Speyer", "Freiberg", "Weimar", "Passau",
    "Kempten", "Straubing", "Fulda", "Wetzlar", "Lörrach",
    "Sankt Augustin", "Ahlen", "Dachau", "Marburg", "Hof",
    "Bad Homburg", "Leonberg", "Kaiserslautern", "Greifswald", "Rüsselsheim",
    "Emden", "Garbsen", "Lippstadt", "Görlitz", "Freising",
    "Wermelskirchen", "Viersen", "Sankt Ingbert", "Bad Salzuflen", "Zweibrücken",
    "Böblingen", "Waiblingen", "Gummersbach", "Erkelenz", "Bad Kreuznach",
    "Oberursel", "Homburg", "Meerbusch", "Bautzen", "Hohen Neuendorf",
    "Unna", "Ibbenbüren", "Schorndorf", "Neu-Ulm", "Hilden",
    "Nordhausen", "Gifhorn", "Schwäbisch Hall", "Delmenhorst", "Wedel",
    "Cloppenburg", "Falkensee", "Bensheim", "Tuttlingen", "Weiden",
    "Stolberg", "Lüneburg", "Bad Nauheim", "Rheine", "Elmshorn",
    "Memmingen", "Bergheim", "Riesa", "Leinfelden-Echterdingen", "Wesseling",
    "Singen", "Oberkirch", "Wismar", "Neustadt an der Weinstraße", "Rosenfeld",
    "Euskirchen", "Garmisch-Partenkirchen", "Bad Oeynhausen", "Forchheim", "Lahr",
    "Schwäbisch Gmünd", "Rathenow", "Willich", "Mettmann", "Grevenbroich",
    "Husum", "Aalen", "Kornwestheim", "Weil am Rhein", "Weinheim",
    "Ludwigshafen am Rhein", "Bad Vilbel", "Bünde", "Erkrath", "Neckarsulm"
]
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

        query = f'email "electronic cables" "{city}"'
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
