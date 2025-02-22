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

# Cities to search in
CITIES1 =["Montgomery", "Hoover", "Tuscaloosa",  # Alabama
    "Fairbanks", "Juneau",  # Alaska
    "Mesa", "Scottsdale",  # Arizona
    "Fayetteville", "Springdale",  # Arkansas
    "Anaheim", "Bakersfield", "Long Beach", "Santa Clara", "Santa Monica",  # California
    "Aurora", "Pueblo",  # Colorado
    "New Haven", "Stamford", "Waterbury",  # Connecticut
    "Dover", "Newark",  # Delaware
    "Fort Myers", "St. Petersburg", "Tallahassee", "West Palm Beach",  # Florida
    "Macon", "Savannah", "Albany",  # Georgia
    "Hilo",  # Hawaii
    "Idaho Falls", "Pocatello",  # Idaho
    "Springfield", "Naperville", "Peoria", "Rockford",  # Illinois
    "Fort Wayne", "Gary", "South Bend",  # Indiana
    "Cedar Rapids", "Sioux City",  # Iowa
    "Overland Park", "Topeka",  # Kansas
    "Lexington", "Bowling Green",  # Kentucky
    "Lafayette", "Lake Charles",  # Louisiana
    "Portland", "Bangor",  # Maine
    "Rockville", "Annapolis",  # Maryland
    "Worcester", "Springfield", "Lowell",  # Massachusetts
    "Abilene", "Akron", "Albany", "Albuquerque", "Anchorage", "Anderson", "Ann Arbor", "Appleton", "Arlington", "Asheville",
    "Aspen", "Athens", "Atlanta", "Augusta", "Austin", "Baltimore", "Birmingham", "Boise", "Boston", "Buffalo",
    "Charleston", "Charlotte", "Chicago", "Cincinnati", "Cleveland", "Colorado Springs", "Columbia", "Columbus", "Dallas", "Denver",
    "Des Moines", "Detroit", "Durham", "El Paso", "Fort Worth", "Fresno", "Grand Rapids", "Greensboro", "Greenville", "Harrisburg",
    "Hartford", "Honolulu", "Houston", "Indianapolis", "Jackson", "Jacksonville", "Kansas City", "Las Vegas", "Little Rock", "Louisville",
    "Madison", "Memphis", "Miami", "Milwaukee", "Minneapolis", "Nashville", "New Orleans", "New York", "Oklahoma City", "Omaha",
    "Orlando", "Philadelphia", "Phoenix", "Pittsburgh", "Portland", "Raleigh", "Richmond", "Riverside", "Sacramento", "St. Louis",
    "Salt Lake City", "San Antonio", "San Diego", "San Francisco", "San Jose", "Seattle", "St. Paul", "Tampa", "Toledo", "Tucson",
    "Tulsa", "Washington", "Wichita", "Aberdeen", "Allentown", "Ames", "Anchorage", "Anniston", "Apple Valley", "Arlington Heights", 
    "Ashtabula", "Atchison", "Atlanta", "Atlantic City", "Auburn", "Augusta", "Austin", "Baltimore", "Bangor", "Barnstable",
    "Baton Rouge", "Battle Creek", "Bay City", "Beaumont", "Bedford", "Bend", "Bessemer", "Bethlehem", "Billings", "Bismarck", 
    "Bloomington", "Blue Springs", "Boise", "Boston", "Boulder", "Bowling Green", "Bradenton", "Brandon", "Brattleboro", 
    "Bremerton", "Bridgeport", "Brockton", "Brooklyn", "Buffalo", "Burlington", "Caldwell", "Camarillo", "Canton", "Cape Coral", 
    "Carson", "Casper", "Cedar Rapids", "Champaign", "Chandler", "Charleston", "Charlotte", "Chattanooga", "Cheyenne", "Chicago", 
    "Chico", "Cincinnati", "Cleveland", "Clarksburg", "Clearwater", "Clinton", "Columbia", "Columbus", "Concord", "Corpus Christi", 
    "Costa Mesa", "Dallas", "Davenport", "Dayton", "Denver", "Des Moines", "Detroit", "Dothan", "Draper", "Durham", 
    "Eagan", "El Paso", "Englewood", "Eugene", "Evansville", "Fargo", "Fayetteville", "Flagstaff", "Flint", "Fort Collins", 
    "Fort Lauderdale", "Fort Wayne", "Fort Worth", "Fresno", "Gainesville", "Galveston", "Garden Grove", "Gastonia", "Gilbert", 
    "Glendale", "Grand Forks", "Grand Junction", "Grand Rapids", "Great Falls", "Green Bay", "Greensboro", "Greenville", "Hagerstown", 
    "Hamilton", "Harrisburg", "Hartford", "Henderson", "Honolulu", "Houston", "Indianapolis", "Iowa City", "Irving", "Jackson", 
    "Jacksonville", "Jamestown", "Janesville", "Jersey City", "Johnson City", "Joliet", "Jonesboro", "Kansas City", "Kennewick", 
    "Killeen", "Kingston", "Knoxville", "Lafayette", "Lansing", "Las Vegas", "Laredo", "Little Rock", "Long Beach", "Los Angeles", 
    "Louisville", "Lubbock", "Madison", "Macon", "Manchester", "Medford", "Memphis", "Miami", "Milwaukee", "Minneapolis", 
    "Mobile", "Modesto", "Montgomery", "Nashville", "New Orleans", "New York", "Norfolk", "Oakland", "Oklahoma City", 
    "Omaha", "Ontario", "Orlando", "Overland Park", "Philadelphia", "Phoenix", "Pittsburgh", "Portland", "Providence", 
    "Raleigh", "Reno", "Richmond", "Riverside", "Rockford", "Sacramento", "St. Louis", "Salt Lake City", "San Antonio", "San Diego", 
    "San Francisco", "San Jose", "Santa Ana", "Seattle", "Shreveport", "Simi Valley", "South Bend", "Spokane", "St. Paul", 
    "Stockton", "Tampa", "Tempe", "Toledo", "Tucson", "Tulsa", "Waco", "Washington", "Wichita", "Yonkers"
]

