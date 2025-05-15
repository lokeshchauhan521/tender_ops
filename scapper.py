import random
import logging
import os
import traceback
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import undetected_chromedriver as uc
import pandas as pd


class AppLogger:
    def __init__(self):
        logger = logging.getLogger("AppLogger")
        logger.setLevel(logging.DEBUG)

        if not logger.handlers:
            log_dir = os.path.join(os.getcwd(), "logs")
            os.makedirs(log_dir, exist_ok=True)  
            file_name = os.path.join(log_dir, "scapper.log")

            handler = logging.FileHandler(file_name)
            formatter = logging.Formatter(
                '%(asctime)s %(levelname)s:%(name)s [%(filename)s:%(lineno)d] %(message)s'
            )
            handler.setFormatter(formatter)
            handler.setLevel(logging.DEBUG)
            logger.addHandler(handler)

        self._logger = logger

    def get(self):
        return self._logger

logger = AppLogger().get()

user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac aOS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

def create_driver():
    try:
        options = uc.ChromeOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument(f'--user-agent={random.choice(user_agents)}')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-notifications')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--headless=new')
        options.add_argument("--disable-blink-features=AutomationControlled")
        try:
            driver = uc.Chrome(options=options, use_subprocess=True, version_main=133)
            logger.info("creating driver success")
        except Exception as e:
            logger.warning(f"creating driver failed: {str(e)}")
        logger.info(f"Driver created successfully at: {driver.service.path}")
        return driver
    
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)[-1] 
        error_message = f"error: {e} [Line: {tb.lineno}]"
        logger.error(error_message)

def create_driver_alternative(download_dir="downloads"):
    try:
        os.makedirs(download_dir, exist_ok=True)
        options = webdriver.ChromeOptions()
        options.add_argument('--disable-gpu')  
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument(f'--user-agent={random.choice(user_agents)}')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-notifications')
        # options.add_argument('--headless=new')
        #Download to a default folder 
        prefs = {
            "download.default_directory": os.path.abspath(download_dir),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "profile.default_content_settings.popups": 0,
            "profile.default_content_setting_values.automatic_downloads": 1
        }
        options.add_experimental_option("prefs", prefs)

        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)

        chrome_driver_path = ChromeDriverManager(driver_version="133.0.6943.141").install()
        logger.info(f"ChromeDriver downloaded to: {chrome_driver_path}")

        driver_dir = os.path.dirname(chrome_driver_path)
        correct_binary_path = os.path.join(driver_dir, "chromedriver")
        if not os.path.exists(correct_binary_path):
            subdir_path = os.path.join(driver_dir, "chromedriver-linux64", "chromedriver")
            if os.path.exists(subdir_path):
                correct_binary_path = subdir_path
            else:
                raise FileNotFoundError(f"ChromeDriver binary not found at {correct_binary_path} or {subdir_path}")

        os.chmod(correct_binary_path, 0o755)
        service = Service(executable_path=correct_binary_path)
        driver = webdriver.Chrome(service=service, options=options)
        
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            'userAgent': random.choice(user_agents)
        })
        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        return driver

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)[-1]
        error_message = f"Alternative driver creation failed: {e} [Line: {tb.lineno}]"
        logger.error(error_message)
        raise

def solve_captcha(driver, api_key):
    try:
        captcha_img = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//img[@data-drupal-selector='edit-captcha-image']"))
        )
        captcha_url = captcha_img.get_attribute("src")
        logger.info(f"CAPTCHA image URL: {captcha_url}")

        payload = {
            'key': api_key,
            'method': 'base64',
            'img': captcha_url,
            'json': 1
        }
        response = requests.post('http://2captcha.com/in.php', data=payload).json()
        if response['status'] != 1:
            raise Exception(f"2Captcha submission failed: {response['request']}")
        
        captcha_id = response['request']
        logger.info(f"CAPTCHA submitted to 2Captcha, ID: {captcha_id}")

        for _ in range(12):  
            result = requests.get(
                f'http://2captcha.com/res.php?key={api_key}&action=get&id={captcha_id}&json=1'
            ).json()
            if result['status'] == 1:
                captcha_code = result['request']
                logger.info(f"CAPTCHA solved: {captcha_code}")
                return captcha_code
            time.sleep(5)
        
        raise Exception("CAPTCHA solving timed out after 60 seconds")

    except Exception as e:
        logger.error(f"CAPTCHA solving failed: {str(e)}")
        raise

