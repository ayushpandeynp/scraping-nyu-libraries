# NYU Libraries Scraping Task

This repository contains the Python script and instructions for scraping data from the NYU Libraries website.

## Prerequisites
1. **NordVPN Premium Subscription**: You need a NordVPN premium subscription to change IP addresses during the scraping process. IPs are blocked by the server for the rest of the day after scraping about 600-700 items. The cheapest monthly plan costs $12.99. Purchase a license and download the app.

2. **NordVPN Executable Path**: Add the path to the NordVPN executable folder to the Environment Variables on Windows. This is necessary for the scraping scripts to interact with NordVPN.

3. **NordVPN Remote Connections**: Enable the option to allow remote access to the cloud instance while NordVPN is connected. Otherwise, you will be locked out of the cloud instance after connecting to NordVPN.

4. **NYU Login Credentials**: Save your NYU Login credentials on Google Chrome. It is recommended to use this method for authentication instead of hardcoding credentials in Python, for security reasons.

5. **Easy Duo Authentication Chrome Extension**: Install the Easy Duo Authentication Chrome Extension and configure it to bypass Duo authentication. This extension ensures that the Multi-Factor Authentication (MFA) process is completed automatically whenever the IP changes.

6. **Required Libraries**: Install the necessary Python libraries listed in the `requirements.txt` file. You can do this by running the following command:

    ```bash
    pip install -r requirements.txt
    ```
6. **ChromeDriver**: Download the ChromeDriver executable from [here](https://chromedriver.chromium.org/downloads) and replace the `chromedriver.exe` file based on the version of Chrome installed your system. This is necessary for the scraping scripts to interact with Google Chrome.

7. **Google Cloud Document AI Setup**: Follow the instructions [here](https://cloud.google.com/sdk/docs/install) to set up Google Cloud CLI. And then follow this [link](https://codelabs.developers.google.com/codelabs/docai-ocr-python) to understand how Document AI Credentials and OCR Processor setup needs to be done. This is necessary to use OCR on the PDFs. **Don't forget to replace credential values in the scraping script.**.

## Usage
Once all the prerequisites are met, you can run the scraping script by running the following command:

```bash
python scrape.py
```

## Runtime
Each page, consisting of 20 scraped items, takes approximately 4 minutes to scrape. Therefore, total runtime for 1000 items (i.e. 50 pages) is 3.33 hours. And considering there are about 15k items, ~50hrs is very very bad.

So, I ran this parallely on 5 Windows virtual machines on Microsoft Azure, each of which was scraping around 3500 items, so the scraping time was reduced to ~12 hours.