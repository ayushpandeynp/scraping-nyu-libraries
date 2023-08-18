from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from google.api_core.client_options import ClientOptions
from google.cloud import documentai  # type: ignore
from typing import Optional
from bs4 import BeautifulSoup
import time
import re
import os
import json
import requests

PROJECT_ID = "REPLACE_WITH_PROJECT_ID"
LOCATION = "REPLACE_WITH_LOCATION"
PROCESSOR_ID = "REPLACE_WITH_PROCESSOR_ID"

# function to process PDFs using Document AI
# reference: https://cloud.google.com/document-ai/docs/send-request
def process_document_sample(
    project_id: str,
    location: str,
    processor_id: str,
    file_path: str,
    mime_type: str,
    field_mask: Optional[str] = None,
    processor_version_id: Optional[str] = None,
) -> None:
    opts = ClientOptions(api_endpoint=f"{location}-documentai.googleapis.com")

    client = documentai.DocumentProcessorServiceClient(client_options=opts)

    if processor_version_id:
        name = client.processor_version_path(
            project_id, location, processor_id, processor_version_id
        )
    else:
        name = client.processor_path(project_id, location, processor_id)

    with open(file_path, "rb") as image:
        image_content = image.read()

    raw_document = documentai.RawDocument(
        content=image_content, mime_type=mime_type)

    request = documentai.ProcessRequest(
        name=name, raw_document=raw_document, field_mask=field_mask
    )

    result = client.process_document(request=request)

    document = result.document

    return document.text

# function that switches location of VPN for a different IP address
def switchVPN():
    global switched

    os.system(f"nordvpn -c")

    # wait until this VPN is connected
    time.sleep(15)
    print("IP CHANGED")
    switched = True


# vpn switched flag
switched = False

# chromedriver configs
driver_path = './chromedriver.exe'
username = "ayushpandeynp"
user_data_dir = f"C:\\Users\\{username}\\AppData\\Local\\Google\\Chrome\\User Data"
profile_dir = 'Default'

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
chrome_options.add_argument(f"--profile-directory={profile_dir}")

