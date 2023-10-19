from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import re
import pandas as pd
from bs4 import BeautifulSoup
import warnings

warnings.filterwarnings("ignore")

# Function to extract and process data from the current page
def process_page(driver, final_df):
    # Locate the first table on the page using XPath
    table = driver.find_element(By.XPATH, '//table')
    # Extract the HTML content of the table
    table_html = table.get_attribute("outerHTML")
    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(table_html, 'html.parser')

    # Find the <pre><strong> element that contains your data
    pre_strong = soup.find('pre')

    # Extract the text data from the <pre><strong> element
    data = pre_strong.get_text()

    # Split the data into lines
    lines = data.strip().split('\n')

    # Split each line into columns based on the "|" delimiter
    table_data = [line.split('|') for line in lines]

    # Create a DataFrame from the table data
    df = pd.DataFrame(table_data)

    # Clean up the DataFrame by removing any leading or trailing spaces
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    # Delete the first four rows (index 0 to 3)
    df = df.drop(index=range(4))

    # Delete the first and last columns
    df = df.drop(df.columns[[0, -1]], axis=1)

    # Reset the index to start from 0
    df = df.reset_index(drop=True)

    # Append the table data to the final_df
    final_df = pd.concat([final_df, df], ignore_index=True)

    return final_df

# Set up Chrome WebDriver
options = Options()
options.add_argument("--headless")  # Run Chrome in headless mode (without opening a browser window)
driver = webdriver.Chrome(options=options)

# Navigate to the page
url = "http://ned.ipac.caltech.edu/forms/OBJatt.html"
driver.get(url)
element = driver.find_element(By.XPATH, '//a[@href="javascript:unhide(\'selectOUT\');"]')
# Click the element using JavaScript
driver.execute_script('arguments[0].click();', element)
# Find the checkbox element by its attributes
checkbox = driver.find_element(By.NAME,'NO_LINKS')

checkbox.click()
# Find the checkbox element by its attributes
checkbox = driver.find_element(By.XPATH,"//input[@type='checkbox' and @name='M' and @value='1234']")
checkbox.click()

submit_button = driver.find_element(By.XPATH, "//input[@type='submit'][@value='Submit Query']")
submit_button.click()

# Get the page source
page_source = driver.page_source

# Use regular expressions to find the text
page_info_pattern = r'Page \d+ of \d+'
page_info_match = re.search(page_info_pattern, page_source)

if page_info_match:
    page_info_text = page_info_match.group(0)
    page_number, total_pages = [int(part) for part in re.findall(r'\d+', page_info_text)]
    print("Page Number:", page_number)
    print("Total Pages:", total_pages)
else:
    # Handle case when the text is not found
    page_info_text = "Page information not found"

current_page = 1  # Start from page 1
final_df = pd.DataFrame()

while True:
    print(f"Processing page {current_page}/{total_pages}")

    final_df = process_page(driver, final_df)
    print('Size of final_df:', final_df.shape)

    if current_page == total_pages:
        break  # Break out of the loop if you're on the last page

    links = driver.find_elements(By.XPATH, '//a[contains(@href, "/cgi-bin/OBJatt?")]')

    # Access the last link in the list and click it
    if links:
        last_link = links[-1]
        last_link.click()

    current_page += 1  # Increment the current page number

print("Scraping complete.")

# final_df.columns = ["row","Essential Note", "Object Name", "RA", "Dec", "Object Type", "Redshift", "z Qual", "Galaxy Morphology","Activity Type","Row"]

final_df.to_csv('Galaxy_Morphology_S0_Catalogue.csv', index=False)
driver.quit()  # Close the browser
