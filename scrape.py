from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
import time
import re
import os
import json
import random
import requests

# function to get NordVPN servers
def get_nordvpn_servers():
    try:
        serverlist =  BeautifulSoup(requests.get("https://nordvpn.com/api/server").content, "html.parser")
        site_json = json.loads(serverlist.text)

        filtered_servers = {key: [] for key in ['windows_names','linux_names']}
        for specific_dict in site_json:
            try:
                if specific_dict['categories'][0]['name'] == 'Standard VPN servers':
                    filtered_servers['windows_names'].append(specific_dict['name'])
                    filtered_servers['linux_names'].append(specific_dict['domain'].split('.')[0])
            except IndexError:
                pass
    except:
        print("Error getting NordVPN servers. Retrying...")
        return get_nordvpn_servers()
    
    return filtered_servers

# function to get current IP
def getCurrentIP(driver):
    # must load it in chrome cuz we use Split Tunneling and only apply VPN to the Chrome process
    # if an API call is made in Python, it will not be routed through the VPN
    try:
        url = "https://jsonip.com"
        driver.execute_script("window.open(arguments[0]);", url)
        driver.switch_to.window(driver.window_handles[-1])

        current_ip = json.loads(driver.find_element(By.XPATH, "/html/body").text)["ip"]
    except:
        # if error, we switch VPN, and try again
        switchVPN()
        return getCurrentIP(driver)
    
    return current_ip

# function that switches location of VPN for a different IP address
def switchVPN():
    global ip, switched
    servers = get_nordvpn_servers()["windows_names"]

    # only use US servers, as they are relatively faster than other locations
    us_servers = set([s for s in servers if s.startswith("United States")])

    os.system(f"nordvpn -c --server-name \"{random.choice(list(us_servers))}\"")
    time.sleep(15)

    new_ip = getCurrentIP(driver)
    if new_ip == ip:
        switchVPN()
    else:
        ip = new_ip
        print("IP CHANGED TO:", ip)
        switched = True
    
# vpn switched flag
switched = False

# chromedriver configs
driver_path = './chromedriver.exe'
username = "ayushpandeynp" # system username
user_data_dir = f"C:\\Users\\{username}\\AppData\\Local\\Google\\Chrome\\User Data" # this is for windows, won't run on mac or linux
profile_dir = 'Default' # this is the default profile dir for chrome

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
chrome_options.add_argument(f"--profile-directory={profile_dir}")

service = Service(driver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

# start with the first IP, to keep track of IP changes
ip = getCurrentIP(driver)

# initial scraping URL
url = 'https://persistent.library.nyu.edu/arch/NYU00020'
driver.get(url)

# let Chrome take some time to load NYU credentials from it's saved passwords
time.sleep(5)

# make data directory
try:
    os.mkdir("data")
except:
    pass

try:
    wait = WebDriverWait(driver, 60)

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

    # to keep track of the number of articles
    count = 0
    limit = driver.find_element(
        By.CSS_SELECTOR, '.content-header .page-title').text.split(" ")[-1]
    limit = re.sub(r"[^0-9]", "", limit)
    limit = int(limit)

    while count < limit:
        current_tab = driver.current_window_handle

        title_links = driver.find_elements(By.CLASS_NAME, 'title-link')
        links = []
        for link in title_links:
            links.append(link.get_attribute('href'))

        # these are the metadata fields we want to scrape
        fields = ["Title:", "Authors:", "Source:", "Document Type:", "Subject Terms:", "Author Affiliations:",
                  "Abstract:", "Full Text Word Count:", "Company/Entity:", "NAICS/Industry Codes:", "Geographic Terms:"]

        # helper function to clean up the metadata fields
        y = lambda x: x.lower().replace(":", "").replace(r" ", "_")

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

                # create a dictionary to store the metadata
                dct = dict.fromkeys([y(f) for f in fields])
                dct["url"] = href
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

                # now after getting the metadata, we need full text
                try:
                    # HTML Full Text
                    html_full_text = driver.find_element(By.LINK_TEXT, 'HTML Full Text')
                    html_full_text.click()

                    fulltext = wait.until(EC.presence_of_element_located(
                        (By.CLASS_NAME, 'full-text-content')))
                    html = fulltext.get_attribute('innerHTML')
                    soup = BeautifulSoup(html, 'html.parser')
                    alltext = soup.find_all(string=True)

                    dct["html/pdf"] = "html"
                    dct["full_text"] = "\n".join([txt.strip() for txt in alltext])

                except:
                    # PDF Full Text
                    try:
                        pdf_full_text = driver.find_element(By.LINK_TEXT, 'PDF Full Text')
                        pdf_full_text.click()

                        iframe = wait.until(
                            EC.presence_of_element_located((By.ID, 'pdfIframe')))
                        src = iframe.get_attribute('src')
                        response = requests.get(src)
                        with open("data/temp.pdf", "wb") as f:
                            f.write(response.content)

                        pdf = PdfReader("data/temp.pdf")
                        text = ""
                        for page in pdf.pages[:-1]:
                            text += page.extract_text()

                        dct["html/pdf"] = "pdf"
                        dct["full_text"] = text
                    except:
                        # if neither HTML nor PDF parsing worked, skip this article, and write the URL to a file
                        with open("pdfErrorURLs.txt", "a") as errFile:
                            errFile.write(href + "\n")        
                        
                        href_count += 1
                        continue
                
                # if we get here, we have successfully scraped the article
                data.append(dct)

                # now onto the next article
                href_count += 1
            except:
                # if an exception occurs, we need to switch VPN
                # exception is global because there can be multiple network exceptions, any of which will trigger a VPN switch
                print("Exception occurred! Switching VPN...")

                # ofc, skipping the article
                href_count += 1

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
            # if no next page button, scraping is complete
            print("No more pages")
            break

except Exception as e:
    # error handling
    print(f"An error occurred: {str(e)}")

finally:
    # close the driver
    print("FINISHED TASK")
    driver.quit()