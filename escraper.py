import re
import requests
import csv
import time
from bs4 import BeautifulSoup
import pandas as pd

# Base URLs
BASE_URL = "https://directory.nationalrestaurantshow.com/8_0/ajax/remote-proxy.cfm"
DETAILS_URL = "https://directory.nationalrestaurantshow.com/8_0/exhibitor/exhibitor-details.cfm?exhid="

# Headers to mimic a real browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest"
}

PAGE_HEADERS = {
    "Host": "directory.nationalrestaurantshow.com",
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:136.0) Gecko/20100101 Firefox/136.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Referer": "https://directory.nationalrestaurantshow.com/8_0/explore/exhibitor-gallery.cfm?featured=false",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Priority": "u=0, i",
    "Cookie": "CFID=66799023; CFTOKEN=40fe4c18a98ceb3f-9B31357D-AD36-C169-52C1CE55C548220D; _ga_N77RQK6L8Y=GS1.1.1741869627.5.1.1741869820.0.0.0; _ga=GA1.1.710678864.1741847012; _gcl_au=1.1.1635033506.1741847013; _ga_6XM43FTVR2=GS1.1.1741847014.1.1.1741869820.0.0.0; _gid=GA1.2.254562019.1741847015; _iris_cdl=aW5mb3JtYWNvbm5lY29ubmVjdC5jb20,Y3NwZGFpbHluZXdzLmNvbQ==,Zm9vZHNlcnZpY2VkaXJlY3Rvci5jb20=,cmVzdGF1cmFudGJ1c2luZXNzb25saW5lLmNvbQ==,Y2F0ZXJzb3VyY2UuY29t,bnJuLmNvbQ==,cmVzdGF1cmFudC1ob3NwaXRhbGl0eS5jb20=,c3VwZXJtYXJrZXRuZXdzLmNvbQ==; _sp_id.ad5c=b4b732ca-0ae3-4ed7-b7c1-dff85da0ebfe.1741847016.4.1741869826.1741863552.ec5307b5-3f20-4a0d-b19c-82433bf46856.5c961259-846b-4052-b896-9846e463a47d.ddfa2912-f9ab-47e7-bfd4-8510333bdc9d.1741869629654.15; _mkto_trk=id:561-ZNP-897&token:_mch-nationalrestaurantshow.com-13dbde20a671279537a1b2644b1da306; _fbp=fb.1.1741847016882.419994509337701250; __td_signed=true; _iris_duid=b4b732ca-0ae3-4ed7-b7c1-dff85da0ebfe; feathr_session_id=67d2d23d31951a33b31385d0; _td=7cec723d-724c-44d8-a4c7-f678d57226bd"
}
# Fetch exhibitors from the API
def fetch_exhibitors():
    params = {
        "action": "search",
        "searchtype": "exhibitorgallery",
        "searchsize": "1796",  # Adjust size as needed
        "start": "0"
    }
    
    response = requests.get(BASE_URL, headers=HEADERS, params=params, timeout=10)
    
    if response.status_code == 200:
        try:
            data = response.json()
            return data.get("DATA", {}).get("results", {}).get("exhibitor", {}).get("hit", [])
        except Exception as e:
            print("JSON Parsing Error:", e)
            return []
    else:
        print("Error fetching exhibitors:", response.status_code)
        return []

# Extract additional details from the exhibitor's page
def fetch_exhibitor_details(exhibitor_id):
    url = DETAILS_URL + exhibitor_id
    response = requests.get(url, headers=HEADERS, timeout=10)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Extract website URL
        website = soup.select_one("a[href^='http']")
        website_url = website["href"] if website else "N/A"

        # Extract product category
        category = soup.select_one(".exhibitor-categories")
        product_category = category.text.strip() if category else "N/A"

        # Extract phone number
        phone = soup.find("span", class_="phone")
        phone_number = phone.text.strip() if phone else ""

        # Extract emails
        emails = []
        for link in soup.find_all("a", href=True):
            if "mailto:" in link["href"]:
                emails.append(link["href"].replace("mailto:", "").strip())

        return website_url, product_category, phone_number, ", ".join(emails)
    
    return "N/A", "N/A", "", ""

