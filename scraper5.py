from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
import csv
from datetime import datetime
import time
import random

# Function to scrape Google search results
def scrape_google(query, pages_to_scrape):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Set headless=False to see the browser
        context = browser.new_context(viewport={"width": 1920, "height": 1080})  # Maximizing the window
        page = context.new_page()

        # Apply stealth to the page
        stealth_sync(page)

        # Open Google
        page.goto("https://www.google.com", timeout=60000)  # Increased timeout

        # Debugging: Check if Google homepage loaded
        print("Checking if Google homepage is loaded...")
        try:
            page.wait_for_selector("input[name='q']", timeout=15000)  # Wait for the search input
            print("Google search input found.")
        except Exception as e:
            print(f"Error: {e}")
            browser.close()
            return

        # Accept cookies or handle any initial prompts
        try:
            print("Attempting to accept cookies...")
            page.wait_for_selector("button:has-text('Accept all')", timeout=5000)
            accept_button = page.locator("button:has-text('Accept all')")
            accept_button.click()
            time.sleep(random.uniform(2, 4))  # Random delay to mimic human behavior
        except:
            print("No cookie acceptance required or unable to find the button.")

        # Fill search query and submit
        try:
            print("Filling search query...")
            search_box = page.locator("input[name='q']")
            search_box.fill(query)
            search_box.press("Enter")
            time.sleep(random.uniform(2, 4))  # Random delay to mimic human behavior
        except Exception as e:
            print(f"Error filling the search query: {e}")
            browser.close()
            return

        # Prepare CSV file for output
        filename = f"google_search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Title', 'URL'])

            # Scrape specified number of pages
            for page_number in range(pages_to_scrape):
                print(f"Scraping page {page_number + 1}")

                # Wait for results to load
                try:
                    page.wait_for_selector("div.g", timeout=10000)  # Wait for search results
                    results = page.locator("div.g")
                    if results.count() == 0:
                        print("No search results found.")
                        break
                except Exception as e:
                    print(f"Error finding search results: {e}")
                    break

                # Extract search results
                for i in range(results.count()):
                    try:
                        # Extract title and URL
                        title = results.nth(i).locator("h3").inner_text()
                        url = results.nth(i).locator("a").get_attribute("href")
                        writer.writerow([title, url])
                        print(f"Found: {title} - {url}")  # Debugging print
                    except Exception as e:
                        print(f"Error extracting result {i}: {e}")

                # Click 'Next' to go to the next page of results
                try:
                    print("Attempting to click 'Next' button...")
                    page.wait_for_selector("a#pnnext", timeout=10000)  # Wait for 'Next' button
                    next_button = page.locator("a#pnnext")
                    next_button.click()
                    time.sleep(random.uniform(2, 4))  # Random delay
                except Exception as e:
                    print(f"Error navigating to next page: {e}")
                    break

        print(f"Scraping completed. Results saved to {filename}")
        browser.close()

# Example usage
scrape_google("site:linkedin.com/in/ Vice President Technology", 25)  # Set the number of pages to scrape
