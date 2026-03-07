import sqlite3
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- Configuration ---
DB_NAME = "scholarships.db"
URL_TO_SCRAPE = "https://www.scholarshipscanada.com/Scholarships/ScholarshipSearch.aspx?type=ScholarshipName&s="

# --- Mock User Profile for Filtering ---
user_profile = {
    "field_of_study": "computer science",
    "gpa": 3.5,
    "year_of_study": 2
}

def setup_database():
    """Create the SQLite database and table if they don't exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scholarships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            amount TEXT,
            deadline TEXT,
            url TEXT,
            match_score INTEGER
        )
    ''')
    conn.commit()
    return conn

def calculate_match_score(scholarship_name, amount, user_prof):
    """
    Very basic mock matching logic.
    A more robust solution would NLP or deeper scraping of eligibility criteria.
    """
    score = 0
    name_lower = scholarship_name.lower()
    
    # Example: Boost score if field of study is in the name
    if user_prof["field_of_study"] in name_lower or "technology" in name_lower or "stem" in name_lower:
        score += 50
    
    # Generic scholarships get a baseline score
    if score == 0:
        score = 10
        
    return score

def save_scholarship(conn, data):
    """Insert a scholarship record into the database."""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO scholarships (name, amount, deadline, url, match_score)
        VALUES (?, ?, ?, ?, ?)
    ''', (data['name'], data['amount'], data['deadline'], data['url'], data['match_score']))
    conn.commit()

def scrape_scholarships():
    """Main scraping function using Selenium."""
    print("Setting up Selenium WebDriver...")
    
    # Setup Chrome options
    chrome_options = Options()
    # Uncomment the next line to run headless
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # Adding a user-agent helps bypass basic bot detection
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    # Initialize WebDriver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    conn = setup_database()
    
    try:
        print(f"Navigating to {URL_TO_SCRAPE}...")
        driver.get(URL_TO_SCRAPE)
        
        # Wait for the results container to load (adjust selector based on actual site structure)
        # Assuming there's a table or list holding the results. We wait for an item to be present.
        print("Waiting for results to load...")
        try:
             WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'table-responsive')]//table//tbody//tr"))
             )
        except Exception as e:
             print("Timeout waiting for data to load. The structure might be different.")
             print(driver.page_source[:500]) # Print snippet for debugging if it fails
             return
             
        # Find the rows containing the scholarship data
        # *Note*: These selectors are speculative until we can inspect the active page
        rows = driver.find_elements(By.XPATH, "//div[contains(@class, 'table-responsive')]//table//tbody//tr")
        print(f"Found {len(rows)} potential scholarship rows.")
        
        saved_count = 0
        
        for row in rows:
            try:
                # Extract columns - these indexes might need adjustment
                cols = row.find_elements(By.TAG_NAME, "td")
                
                if len(cols) >= 3:
                     # Usually Name is the first meaningful column and contains a link
                     name_element = cols[0].find_element(By.TAG_NAME, "a")
                     name = name_element.text.strip()
                     url = name_element.get_attribute("href")
                     
                     amount = cols[1].text.strip()
                     deadline = cols[2].text.strip()
                     
                     match_score = calculate_match_score(name, amount, user_profile)
                     
                     # Only save if it's considered a decent match
                     if match_score >= 10:
                        data = {
                            "name": name,
                            "amount": amount,
                            "deadline": deadline,
                            "url": url,
                            "match_score": match_score
                        }
                        save_scholarship(conn, data)
                        saved_count += 1
                        print(f"Saved match: {name} (Score: {match_score})")
                        
            except Exception as row_err:
                 print(f"Error parsing a row: {row_err}")
                 continue
                 
        print(f"\nScraping complete! Saved {saved_count} matching scholarships to the database.")

    except Exception as e:
        print(f"An error occurred during scraping: {e}")
    finally:
        print("Closing browser and database connection...")
        driver.quit()
        conn.close()

if __name__ == "__main__":
    scrape_scholarships()