def download_per_page_tender_data(driver):
    try:
        def get_text_by_label(label):
            try:
                td_xpath = f"//td[normalize-space(text())='{label}']/following-sibling::td[2]"
                element = driver.find_element(By.XPATH, td_xpath)
                return element.text.strip()
            except:
                return ""

        def get_link_by_label(label):
            try:
                td_xpath = f"//td[normalize-space(text())='{label}']/following-sibling::td[2]//a"
                element = driver.find_element(By.XPATH, td_xpath)
                return element.get_attribute("href").strip()
            except:
                return ""

        tender_data = {
                "Organisation Name": get_text_by_label("Organisation Name"),
                "Organisation Type": get_text_by_label("Organisation Type"),
                "Tender Title": get_text_by_label("Tender Title"),
                "Tender Reference Number": get_text_by_label("Tender Reference Number"),
                "Tender Type": get_text_by_label("Tender Type"),
                "Tender Category": get_text_by_label("Tender Category"),
                "Product Category": get_text_by_label("Product Category"),
                "Product Sub-Category": get_text_by_label("Product Sub-Category"),
                "Tender Fee": get_text_by_label("Tender Fee"),
                "EMD": get_text_by_label("EMD"),
                "Location": get_text_by_label("Location"),
                "ePublished Date": get_text_by_label("ePublished Date"),
                "Document Download Start Date": get_text_by_label("Document Download Start Date"),
                "Document Download End Date": get_text_by_label("Document Download End Date"),
                "Bid Submission Start Date": get_text_by_label("Bid Submission Start Date"),
                "Bid Submission End Date": get_text_by_label("Bid Submission End Date"),
                "Bid Opening Date": get_text_by_label("Bid Opening Date"),
                "Work Description": get_text_by_label("Work Description"),
                "Tender Document": get_link_by_label("Tender Document"),
                "Authority Name": get_text_by_label("Name"),
                "Authority Address": get_text_by_label("Address")
        }

        return True , tender_data
    except Exception as e:
        logger.error(f"getting error in downloading tender data: {str(e)}")
        return False , False

def save_data_to_csv(scrape_data):
    try:
        output_dir = os.path.join(os.getcwd(), "output")
        os.makedirs(output_dir, exist_ok=True)
        csv_file = os.path.join(output_dir, "all_tenders_data.csv")
        df = pd.DataFrame([scrape_data])
        if not os.path.exists(csv_file):
            df.to_csv(csv_file, index=False) 
        else:
            df.to_csv(csv_file, mode='a', header=False, index=False)
        return True
    except Exception as e:
        logger.error(f"failed to save data in csv, error: {str(e)}")
        return False


def download_tender_doc(driver):
    parent_tab = driver.current_window_handle
    try:
        get_document  = f"//*[@id='tenderDetailDivTd']/div/a"
        doc_url  = driver.find_element(By.XPATH , get_document)
        link = doc_url.get_attribute("href")
        if link:
            driver.execute_script(f"window.open('{link}', '_blank');")
            logger.info(f"moving to captcha page")
            try:
                tabs = driver.window_handles
                driver.switch_to.window(tabs[-1])
                time.sleep(5)
                get_download_link  = f"//*[@id='DirectLink_5']"
                driver.find_element(By.XPATH , get_download_link).click()
                logger.info(f"searching for captcha")
                time.sleep(3)
                try:
                    # driver.switch_to.window(parent_tab)
                    cap_image_path = f"//*[@id='captchaImage']"
                    find_cap_img_path = driver.find_element(By.XPATH , cap_image_path)
                    if find_cap_img_path:
                        logger.info(f"Got image path.....{len(tabs)}")
                        time.sleep(15)
                        ## This block download the pdf via browser.
                        try:
                            final_download_link = f"//*[@id='DirectLink_4']"
                            final_download_pdf = driver.find_element(By.XPATH , final_download_link)
                            if final_download_pdf:
                                logger.info(f"find the path, Now downloading pdf...")
                                final_download_pdf.click()
                                time.sleep(4)
                                driver.close()
                            # time.sleep(10)
                            else:
                                driver.close()
                        except Exception as e:
                            logger.error(f"Getting error submit button ..{str(e)}")

                        finally:
                            if driver:
                                driver.close()
                except Exception as e:
                    logger.error(f"Getting captch path error: {str(e)}")
            except Exception as e:
                logger.error(f"Getting error while downloading tender doc..{str(e)}")
        return True
    
    except Exception as e:
        logger.error(f"Error downloading tender document, error: {str(e)}")
        return False
    
    finally:
            if parent_tab:
                driver.switch_to.window(parent_tab)        
                logger.info(f"closing final window window.....")
                driver.close()


