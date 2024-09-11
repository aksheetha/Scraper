import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import pandas as pd
import random
import signal
import sys

# Define the Google search query to find LinkedIn profiles
query = "site:linkedin.com/in/ Staff Engineer"

# Set up Chrome options for undetected_chromedriver
options = uc.ChromeOptions()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-notifications")  # Disable notifications
options.add_argument("--disable-geolocation")  # Disable location prompts
options.add_argument("--start-maximized")  # Start the browser maximized

# Initialize the undetected Chrome driver
driver = uc.Chrome(options=options)
driver.maximize_window()  # Ensure the window is maximized
driver.get("https://www.google.com")
time.sleep(2)  # Added delay to ensure the page loads

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

# Define a list of known large companies to exclude
large_companies = [
    "Google", "Amazon", "Microsoft", "Apple", "Facebook", "Meta", 
    "Netflix", "Tesla", "IBM", "Oracle", "Salesforce", "Intel",
    "Accenture", "Deloitte", "PwC", "EY", "KPMG", "McKinsey",
    # Add more large companies as needed
]

# Keywords to identify profiles from IT or tech-related companies
tech_keywords = [
    "Software", "Tech", "Information Technology", "IT", "Engineering",
    "Cloud", "Cybersecurity", "Data", "AI", "Machine Learning", "Development", "Full-Stack", "Backend"
    # Add more relevant keywords as needed
]

# Function to extract profile links and snippets from Google search results
def extract_profile_data():
    soup = BeautifulSoup(driver.page_source, "html.parser")
    found_links = 0  # Track the number of profile links found
    for result in soup.find_all('div', class_='g'):  # Each search result is in a div with class 'g'
        link_tag = result.find('a')
        href = link_tag.get('href') if link_tag else None

        # Only keep valid LinkedIn profile URLs
        if href and "linkedin.com/in/" in href and "/pub/dir/" not in href:
            clean_url = href.split('&')[0]  # Clean up the URL
            if clean_url.startswith("http"):  # Ensure the URL is valid
                snippet = result.get_text(separator=' ')
                name, role, company = parse_snippet(snippet)

                # Filter by company size and industry
                if is_mid_sized_company(company) and is_tech_industry(snippet):
                    profile_links.append(clean_url)
                    names.append(name)
                    roles.append(role)
                    companies.append(company)
                    found_links += 1

    print(f"Found {found_links} profile links on this page.")

# Function to parse the snippet text for name, role, and company
def parse_snippet(snippet):
    # Simple heuristic-based approach to extract potential name, role, and company
    words = snippet.split()
    name = "N/A"
    role = "N/A"
    company = "N/A"

    # Attempt to find typical patterns for names, roles, and companies
    # This is a heuristic approach; parsing may need refinement based on observed patterns
    if " at " in snippet:
        parts = snippet.split(" at ")
        if len(parts) > 1:
            role = parts[0].strip()  # Text before "at" might contain the role
            company = parts[1].split('.')[0].strip()  # Text after "at" might contain the company name

    # Check for a name in the first few words of the snippet
    if len(words) > 2 and words[0].istitle() and words[1].istitle():
        name = f"{words[0]} {words[1]}"

    return name, role, company

# Function to check if the company is mid-sized (i.e., not a known large company)
def is_mid_sized_company(company):
    return company and all(large_company.lower() not in company.lower() for large_company in large_companies)

# Function to check if the profile is likely from the tech/IT industry
def is_tech_industry(snippet):
    return any(keyword.lower() in snippet.lower() for keyword in tech_keywords)

# Function to save data to a CSV file
def save_data_to_csv():
    # Save the results to a CSV file
    df = pd.DataFrame({
        "Name": names,
        "Current Role": roles,
        "Company": companies,
        "Profile Link": profile_links
    })
    # Save to CSV with a unique name based on the current time
    output_filename = f'linkedin_profiles_{time.strftime("%Y%m%d_%H%M%S")}.csv'
    df.to_csv(output_filename, index=False)
    print(f"Data saved to {output_filename}.")

# Signal handler for keyboard interrupt
def signal_handler(sig, frame):
    print("\nKeyboardInterrupt detected. Saving data before exit...")
    save_data_to_csv()
    driver.quit()
    sys.exit(0)

# Register the signal handler
signal.signal(signal.SIGINT, signal_handler)

# Main scraping loop
try:
    page_count = 0  # Track the number of pages scraped
    max_pages = 50  # Set a limit for the number of pages to scrape

    # Scrape links from multiple pages of Google results
    while page_count < max_pages:
        print(f"Scraping page {page_count + 1} of Google results.")
        extract_profile_data()
        page_count += 1

        # Check for the "Next" button and click if available
        try:
            next_button = driver.find_element(By.ID, "pnnext")
            if next_button.is_displayed():
                next_button.click()
                time.sleep(random.uniform(5, 10))  # Random delay to mimic human behavior
            else:
                print("No 'Next' button found; ending pagination.")
                break
        except Exception as e:
            print(f"Error clicking 'Next' button or no more pages: {e}")
            break

except KeyboardInterrupt:
    # Handle unexpected keyboard interrupt
    print("\nInterrupted by user.")
    save_data_to_csv()

# Save data if completed normally
save_data_to_csv()

# Close the browser
driver.quit()
