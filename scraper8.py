import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pandas as pd
import random
import signal
import sys

# Define the search query tailored to target specific roles
query = 'site:linkedin.com/in/ ("Engineering Director" OR "Senior Director of Engineering" OR "Staff Engineer" OR "Principal Engineer") AND ("company size 250 to 2500" OR "mid-sized company") -Google -Amazon -Microsoft -Accenture -Deloitte -LinkedIn -Cloudflare -Uber -Stripe -Visa -Healthtech -Fintech'

# Chrome options setup to handle location and notifications
options = uc.ChromeOptions()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-notifications")  # Disable notifications
options.add_argument("--disable-geolocation")  # Disable location prompts
options.add_argument("--start-maximized")  # Start the browser maximized

# Preferences to further disable prompts
prefs = {
    "profile.default_content_setting_values.geolocation": 2,
    "profile.default_content_setting_values.notifications": 2,
    "profile.default_content_setting_values.media_stream_camera": 2,
    "profile.default_content_setting_values.media_stream_mic": 2,
}
options.add_experimental_option("prefs", prefs)

# Initialize the Chrome driver
driver = uc.Chrome(options=options)
driver.get("https://www.google.com")
time.sleep(2)

# Perform a Google search
try:
    search_box = driver.find_element(By.NAME, "q")
    search_box.send_keys(query)
    search_box.submit()
    print("Google search submitted successfully.")
except Exception as e:
    print(f"Error performing Google search: {e}")
    driver.quit()
    sys.exit()

# Lists to store scraped data
profile_links = []
names = []
roles = []
companies = []

# Define a list of big tech, consultancies, anti-vendor, and regulated companies to exclude
excluded_companies = [
    "Google", "Amazon", "Microsoft", "Accenture", "Deloitte", "LinkedIn", 
    "Cloudflare", "Uber", "Stripe", "Visa", "JP Morgan", "Goldman Sachs", 
    "PayPal", "Oracle", "IBM", "SAP"
]

# Function to extract profile links and snippets from Google search results
def extract_profile_data():
    soup = BeautifulSoup(driver.page_source, "html.parser")
    found_links = 0
    for result in soup.find_all('div', class_='g'):
        link_tag = result.find('a')
        href = link_tag.get('href') if link_tag else None

        # Only keep valid LinkedIn profile URLs
        if href and "linkedin.com/in/" in href and "/pub/dir/" not in href:
            clean_url = href.split('&')[0]
            if clean_url.startswith("http"):
                snippet = result.get_text(separator=' ')
                name, role, company = parse_snippet(snippet)

                # Filter profiles based on exclusions and relevance
                if (not any(excluded_company.lower() in company.lower() for excluded_company in excluded_companies) and
                    ("Engineering" in role or "Director" in role)):
                    profile_links.append(clean_url)
                    names.append(name)
                    roles.append(role)
                    companies.append(company)
                    found_links += 1

    print(f"Found {found_links} profile links on this page.")

# Function to parse snippet text for name, role, and company
def parse_snippet(snippet):
    words = snippet.split()
    name = "N/A"
    role = "N/A"
    company = "N/A"

    if " at " in snippet:
        parts = snippet.split(" at ")
        if len(parts) > 1:
            role = parts[0].strip()  # Text before "at" might contain the role
            company = parts[1].split('.')[0].strip()  # Text after "at" might contain the company name

    if len(words) > 2 and words[0].istitle() and words[1].istitle():
        name = f"{words[0]} {words[1]}"

    return name, role, company

# Function to save data to a CSV file
def save_data_to_csv():
    df = pd.DataFrame({
        "Name": names,
        "Current Role": roles,
        "Company": companies,
        "Profile Link": profile_links
    })
    output_filename = f'linkedin_profiles_{time.strftime("%Y%m%d_%H%M%S")}.csv'
    df.to_csv(output_filename, index=False)
    print(f"Data saved to {output_filename}.")

# Signal handler for keyboard interrupt
def signal_handler(sig, frame):
    print("\nKeyboardInterrupt detected. Saving data before exit...")
    save_data_to_csv()
    driver.quit()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Main scraping loop
try:
    page_count = 0
    max_pages = 25

    while page_count < max_pages:
        print(f"Scraping page {page_count + 1} of Google results.")
        extract_profile_data()
        page_count += 1

        try:
            next_button = driver.find_element(By.ID, "pnnext")
            if next_button.is_displayed():
                driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                next_button.click()
                time.sleep(random.uniform(5, 10))
            else:
                print("No 'Next' button found; ending pagination.")
                break
        except Exception as e:
            print(f"Error clicking 'Next' button or no more pages: {e}")
            break

except KeyboardInterrupt:
    print("\nInterrupted by user.")
    save_data_to_csv()

save_data_to_csv()
driver.quit()
