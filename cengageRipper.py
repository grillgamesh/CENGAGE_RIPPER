import time
import pytesseract
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

def save_frame_as_html(frame, index):
    """ Save the content of the frame as HTML """
    html_content = frame.get_attribute('outerHTML')
    
    # Create a new HTML file with the given index
    filename = f"{index:03d}.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    html_files.append(filename)

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
    """ Process the current page: locate the frame, save it, and navigate to the next page """
    global counter
    # Wait for the frame to load before finding it
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "iframe")))
    
    # Find the frame in the center of the page
    frame = find_center_frame()
    
    # Right-click on the frame to open it in a new tab
    actions = ActionChains(driver)
    actions.context_click(frame).perform()
    time.sleep(1)
    
    # Find and click the "Open in New Tab" option in the right-click menu
    driver.find_element(By.CSS_SELECTOR, "your_specific_selector_to_open_in_new_tab").click()
    time.sleep(2)
    
    # Switch to the new tab
    driver.switch_to.window(driver.window_handles[-1])
    
    # Wait for the page to load before saving the content
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "html")))
    
    # Save the frame's content as HTML
    save_frame_as_html(frame, counter)
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

def create_epub_from_html_files():
    """ Create an EPUB from all the saved HTML files """
    book = epub.EpubBook()
    book.set_title("Merged HTML Files")
    book.set_language('en')

    # Add HTML files to the book
    for html_file in html_files:
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        html_item = epub.EpubHtml(title=html_file, file_name=html_file, lang='en')
        html_item.set_body(html_content)
        book.add_item(html_item)

    # Define the spine and TOC (table of contents)
    book.spine = ['nav'] + [epub.EpubHtml(title=f'Page {i+1}', file_name=f'{i+1:03d}.html', lang='en') for i in range(len(html_files))]
    book.add_item(epub.EpubNav())
    
    # Write the EPUB file
    epub.write_epub('merged_book.epub', book)

def main():
    global driver
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
    
    create_epub_from_html_files()

    driver.quit()

if __name__ == '__main__':
    main()
