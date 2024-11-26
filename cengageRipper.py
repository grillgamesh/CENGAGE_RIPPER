import time
import json
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
import os
from ebooklib import epub
from bs4 import BeautifulSoup
import py2web
global counter
# Setup Tesseract OCR path if necessary
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Adjust based on your installation

# Setup the Firefox WebDriver
options = webdriver.FirefoxOptions()
options.headless = False  # Set to True if you want the browser to run in headless mode (without UI)

# Optionally, you can add the extension automatically to Firefox from a file if you have the .xpi downloaded
extension_path = r'path_to_extension.xpi'  # Update with the path to the .xpi file if you have it

# Initialize the driver
driver = webdriver.Firefox(options=options)

# Initialize variables
html_files = []
counter = 1

def collect_page_content():
    """ Collect the content of all open tabs as HTML """
    all_html = ""
    for handle in driver.window_handles:
        driver.switch_to.window(handle)
        html_content = driver.page_source  # Get the entire HTML of the current tab
        all_html += f"<div class='tab-content' id='tab-{counter}'>\n"
        all_html += html_content
        all_html += "\n</div>\n"
        counter += 1
    return all_html

def find_center_frame():
    """ Find the iframe streaming from the specific URL """
    iframe = None
    # Find all iframe elements on the page
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    
    for iframe_element in iframes:
        # Check if the iframe's src contains the streaming URL
        if "https://ebooks.cenreader.com/v1/reader/stream/" in iframe_element.get_attribute("src"):
            iframe = iframe_element
            break
    
    if iframe is None:
        raise Exception("Frame not found with the expected URL pattern.")
    
    return iframe

def process_page():
    # Wait for the frame to load before finding it
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "iframe")))

    # Find the frame in the center of the page
    frame = find_center_frame()

    # Scroll the iframe into view
    driver.execute_script("arguments[0].scrollIntoView(true);", frame)

    # Find the textLayer div and a clickable child element inside it (e.g., span or p)
    text_layer = frame.find_element(By.CSS_SELECTOR, ".textLayer")
    
    # Find the first clickable child inside the textLayer (replace this with an actual child element inside the div)
    clickable_element = text_layer.find_element(By.CSS_SELECTOR, "span.textElement")  # Adjust selector as needed

    # Perform the right-click action on the child element
    actions = ActionChains(driver)
    actions.context_click(clickable_element).perform()
    time.sleep(1)

    # Find and click the "Open in New Tab" option in the right-click menu
    driver.find_element(By.CSS_SELECTOR, ".open-in-new-tab").click()  # Replace with actual selector
    time.sleep(2)

    # Switch to the new tab
    driver.switch_to.window(driver.window_handles[-1])

    # Wait for the page to load before saving the content
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "html")))

    # Now we don't save each frame separately, but will collect all open tabs later
    counter += 1

    # Close the tab with the frame
    driver.close()

    # Switch back to the main window
    driver.switch_to.window(driver.window_handles[0])


def check_next_page():
    """ Check if the "next page" button exists and is clickable """
    try:
        next_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Next Page')]"))
        )
        return next_button.is_enabled()
    except:
        return False

def save_all_tabs_as_single_html():
    """ Save all open tabs as a single HTML file using py2web """
    all_html = collect_page_content()

    # Save the combined HTML to a single file using py2web
    py2web.save_html(all_html, "merged_ebook.html")

def main():
    global driver
    driver.set_window_size(1920, 1080)  
    # Step 1: Open the login page
    driver.get('https://account.cengage.com/login')
    
    print("Login page is open. Please log in manually.")
    URL = input("Paste URL of ebook here")
    
    # Step 2: Open the ebook in a new tab
    print("Opening ebook in a new tab...")
    driver.execute_script(f"window.open('{URL}');")
    
    # Step 3: Get the current window handles
    current_window_handles = driver.window_handles
    
    # Step 4: Close the login tab (the first tab opened)
    print("Closing login page tab...")
    driver.switch_to.window(current_window_handles[0])  # Switch to the login page tab
    driver.close()  # Close the login page tab
    
    # Step 5: Switch to the ebook tab (the new tab opened)
    driver.switch_to.window(current_window_handles[1])  # Switch to the second tab (ebook)
    
    while True:
        process_page()

        if not check_next_page():
            print("No 'Next Page' button found. Stopping.")
            break

        # Click the "next page" button
        next_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Next Page')]")
        next_button.click()
        time.sleep(3)
    
    save_all_tabs_as_single_html()

    driver.quit()

if __name__ == '__main__':
    main()
