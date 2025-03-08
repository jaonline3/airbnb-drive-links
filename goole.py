from io import BytesIO
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import time
from time import sleep
from bs4 import BeautifulSoup
from requests import get
from urllib.parse import unquote
# Function to get a new proxy IP
def get_new_proxy():
    # Use Nimble's API to get a new proxy IP
    proxy_url = f"http://{NIMBLE_USERNAME}:{NIMBLE_PASSWORD}@{NIMBLE_SERVER}:{NIMBLE_PORT}"
    return proxy_url
def get_useragent():
    """
    Generates a random user agent string mimicking the format of various software versions.

    The user agent string is composed of:
    - Lynx version: Lynx/x.y.z where x is 2-3, y is 8-9, and z is 0-2
    - libwww version: libwww-FM/x.y where x is 2-3 and y is 13-15
    - SSL-MM version: SSL-MM/x.y where x is 1-2 and y is 3-5
    - OpenSSL version: OpenSSL/x.y.z where x is 1-3, y is 0-4, and z is 0-9

    Returns:
        str: A randomly generated user agent string.
    """
    lynx_version = f"Lynx/{random.randint(2, 3)}.{random.randint(8, 9)}.{random.randint(0, 2)}"
    libwww_version = f"libwww-FM/{random.randint(2, 3)}.{random.randint(13, 15)}"
    ssl_mm_version = f"SSL-MM/{random.randint(1, 2)}.{random.randint(3, 5)}"
    openssl_version = f"OpenSSL/{random.randint(1, 3)}.{random.randint(0, 4)}.{random.randint(0, 9)}"
    return f"{lynx_version} {libwww_version} {ssl_mm_version} {openssl_version}"
# Function to clean and format phone numbers
# Function to extract and format the first valid phone number
def format_phone_number(numbers):
    phone_pattern = re.compile(r'\+?\d{1,3}\s?\d{6,}')

    for number in numbers:
        match = phone_pattern.search(number)  # Find the first valid number
        if match:
            phone = match.group(0)

            # Remove unwanted characters
            phone = re.sub(r"[^\d+]", "", phone)

            # Convert leading "00" to "+"
            if phone.startswith("00"):
                phone = "+" + phone[2:]

            # Ensure it starts with '+'
            if not phone.startswith("+"):
                phone = "+" + phone

            # Format as +CC XXX-XXX-XXXX if possible
            phone = re.sub(r"(\+\d{1,3})\s?(\d{3})\s?(\d{3})\s?(\d{4})", r"\1 \2-\3-\4", phone)

            return phone  # Return only the first valid number

    return None  # Return None if no valid phone number is found
def extract_and_format_phone(text):
    if pd.isna(text) or not isinstance(text, str):
        return None

    # Remove any non-phone-related text (e.g., emails, names, or extra words)
    cleaned_text = re.sub(r"[A-Za-z@]+[\w.-]*", "", text)  # Remove emails and words

    # Regular expression to extract phone numbers
    phone_pattern = re.compile(r'\+?\d{1,3}[-\s]?\d{3}[-\s]?\d{3,4}[-\s]?\d{3,4}')

    match = phone_pattern.search(cleaned_text)  # Find the first valid phone number
    if match:
        phone = match.group(0)

        # Remove unwanted characters (spaces, hyphens, etc.)
        phone = re.sub(r"[^\d+]", "", phone)

        # Convert leading "00" to "+"
        if phone.startswith("00"):
            phone = "+" + phone[2:]

        # Ensure it starts with '+'
        if not phone.startswith("+"):
            phone = "+" + phone

        return phone  # Return phone number without spaces

    return None  # Return None if no valid phone number is found

# def format_phone_number(phone):
#     # Remove unwanted characters
#     phone = re.sub(r"[^\d+]", "", phone)

#     # Ensure country code starts with '+'
#     if phone.startswith("00"):  # Convert "00" prefix to "+"
#         phone = "+" + phone[2:]
#     elif phone.startswith("1") and len(phone) == 10:  # Format US numbers
#         phone = "+1 " + phone[:3] + "-" + phone[3:6] + "-" + phone[6:]
#     elif phone.startswith("+") and len(phone) > 10:  # Already in international format
#         phone = phone
#     elif len(phone) > 10:  # If country code is missing, assume it's international
#         phone = "+" + phone

#     # Standardize formatting: +CC XXX-XXX-XXXX
#     phone = re.sub(r"(\+\d{1,3})\s?(\d{3})\s?(\d{3})\s?(\d{4})", r"\1 \2-\3-\4", phone)

#     return phone
def _req(term, results, lang, start, proxies, timeout, safe, ssl_verify, region):
    resp = get(
        url="https://www.google.com/search",
        headers={
            "User-Agent": get_useragent(),
            "Accept": "*/*"
        },
        params={
            "q": term,
            "num": results + 2,  # Prevents multiple requests
            "hl": lang,
            "start": start,
            "safe": safe,
            "gl": region,
        },
        proxies=proxies,
        timeout=timeout,
        verify=ssl_verify,
        cookies = {
            'CONSENT': 'PENDING+987', # Bypasses the consent page
            'SOCS': 'CAESHAgBEhIaAB',
        }
    )
    resp.raise_for_status()
    return resp