service = Service(driver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

# initial scraping URL
url = 'https://persistent.library.nyu.edu/arch/NYU00020'
driver.get(url)

# let Chrome take some time to load NYU credentials from its saved passwords
time.sleep(5)

# make data directory
if not os.path.exists("data"):
    os.makedirs("data")

try:
    wait = WebDriverWait(driver, 30)

    # click on Login after creds are loadeds
    button = wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, 'button[name="_eventId_proceed"]')))
    button.click()

    # perform the search query - JN "Harvard Business Review"
    search_input = wait.until(
        EC.element_to_be_clickable((By.ID, 'Searchbox1')))
    search_input.send_keys('JN "Harvard Business Review"')

    # click on search button
    submit_button = wait.until(
        EC.element_to_be_clickable((By.ID, 'SearchButton')))
    submit_button.click()

    # to keep track of the page number
    pageNumber = 1

    # pdf count
    pdf_count = 0

    # if running on multiple machines make necessary search changes
    input("Make changes and press Enter to continue...")

    # to keep track of the number of articles gone through
    count = 0
    limit = driver.find_element(
        By.CSS_SELECTOR, '.content-header .page-title').text.split(" ")[-1]
    limit = re.sub(r"[^0-9]", "", limit)
    limit = int(limit)

    while count < limit:
        # check if we need to click on the Login button
        if driver.current_url.startswith("https://shibboleth.nyu.edu/idp/profile/SAML2"):
            print("Login detected!")
            button = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, 'button[name="_eventId_proceed"]')))
            button.click()

        current_tab = driver.current_window_handle

        title_links = driver.find_elements(By.CLASS_NAME, 'title-link')
        if len(title_links) == 0:
            # this means the search results page has crashed, so we need to switch VPN
            print("No links found! Switching VPN...")
            switchVPN()
            driver.refresh()
            continue

        links = []
        for link in title_links:
            links.append(link.get_attribute('href'))

        # these are the metadata fields we want to scrape
        fields = ["Title:", "Authors:", "Source:", "Document Type:", "Subject Terms:", "Author Affiliations:",
                  "Abstract:", "Company/Entity:", "NAICS/Industry Codes:", "Geographic Terms:"]

        # helper function to clean up the metadata fields
        def y(x): return x.lower().replace(":", "").replace(r" ", "_")

        # this is where actual scraping happens
        data = []
        href_count = 0
        while href_count < len(links):
            href = links[href_count]
            try:
                driver.execute_script("window.open(arguments[0]);", href)
                driver.switch_to.window(driver.window_handles[-1])

                try:
                    # if VPN is switched, NYU will ask for login again, so waiting until credentials are loaded on Chrome
                    if switched:
                        time.sleep(5)

                    # we need to click on the Login button again if this happens
                    if driver.current_url.startswith("https://shibboleth.nyu.edu/idp/profile/SAML2"):
                        print("Login detected!")
                        button = wait.until(EC.element_to_be_clickable(
                            (By.CSS_SELECTOR, 'button[name="_eventId_proceed"]')))
                        button.click()
                except:
                    pass

                # resetting the switched variable
                switched = False

                # the components that store the metadata
                citation_fields = wait.until(
                    EC.presence_of_element_located((By.ID, 'citationFields')))
                html = citation_fields.get_attribute('innerHTML')

                # parse metadata html
                soup = BeautifulSoup(html, 'html.parser')
                alltext = soup.find_all(string=True)

                # a dictionary to store the metadata
                dct = dict.fromkeys([y(f) for f in fields])
                try:
                    for i, text in enumerate(alltext):
                        if text.strip() in fields:
                            key = y(text)

                            # one field may have multiple values
                            c = i
                            val = []
                            while alltext[c + 1].strip() and ":" != alltext[c + 1].strip()[-1]:
                                v = alltext[c + 1].strip()

                                # minor cleaning
                                if key == "authors":
                                    v = re.sub(r"[0-9*]+", "", v)
                                elif key == "subject_terms":
                                    v = v.replace(r"*", "")

                                if len(v) > 1:
                                    val.append(v)

                                c += 1

                            # source needs to be broken down
                            if key == "source":
                                source = val[0].split(" ")

                                # published = item after "Harvard Business Review"
                                published = source[3][:-1]
                                dct["published"] = published

                                # volume + issue = [4 to 7] joined by spaces
                                volume_issue = " ".join(source[4:8])[:-1]
                                dct["volume/issue"] = volume_issue

                                # page = [8 and 9] joined by spaces
                                pg = " ".join(source[8:10])
                                dct["page"] = pg

                                # extra_info = rest of source joined by spaces
                                extra_info = " ".join(source[10:])
                                dct["extra_info"] = extra_info

                            dct[key] = val[0] if len(val) == 1 else val
                except:
                    with open("metadataErrors.txt", "a") as errFile:
                        errFile.write(href + "\n")

                # now after getting the metadata, we need full text
                try:
                    # HTML Full Text
                    html_full_text = driver.find_element(
                        By.LINK_TEXT, 'HTML Full Text')
                    html_full_text.click()

                    fulltext = wait.until(EC.presence_of_element_located(
                        (By.CLASS_NAME, 'full-text-content')))
                    html = fulltext.get_attribute('innerHTML')
                    soup = BeautifulSoup(html, 'html.parser')
                    alltext = soup.find_all(string=True)

                    dct["html/pdf"] = "html"
                    dct["full_text"] = "\n".join(
                        [txt.strip() for txt in alltext])

                except:
                    # PDF Full Text
                    try:
                        dct["html/pdf"] = "pdf"

                        pdf_full_text = driver.find_element(
                            By.LINK_TEXT, 'PDF Full Text')
                        pdf_full_text.click()

                        iframe = wait.until(
                            EC.presence_of_element_located((By.ID, 'pdfIframe')))
                        src = iframe.get_attribute('src')
                        response = requests.get(src)

                        with open(f"data/pdf{pdf_count}.pdf", "wb") as f:
                            f.write(response.content)
                            dct["filename"] = f"pdf{pdf_count}.pdf"
                            pdf_count += 1

                        text = process_document_sample(
                            PROJECT_ID,
                            LOCATION,
                            PROCESSOR_ID,
                            f"data/{dct['filename']}",
                            "application/pdf",
                            "text",
                        )

                        dct["full_text"] = text

                    except:
                        # if neither HTML nor PDF parsing worked, skip this article, and write the URL to a file
                        with open("pdfErrorURLs.txt", "a") as errFile:
                            errFile.write(href + "\n")

                        href_count += 1
                        count += 1
                        continue

                # if we get here, we have successfully scraped the article
                data.append(dct)

                # now onto the next article
                href_count += 1
                count += 1
            except:
                # if an exception occurs, we need to switch VPN
                # exception is global because there can be multiple network exceptions, any of which will trigger a VPN switch
                print("Exception occurred! Switching VPN...")

                with open("exceptionURLs.txt", "a") as errFile:
                    errFile.write(href + "\n")

                # VPN Switch
                switchVPN()

        # write the data to a file [Typically 20 articles per page, less if errors]
        data = json.dumps(data)

        with open(f"data/PAGE_{pageNumber}.json", "w") as f:
            f.write(data)
            pageNumber += 1

        # close all tabs except the first one, where we move to the next page
        try:
            for tab in driver.window_handles:
                if tab != current_tab:
                    driver.switch_to.window(tab)
                    driver.close()

            driver.switch_to.window(current_tab)

            next = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, 'a[title="Next"]')))
            next.click()
        except:
            print("Next button not found!")
            if count >= limit:
                print("No more pages")
                break

except Exception as e:
    # error handling
    print(f"An error occurred: {str(e)}")

finally:
    # close the driver
    print("FINISHED TASK")