def download_content(col_num=1, driver=None):
    parent_tab = driver.current_window_handle
    tabs = driver.window_handles
    try:
        row_wise_data = driver.find_element(By.XPATH , f"//*[@id='table']/tbody[{col_num}]/tr/td[5]/a")
        link = row_wise_data.get_attribute("href")
        if link:
            driver.execute_script(f"window.open('{link}', '_blank');")
            time.sleep(1)
            tabs = driver.window_handles
            driver.switch_to.window(tabs[-1])
            time.sleep(3)
            status, scrape_data = download_per_page_tender_data(driver)
            if status is True and scrape_data:
                save_data_to_csv(scrape_data)
                result  = download_tender_doc(driver)
                logger.info(f"{result}, move to tender doc page..")
                if result == False:
                    return False

            else:
                logger.error(f"failed to save data...")
                return False
            driver.close()
            return True
        else:
            logger.warning("No link......")
            return False
    except Exception as e:
        logger.error(f"getting error to download content")
        return False
    finally:
        try:
           driver.switch_to.window(parent_tab)
        except Exception as e:
            logger.error(f"error moving to previous page {str(e)}")

def fill_captcha(driver=None):
    try:
        if driver is not None:
            captcha_field = driver.find_element(By.ID, "edit-captcha-response")
            captcha_code = input("Please enter the CAPTCHA code from the page (e.g., 'A7KZ5X'): ")
            captcha_field.send_keys(captcha_code)
            logger.info("CAPTCHA code entered manually")
            if captcha_code:
                search_button = driver.find_element(By.XPATH, "//input[@value='Search']")
                search_button.click()
                data  = WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.ID, "edit-data4"))
                )
                if data:
                    logger.info("Form submitted successfully")
                    return True
                else:
                    logger.error(f"We are not getting data............")
                    return False
            else:
                return False
    except Exception as e:
        logger.error(f"getting error in fill captcha: {str(e)}")
        return False

def get_total_pages(driver):
    try:
        url = "https://eprocure.gov.in/cppp/latestactivetendersnew/mmpdata"
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "pagination"))
        )
        pagination = driver.find_element(By.CLASS_NAME, "pagination")
        page_links = pagination.find_elements(By.TAG_NAME, "a")
        page_numbers = []
        for link in page_links:
            href = link.get_attribute("href")
            if href and "page=" in href:
                try:
                    page_num = int(href.split("page=")[-1])
                    page_numbers.append(page_num)
                except ValueError:
                    continue

        total_pages = max(page_numbers) if page_numbers else 1
        logger.info(f"Total number of pages: {total_pages}")
        return total_pages

    except Exception as e:
        logger.error(f"Error while getting total number of pages: {str(e)}")
        return None


def interact_with_form(driver, page , state="Haryana", captcha_api_key=None ): 
    try:
        url = f"https://eprocure.gov.in/cppp/latestactivetendersnew/mmpdata?page={page}"
        driver.get(url)        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "tendercategory"))
        )
        try:

            state_dropdown = Select(driver.find_element(By.ID, "tendercategory"))
            state_dropdown.select_by_visible_text(state)
            WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "edit-captcha-response"))
                )
        except Exception as e :
            logger.error(f"Getting error to select state : {str(e)}")
            pass


        captcha_field = driver.find_element(By.ID, "edit-captcha-response")
        
        if captcha_api_key:
            captcha_code = solve_captcha(driver, captcha_api_key)
            captcha_field.send_keys(captcha_code)
            logger.info("CAPTCHA code entered via 2Captcha")
        else:
            # fetch_data = fill_captcha(driver)
            fetch_data = True
            if fetch_data==True:
                try:
                    # para_data = driver.find_element(By.XPATH, '//*[@id="edit-captcha-response"]')
                    para_data = True
                    if para_data:
                        time.sleep(1)
                        try:
                            # Use multi processing here to download each page content.
                            for i in range(1, 11):
                                per_col_data = download_content(i,driver)
                                if per_col_data:
                                    logger.info(f"moving to column {i}")
                        except:
                            logger.error(f"getting errror to download content.")
                except Exception as e:
                    logger.error(f"error getting captcha: {str(e)}")
                    return 
    except TimeoutException as e:
        logger.error(f"Timeout while loading page or elements: {e}")
        raise
    except NoSuchElementException as e:
        logger.error(f"Element not found: {e}")
        raise
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)[-1]
        error_message = f"Error during form interaction: {e} [Line: {tb.lineno}]"
        logger.error(error_message)
        raise

if __name__ == "__main__":
    driver = None
    try:
        driver = create_driver_alternative()
        # Undetected driver for headless mode.
        # driver = create_driver()
        
        # interact_with_form(driver, state="Haryana")
        total_pages = get_total_pages(driver)
        if total_pages > 0 and not None:
                for page in range(1034,int(total_pages)):
                    logger.info(f"working on page number : {page}")
                    interact_with_form(driver, page , state="Haryana")


        
    except Exception as e:
        logger.error(f"Script failed: {e}")
    finally:
        if driver:
            driver.quit()
            logger.info("Driver closed successfully")