CITIES=[
   "Madrid", "Barcelona", "Valencia", "Seville", "Zaragoza",
    "Málaga", "Murcia", "Palma", "Las Palmas", "Bilbao",
    "Alicante", "Córdoba", "Valladolid", "Vigo", "Gijón",
    "L'Hospitalet", "A Coruña", "Vitoria-Gasteiz", "Granada", "Elche",
    "Santa Cruz de Tenerife", "Oviedo", "Badalona", "Cartagena", "Tarragona",
    "Jerez de la Frontera", "Sabadell", "Móstoles", "Alcalá de Henares", "Pamplona",
    "Fuenlabrada", "Almería", "San Sebastián", "Leganés", "Santander",
    "Castellón de la Plana", "Burgos", "Albacete", "Getafe", "Alcorcón",
    "Logroño", "Badajoz", "Salamanca", "Huelva", "Lleida",
    "Marbella", "Tarrasa", "Dos Hermanas", "San Cristóbal de La Laguna", "Torrejón de Ardoz","Torrevieja", "Mataró", "Santa Coloma de Gramenet", "Jaén", "Algeciras",
    "Reus", "Ourense", "Santiago de Compostela", "Guadalajara", "Telde",
    "San Fernando", "Roquetas de Mar", "San Sebastián de los Reyes", "Avilés", "Ponferrada",
    "Benidorm", "Zamora", "Rivas-Vaciamadrid", "Toledo", "Coslada",
    "El Puerto de Santa María", "Pontevedra", "Girona", "Melilla", "Ceuta",
    "Talavera de la Reina", "Castelldefels", "Rubí", "Fuengirola", "Segovia",
    "Manresa", "Ferrol", "Sanlúcar de Barrameda", "Arrecife", "Gandía",
    "Ávila", "Collado Villalba", "Ciudad Real", "San Vicente del Raspeig", "Utrera",
    "Elda", "Granollers", "Chiclana de la Frontera", "Torremolinos", "Vélez-Málaga",
    "Mollet del Vallès", "La Línea de la Concepción", "Viladecans", "Majadahonda", "Motril","Barakaldo", "San Bartolomé de Tirajana", "Lorca", "Orihuela", "San Cugat del Vallès",
    "Cornellà de Llobregat", "Alcobendas", "Ibiza", "Benalmádena", "Arona",
    "Pozuelo de Alarcón", "Valdemoro", "Torrelavega", "Paterna", "Irún",
    "Esplugues de Llobregat", "Torremolinos", "Linares", "Mijas", "Vilafranca del Penedès",
    "Sant Boi de Llobregat", "Manacor", "Santa Lucía de Tirajana", "Vic", "Olot",
    "Mérida", "Sestao", "Figueres", "Moncada y Reixach", "Cáceres",
    "Alcoy", "Aranjuez", "Port de Pollença", "San Andrés del Rabanedo", "Rota",
    "Zafra", "Tafalla", "Pinto", "Baza", "Cieza",
    "Yecla", "Plasencia", "Cuenca", "Los Realejos", "Lloret de Mar",
    "Villarreal", "La Orotava", "Eivissa", "Calella", "Alzira", "San Vicente del Raspeig", "Torrevieja", "Ferrol", "Sanlúcar de Barrameda", "Benidorm",
    "Santa Pola", "Manresa", "Arrecife", "Rincón de la Victoria", "Puerto de la Cruz",
    "Sant Adrià de Besòs", "Cerdanyola del Vallès", "Ávila", "Villanueva de la Serena", "Gandía",
    "Inca", "Coslada", "Adeje", "Blanes", "Sant Feliu de Llobregat",
    "Estepona", "Elda", "Roses", "Martorell", "Mollet del Vallès",
    "Catarroja", "Puerto Real", "Sagunto", "Chiclana de la Frontera", "Cangas",
    "Fuengirola", "Tres Cantos", "Ponferrada", "Las Rozas de Madrid", "Molins de Rei",
    "Onda", "Villajoyosa", "San Pedro del Pinatar", "San Roque", "Almendralejo",
    "Noia", "Santander de Quilichao", "Silla", "Villafranca del Bierzo", "Navalmoral de la Mata",
    "Lepe", "Narón", "Sant Celoni", "Alhaurín de la Torre", "Utrera"
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
