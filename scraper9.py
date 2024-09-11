import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import pandas as pd
import random
import signal
import sys

# Define the Google search query to find LinkedIn profiles
query = "site:linkedin.com/in/ Engineering Mentor"

# Set up Chrome options for undetected_chromedriver
options = uc.ChromeOptions()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-notifications")  # Disable notifications
options.add_argument("--disable-geolocation")  # Disable location prompts
options.add_argument("--start-maximized")  # Start the browser maximized

def initialize_driver():
    driver = uc.Chrome(options=options)
    driver.maximize_window()
    driver.get("https://www.google.com")
    time.sleep(5)  # Increased delay to ensure the page loads properly
    return driver

driver = initialize_driver()

# Lists to store scraped data
profile_links = []
names = []
roles = []
companies = []

# Function to extract profile links and snippets from Google search results
def extract_profile_data():
    soup = BeautifulSoup(driver.page_source, "html.parser")
    found_links = 0  # Track the number of profile links found
    results_divs = soup.find_all('div', class_='g')

    if not results_divs:
        print("No search result divs found. Page structure may have changed.")
        return

    for result in results_divs:  # Each search result is in a div with class 'g'
        link_tag = result.find('a')
        href = link_tag.get('href') if link_tag else None

        # Only keep valid LinkedIn profile URLs
        if href and "linkedin.com/in/" in href and "/pub/dir/" not in href:
            clean_url = href.split('&')[0]  # Clean up the URL
            if clean_url.startswith("http"):  # Ensure the URL is valid
                profile_links.append(clean_url)
                found_links += 1

                # Extract snippets containing potential names, roles, and companies
                snippet = result.get_text(separator=' ')
                name, role, company = parse_snippet(snippet)
                names.append(name)
                roles.append(role)
                companies.append(company)

    print(f"Found {found_links} profile links on this page.")

# Function to parse the snippet text for name, role, and company
def parse_snippet(snippet):
    # Simple heuristic-based approach to extract potential name, role, and company
    words = snippet.split()
    name = "N/A"
    role = "N/A"
    company = "N/A"

    # Attempt to find typical patterns for names, roles, and companies
    if " at " in snippet:
        parts = snippet.split(" at ")
        if len(parts) > 1:
            role = parts[0].strip()  # Text before "at" might contain the role
            company = parts[1].split('.')[0].strip()  # Text after "at" might contain the company name

    # Check for a name in the first few words of the snippet
    if len(words) > 2 and words[0].istitle() and words[1].istitle():
        name = f"{words[0]} {words[1]}"

    return name, role, company

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
    max_pages_per_session = 10  # Set a limit for the number of pages to scrape before refreshing

    while True:
        print(f"Scraping page {page_count + 1} of Google results.")
        extract_profile_data()
        page_count += 1

        # Check if we've reached the max pages per session
        if page_count % max_pages_per_session == 0:
            print("Reached page limit. Restarting session...")
            save_data_to_csv()
            driver.quit()
            driver = initialize_driver()  # Reinitialize the driver
            time.sleep(random.uniform(10, 20))  # Wait before restarting the scraping

        # Check for the "Next" button and click if available
        try:
            next_button = driver.find_element(By.ID, "pnnext")
            if next_button.is_displayed():
                driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
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