class SearchResult:
    def __init__(self, url, title, description):
        self.url = url
        self.title = title
        self.description = description

    def __repr__(self):
        return f"SearchResult(url={self.url}, title={self.title}, description={self.description})"


def search(term, num_results=10, lang="en", proxy=None, advanced=False, sleep_interval=0, timeout=5, safe="active", ssl_verify=None, region=None, start_num=0, unique=False):
    """Search the Google search engine"""

    # Proxy setup
    proxies = {"https": proxy, "http": proxy} if proxy and (proxy.startswith("https") or proxy.startswith("http")) else None

    start = start_num
    fetched_results = 0  # Keep track of the total fetched results
    fetched_links = set() # to keep track of links that are already seen previously

    while fetched_results < num_results:
        # Send request
        resp = _req(term, num_results - start,
                    lang, start, proxies, timeout, safe, ssl_verify, region)

        # put in file - comment for debugging purpose
        # with open('google.html', 'w') as f:
        #     f.write(resp.text)

        # Parse
        soup = BeautifulSoup(resp.text, "html.parser")
        result_block = soup.find_all("div", class_="ezO2md")
        new_results = 0  # Keep track of new results in this iteration

        for result in result_block:
            # Find the link tag within the result block
            link_tag = result.find("a", href=True)
            # Find the title tag within the link tag
            title_tag = link_tag.find("span", class_="CVA68e") if link_tag else None
            # Find the description tag within the result block
            description_tag = result.find("span", class_="FrIlee")

            # Check if all necessary tags are found
            if link_tag and title_tag and description_tag:
                # Extract and decode the link URL
                link = unquote(link_tag["href"].split("&")[0].replace("/url?q=", "")) if link_tag else ""
            # Extract and decode the link URL
            link = unquote(link_tag["href"].split("&")[0].replace("/url?q=", "")) if link_tag else ""
            # Check if the link has already been fetched and if unique results are required
            if link in fetched_links and unique:
                continue  # Skip this result if the link is not unique
            # Add the link to the set of fetched links
            fetched_links.add(link)
            # Extract the title text
            title = title_tag.text if title_tag else ""
            # Extract the description text
            description = description_tag.text if description_tag else ""
            # Increment the count of fetched results
            fetched_results += 1
            # Increment the count of new results in this iteration
            new_results += 1
            # Yield the result based on the advanced flag
            if advanced:
                yield SearchResult(link, title, description)  # Yield a SearchResult object
            else:
                yield link  # Yield only the link

            if fetched_results >= num_results:
                break  # Stop if we have fetched the desired number of results

        if new_results == 0:
            #If you want to have printed to your screen that the desired amount of queries can not been fulfilled, uncomment the line below:
            #print(f"Only {fetched_results} results found for query requiring {num_results} results. Moving on to the next query.")
            break  # Break the loop if no new results were found in this iteration

        start += 10  # Prepare for the next set of results
        sleep(sleep_interval)

import random
import re
import pandas as pd
# Nimble API Proxy Credentials
NIMBLE_USERNAME = "account-jamshaid_arif_e49iri-pipeline-nimbleip"
NIMBLE_PASSWORD = "H7v75J65U1sK"
NIMBLE_SERVER = "ip.nimbleway.com"
NIMBLE_PORT = "7000"
search_query = 'site:facebbok.com ("@gmail.com" OR "@yahoo.com" OR "@outlook.com" OR "@hotmail.com" OR "@icloud.com" OR "@protonmail.com" OR "@aol.com" OR "@zoho.com" OR "@gmx.com" OR "@yandex.com" OR "@mail.com") "crypto"'

# List of cities to search

