import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import pandas as pd
import random

# Define the Google search query to find LinkedIn profiles
query = "site:linkedin.com/in/ Staff Engineer"

# Set up Chrome options for undetected_chromedriver
options = uc.ChromeOptions()
# Remove '--headless' to make the browser visible
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")

# Initialize the undetected Chrome driver
driver = uc.Chrome(options=options)
driver.get("https://www.google.com")

# Perform a Google search
search_box = driver.find_element(By.NAME, "q")
search_box.send_keys(query)
search_box.submit()

# Lists to store scraped data
names = []
job_titles = []
profile_links = []

# Function to extract profile links from Google search results
def extract_profile_links():
    soup = BeautifulSoup(driver.page_source, "html.parser")
    for link in soup.select('a'):
        href = link.get('href')
        # Only keep valid LinkedIn profile URLs
        if href and "linkedin.com/in/" in href and "/pub/dir/" not in href:
            clean_url = href.split('&')[0]  # Clean up the URL
            if clean_url.startswith("http"):  # Ensure the URL is valid
                profile_links.append(clean_url)

# Function to extract name and job title from LinkedIn profiles
def extract_profile_details(url):
    try:
        driver.get(url)
        time.sleep(random.uniform(2, 4))  # Delay to mimic human behavior
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Extract name and job title based on LinkedIn's public profile layout
        name = soup.find("h1", class_="text-heading-xlarge")
        job_title = soup.find("div", class_="text-body-medium")

        # Append data if found
        names.append(name.text.strip() if name else "N/A")
        job_titles.append(job_title.text.strip() if job_title else "N/A")
    except Exception as e:
        print(f"Error extracting profile details from {url}: {e}")

# Scrape links from multiple pages of Google results
for _ in range(3):  # Adjust range for more pages if needed
    extract_profile_links()
    try:
        # Click the "Next" button to go to the next page of Google search results
        next_button = driver.find_element(By.ID, "pnnext")
        next_button.click()
        time.sleep(random.uniform(5, 10))  # Random delay to mimic human behavior
    except Exception as e:
        print("No more pages or error clicking next:", e)
        break

# Extract details from each LinkedIn profile link found
for link in profile_links:
    extract_profile_details(link)

# Save the results to a CSV file
df = pd.DataFrame({
    "Name": names,
    "Current Job": job_titles,
    "Profile Link": profile_links
})

# Save to CSV with a unique name based on the current time
output_filename = f'linkedin_profiles_{time.strftime("%Y%m%d_%H%M%S")}.csv'
df.to_csv(output_filename, index=False)
print(f"Scraping completed. Data saved to {output_filename}.")

# Close the browser
driver.quit()
