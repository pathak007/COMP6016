from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import re
import pandas as pd
from bs4 import BeautifulSoup
import warnings

def setup_driver():
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    return driver

def navigate_to_page(driver, checkbox_value):
    url = "http://ned.ipac.caltech.edu/forms/OBJatt.html"
    driver.get(url)
    element = driver.find_element(By.XPATH,'//a[@href="javascript:unhide(\'selectOUT\');"]')
    driver.execute_script('arguments[0].click();', element)
    checkbox = driver.find_element(By.XPATH,f"//input[@type='checkbox' and @name='M' and @value='{checkbox_value}']")
    checkbox.click()
    submit_button = driver.find_element(By.XPATH, "//input[@type='submit'][@value='Submit Query']")
    submit_button.click()

def extract_page_info(page_source):
    page_info_pattern = r'Page \d+ of \d+'
    page_info_match = re.search(page_info_pattern, page_source)

    if page_info_match:
        page_info_text = page_info_match.group(0)
        page_number, total_pages = [int(part) for part in re.findall(r'\d+', page_info_text)]
        return page_number, total_pages
    else:
        return None, None

def process_page_data(driver, final_df):
    table = driver.find_element(By.XPATH, '//table')
    table_html = table.get_attribute("outerHTML")
    soup = BeautifulSoup(table_html, 'html.parser')
    pre_strong = soup.find('pre')
    data = pre_strong.get_text()
    lines = data.strip().split('\n')

    table_data = []

    for line in lines:
        if not re.match(r'^\|+$', line):
            row = re.split(r'(?<!\|)\|', line)
            row = [cell.strip() for cell in row]
            table_data.append(row)

    df = pd.DataFrame(table_data)
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    df = df.drop(index=range(4))
    df = df.drop(df.columns[[0, 1, -1]], axis=1)
    df = df.reset_index(drop=True)

    final_df = pd.concat([final_df, df], ignore_index=True)
    return final_df

warnings.filterwarnings("ignore")

# Define the values of checkboxes you want to scrape
checkbox_values = {
    "1234": "S0",
    "1168": "S",
    "1250": "S0a"
}

for checkbox_value, abbreviation in checkbox_values.items():
    driver = setup_driver()
    navigate_to_page(driver, checkbox_value)
    page_source = driver.page_source
    page_number, total_pages = extract_page_info(page_source)

    current_page = 1
    final_df = pd.DataFrame()

    while True:
        print(f"Processing page {current_page}/{total_pages}")
        final_df = process_page_data(driver, final_df)
        print('Size of final_df:', final_df.shape)

        if current_page == total_pages:
            break

        links = driver.find_elements(By.XPATH, '//a[contains(@href, "/cgi-bin/OBJatt?")]')

        if links:
            last_link = links[-1]
            last_link.click()

        current_page += 1

    final_df.columns = [ "Object Name", "RA", "Dec", "Object Type", "Redshift", "z Qual", "Galaxy Morphology", "Activity Type"]
    driver.quit()

    # Save the data to a CSV file with a name based on the checkbox value
    csv_filename = f'Galaxy_Morphology_{abbreviation}_Catalogue.csv'
    final_df.to_csv(csv_filename, index=False)