cities = [
        "Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide", "Gold Coast", "Canberra", "Newcastle", "Wollongong", "Logan City",
    "Geelong", "Hobart", "Townsville", "Cairns", "Darwin", "Toowoomba", "Ballarat", "Bendigo", "Launceston", "Mackay",
    "Rockhampton", "Bunbury", "Coffs Harbour", "Bundaberg", "Wagga Wagga", "Hervey Bay", "Mildura", "Shepparton", "Gladstone",
    "Tamworth", "Orange", "Port Macquarie", "Dubbo", "Geraldton", "Nowra", "Bathurst", "Blue Mountains", "Lismore", "Kalgoorlie",
    "Alice Springs", "Sunshine Coast", "Albany", "Mount Gambier", "Devonport", "Armidale", "Broken Hill", "Goulburn", "Echuca",
    "Warrnambool", "Whyalla", "Ballina", "Gympie", "Busselton", "Maryborough", "Batemans Bay", "Grafton", "Emerald", "Forster",
    "Victor Harbor", "Karratha", "Port Augusta", "Yeppoon", "Esperance", "Narrabri", "Kingaroy", "Parkes", "Inverell", "Muswellbrook",
    "Bowral", "Mudgee", "Singleton", "Taree", "Lithgow", "Griffith", "Moree", "Port Lincoln", "Roma", "Wangaratta",
    "Katherine", "Port Hedland", "Bairnsdale", "Mount Isa", "Warragul", "Morwell", "Gisborne", "Maitland", "Young", "Murray Bridge",
    "Torquay", "Carnarvon", "Stawell", "Burnie", "Cooma", "Colac", "Deniliquin", "Goondiwindi", "Swan Hill", "Horsham",
    "Narrandera", "Warwick", "Port Pirie", "Manjimup", "Yass", "Charters Towers"
]
# Google Drive API Credentials
SERVICE_ACCOUNT_FILE = "file.json"  # Ensure this is a valid file path
DRIVE_FOLDER_ID = "1MP5GR_GFxe8x4eEE-A-uOLaLPeq37Yg1"
# Search parameters
num_results = 1500  # Reduce to avoid being blocked
sleep_interval = 1  # Delay to prevent rate limiting
save_interval = 50  # Save every X searches to prevent data loss

# Regex patterns for email and phone extraction
email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
phone_pattern = r"\+?\d{1,4}?[-.\s]?\(?\d{2,4}?\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}"

# Master list to store all results
all_results = []


for city in cities:
    query = f"{search_query}"
    city_results = []

    print(f"\n🔍 Searching for investors in {city}...")

    try:
        for i, result in enumerate(search(query, sleep_interval=3, num_results=num_results,
                                          lang="en", proxy=get_new_proxy(), advanced=True)):
            try:
                print(f"✅ Found: {result.url}")

                # Ensure the description exists
                description = result.description if hasattr(result, "description") else ""

                # Extract emails and phone numbers
                emails = re.findall(email_pattern, description)
                phones = re.findall(phone_pattern, description)

                city_results.append((city, result.title, result.url, description, ", ".join(emails), ", ".join(phones)))
                all_results.append((city, result.title, result.url, description, ", ".join(emails), ", ".join(phones)))

                if i % save_interval == 0:
                    df_partial = pd.DataFrame(all_results, columns=["City", "Title", "URL", "Description", "Emails", "Phone Numbers"])
                    df=df_partial
                    df.drop_duplicates(inplace=True)

                    df = df[~df["Phone Numbers"].str.contains("@")]


                    df_partial['Description'] = df_partial['Description'].str.replace(r'\s+', ' ', regex=True)

                    df_partial['phone_number'] = df_partial['Description'].str.extract(f'({phone_pattern})')

                    df.reset_index(drop=True, inplace=True)

                    df.to_csv(f"Partial_data{city}.csv", index=False)
                    print("💾 Auto-saved partial data to 'Partial_data.csv'")

            except Exception as result_error:
                print(f"⚠️ Skipping result due to error: {result_error}")

    except Exception as e:
        print(f"❌ Error scraping {city}: {e}")

    time.sleep(sleep_interval)  # Prevent rapid requests

# Final save
if all_results:
    df = pd.DataFrame(all_results, columns=["City", "Title", "URL", "Description", "Emails", "Phone Numbers"])
    df.drop_duplicates(inplace=True)

                    # Remove emails from phone number column
    df = df[~df["Phone Numbers"].str.contains("@")]

    df.loc[df["Phone Numbers"].str.replace(r"\D", "", regex=True).str.len() < 7, "Phone Numbers"] = ""
    df['phone_number'] = df['Description'].str.extract(f'({phone_pattern})')
    # Reset index
    df.reset_index(drop=True, inplace=True)
    # Display cleaned phone numbers
    print(df)
    df = df.drop_duplicates(subset=['Emails'])
    df.to_csv("All_dataz.csv", index=False)
    # Upload to Google Drive
    def upload_to_drive(file_path, folder_id):
        file_name = os.path.basename(file_path)
        file_metadata = {"name": file_name, "parents": [folder_id]}
        
        file = open(file_path, "rb")  # Open file without 'with' block
        media = MediaIoBaseUpload(file, mimetype="text/csv", resumable=True)

        try:
            file_drive = drive_service.files().create(body=file_metadata, media_body=media, fields="id").execute()
            print(f"\n📂 File uploaded to Google Drive: {file_drive.get('id')}")
        finally:
            file.close()  # Manually close file after upload
    import os
    import json
    with open('file.json', 'r') as f:
        key_data = json.load(f)
    creds = service_account.Credentials.from_service_account_info(key_data, scopes=["https://www.googleapis.com/auth/drive"])
    drive_service = build("drive", "v3", credentials=creds)
    upload_to_drive('All_dataz.csv', DRIVE_FOLDER_ID)

    print("\n🎯 Scraping complete!")

    print("\n✅ All results saved to 'All_data.csv'")

print("\n🎯 Scraping complete!")