# Save exhibitors to a CSV file
def save_to_csv(exhibitors):
    with open("e_exhibitors.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Name", "Booth", "Description", "Image", "Link", "website", "product_categories", "Phone Numbers", "Emails"])

        for exhibitor in exhibitors:
            fields = exhibitor.get("fields", {})
            name = fields.get("exhname_t", "N/A")
            booth = ", ".join(fields.get("booths_la", []))
            description = fields.get("exhdesc_t", "N/A").strip()
            image = fields.get("exhlogo_t", "N/A")
            exhibitor_id = fields.get("exhid_l", "N/A")
            exhibitor_link = f"{DETAILS_URL}{exhibitor_id}"

            # Fetch additional details
            website_url, product_category, phone_numbers, emails = fetch_exhibitor_details(exhibitor_id)

            writer.writerow([name, booth, description, image, exhibitor_link, website_url, product_category, phone_numbers, emails])
            print(f"Saved: {name}")

            # time.sleep(1)  # Prevent getting blocked
def extract_exhibitor_info(df):
    """
    Extracts additional exhibitor info from each exhibitor's link and updates the DataFrame.
    """
    # Ensure the new columns exist with empty values before extraction
    for col in ['product_categories', 'industry_segments', 'address', 'website', 'email', 'phone', 'fax', 'instagram', 'facebook', 'twitter', 'linkedin']:
        if col not in df.columns:
            df[col] = ""

    for index, row in df.iterrows():
        exhibitor_url = row['Link']  # Assuming the column name is 'Link'
        print(f"Loading data for {row['Name']}....")
        if not exhibitor_url:
            continue
        
        response = requests.get(exhibitor_url, headers=PAGE_HEADERS)
        print(f"Fetching {exhibitor_url} - Status Code: {response.status_code}")
        
        if response.status_code != 200:
            continue
        
        soup = BeautifulSoup(response.text, 'lxml')
        # print(soup.prettify())  # Print full HTML to check structure

        
        print(f"Extracting categories for {row['Name']}....")
        # Extract product categories
        categories_section = soup.find('article', id='js-vue-products')
        if categories_section:
            categories = [a.text.strip() for a in categories_section.find_all('a')]
        else:
            categories = []
        # print(f"Extracted Categories: {categories}")
        
        
        print(f"Extracting industry segments for {row['Name']}....")
        # Extract industry segments
        industry_section = soup.find('article', id='js-vue-georegions')
        industry_segments = [a.text for a in industry_section.find_all('a')] if industry_section else []
        # print(f"Extracted Industry Segments: {industry_segments}")
         
        print(f"Extracting company address for {row['Name']}....")    
        print(f"Extracting website URL for {row['Name']}....")    
        # Extract company address
        
        # Find the script containing "contactinfov3"
        script_tag = None
        for script in soup.find_all('script'):
            if 'contactinfov3' in script.text:
                script_tag = script.text
                break

        if not script_tag:
            print(f"No contactinfov3 script found for {row['Name']}")
            continue

        # Extract JSON-like data using regex
        match = re.search(r'addressValues:\s*(\{.*?\}),\s*websiteValue:\s*"([^"]+)",\s*instagramValue:\s*"([^"]*)",\s*facebookValue:\s*"([^"]*)",\s*twitterValue:\s*"([^"]*)",\s*linkedInValue:\s*"([^"]*)",\s*emailValue:\s*"([^"]*)",\s*phoneValue:\s*"([^"]*)",\s*faxValue:\s*"([^"]*)"', script_tag, re.DOTALL )
        if not match:
            print(f"Failed to extract data for {row['Name']}")
            continue

        address_json, website, instagram, facebook, twitter, linkedin, email, phone, fax = match.groups()
        
        df.at[index, 'product_categories'] = ', '.join(categories)
        df.at[index, 'industry_segments'] = ', '.join(industry_segments)
        df.at[index, 'address'] = address_json
        df.at[index, 'website'] = website.replace("\\/", "/")
        df.at[index, 'instagram'] = instagram.replace("\\/", "/")
        df.at[index, 'facebook'] = facebook.replace("\\/", "/")
        df.at[index, 'twitter'] = twitter.replace("\\/", "/")
        df.at[index, 'linkedin'] = linkedin.replace("\\/", "/")
        df.at[index, 'email'] = email
        df.at[index, 'phone'] = phone
        df.at[index, 'fax'] = fax
        
        print(df.columns)
        print("Done!\n-----------------------------------------------------------------------------")
    
    return df
# Main Execution
exhibitors = fetch_exhibitors()
if exhibitors:
    print(f"Total Exhibitors Found: {len(exhibitors)}")
    save_to_csv(exhibitors)
    print("Data saved to exhibitors.csv ")
else:
    print("No exhibitors found ")


# Load CSV file
df = pd.read_csv("exhibitors.csv")
print(df.shape)
# test_df = df.copy()
# get exhibitors data
result_df = extract_exhibitor_info(df)

# sort by number of null values
# result_df.sort_values(by=result_df.isnull().sum(axis=1))

result_df.to_csv("exhibitors_with_extracted_data.csv", index=False)


print(result_df.head(5))