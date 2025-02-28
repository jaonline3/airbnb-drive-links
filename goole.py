from io import BytesIO
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import time
import random
import re
import pandas as pd
# Nimble API Proxy Credentials
NIMBLE_USERNAME = "account-asf_mawm03-pipeline-nimbleip"
NIMBLE_PASSWORD = "3m70gRi643Rm"
NIMBLE_SERVER = "ip.nimbleway.com"
NIMBLE_PORT = "7000"

# List of cities to search

cities = [
        "Hialeah"]
# Google Drive API Credentials
SERVICE_ACCOUNT_FILE = "file.json"  # Ensure this is a valid file path
DRIVE_FOLDER_ID = "1MP5GR_GFxe8x4eEE-A-uOLaLPeq37Yg1"
# Search parameters
num_results = 15  # Reduce to avoid being blocked
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
