from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
import time
from PIL import Image
import io
import os
from dotenv import load_dotenv
import tarfile
import logging
import subprocess
import selenium

logging.basicConfig(level=logging.INFO)
load_dotenv()  # Load environment variables from .env file

class NoExamplesException(Exception):
    def __init__(self, message="No examples found."):
        self.message = message
        super().__init__(self.message)

def extract_archive(archive_path, extract_to):
    """Extracts a tar.gz or tar.bz2 file."""
    if archive_path.endswith(('.tar.gz', '.tar.bz2')):
        with tarfile.open(archive_path, 'r:*') as archive:
            archive.extractall(path=extract_to)
        print(f"Extracted {archive_path} to {extract_to}")
    else:
        raise ValueError("Unsupported file type. Only .tar.gz or .tar.bz2 are supported.")
    
###Variables
#Drivers
driver = None 
default_wait= None

#Info Xpaths
kanji_png_xpath = '/html/body/div[2]/div[2]/div/div[1]/div/div/div[4]/div/div[1]'
kanji_character_xpath = '/html/body/div[2]/div[2]/div/div[1]/div/div/div[4]/div/div[position()=last()-1]/span'
meaning_xpath = '/html/body/div[2]/div[2]/div/div[1]/div/div/div[4]/div/div[1]/table/tbody/tr[2]/td[1]'
onyomi_xpath = '/html/body/div[2]/div[2]/div/div[1]/div/div/div[4]/div/div[1]/table/tbody/tr[2]/td[2]'
kunyomi_xpath = '/html/body/div[2]/div[2]/div/div[1]/div/div/div[4]/div/div[1]/table/tbody/tr[2]/td[3]'

#Image Xpaths
examples_xpath = '/html/body/div[2]/div[2]/div/div[1]/div/div/div[4]/div/div[position()=last()-2]/ul' 
xpath_image = "/html/body/div[2]/div[2]/div/div[1]/div/div/div[4]/div/div[1]/table/tbody/tr[1]/td/a/img"

#Search
input_text_xpath = '/html/body/div[2]/div[2]/div/div[1]/div/div/div[3]/form/p[2]/input[1]'
submit_xpath = '/html/body/div[2]/div[2]/div/div[1]/div/div/div[3]/form/p[2]/input[2]'
#Image paths
kanji_png_path = os.path.join(os.path.dirname(__file__), '..', 'img', 'kanji_character.png')
examples_png_path = os.path.join(os.path.dirname(__file__), '..', 'img', 'kanji_examples.png')

#Setup 
firefox_archive_path = os.path.join(os.path.dirname(__file__), '..','firefox', 'firefox-130.0.1.tar.bz2')
geckodriver_archive_path = os.path.join(os.path.dirname(__file__), '..', 'gecko', 'geckodriver.tar.gz')
firefox_extract_to = os.path.join(os.path.dirname(__file__), '..', 'firefox') 
geckodriver_extract_to = os.path.join(os.path.dirname(__file__), '..', 'gecko') 
firefox_binary_path = os.path.join(firefox_extract_to, 'firefox', 'firefox')  
geckodriver_path = os.path.join(geckodriver_extract_to, 'geckodriver')  
print("firefox path:", firefox_binary_path)
print("gecko path:",geckodriver_path)
extract_archive(firefox_archive_path, firefox_extract_to)
extract_archive(geckodriver_archive_path, geckodriver_extract_to)

def initialize_driver():
    
    firefox_options = Options()

    #firefox_options.binary_location = r'C:\Program Files\Mozilla Firefox\firefox.exe'
    firefox_options.binary_location = firefox_binary_path
    #firefox_options.add_argument('--headless')
    firefox_options.log.level = "trace"
    firefox_service = FirefoxService(executable_path=geckodriver_path)
    try:
        global driver
        global default_wait
        driver = webdriver.Firefox(service=firefox_service, options=firefox_options)
        default_wait = WebDriverWait(driver, 6)  
    except OSError as e:
        logging.error(f"OS error:{e}")
        raise OSError(f"Driver setup failure:{e}")
    except Exception as e:
        logging.error(f"Driver setup error:{e}")
        raise Exception(f"Driver setup failure:{e}")


#grade can be "All", "N5", "N4", "N3", "N2", "N1", "1", "2", "3", "4", "5", "6"
def scrape_kanji_info(grade):
    initialize_driver()
    driver.get(f'https://www.yookoso.com/study/kanji-study/?grade={grade}')
    time.sleep(1)
    try:
        return get_kanji_info()
    except NoSuchElementException as e:
        print(f"Error : {e}")
        raise NoSuchElementException
    except Exception as e:
        print(f"Error: {e}")
        raise Exception
    finally:
        driver.quit()

def scrape_kanji_images(grade):
    initialize_driver()
    driver.get(f'https://www.yookoso.com/study/kanji-study/?grade={grade}')
    time.sleep(1)
    try:
        return get_images()
    except NoExamplesException as e:
        raise NoExamplesException
    except NoSuchElementException as e:
        logging.error(f"Error at scrape images: {e}")
        raise NoSuchElementException
    except Exception as e:
        logging.error(f"Error at scrape images: {e}")
        raise Exception
    finally:
        driver.quit()

def search_images(kanji):
    initialize_driver()
    driver.get(f'https://www.yookoso.com/study/kanji-study/')

    input_field = default_wait.until(EC.visibility_of_element_located((By.XPATH, input_text_xpath)))
    input_field.clear()
    input_field.send_keys(kanji)  
    submit_button = default_wait.until(EC.element_to_be_clickable((By.XPATH, submit_xpath)))
    submit_button.click()
    try:
        return get_images()
    except NoExamplesException as e:
        raise NoExamplesException
    except NoSuchElementException as e:
        logging.error(f"Error at search images: {e}")
        raise NoSuchElementException
    except Exception as e:
        logging.error(f"Error at search images: {e}")
        raise Exception
    finally:
        driver.quit()

def search_info(kanji):
    initialize_driver()
    driver.get(f'https://www.yookoso.com/study/kanji-study/')
    input_field = default_wait.until(EC.visibility_of_element_located((By.XPATH, input_text_xpath)))
    input_field.clear()
    input_field.send_keys(kanji)  
    submit_button = default_wait.until(EC.element_to_be_clickable((By.XPATH, submit_xpath)))
    submit_button.click()
    try:
        return get_kanji_info()
    except NoSuchElementException as e:
        print(f"Error: {e}")
        raise NoSuchElementException
    except Exception as e:
        print(f"Error: {e}")
        raise Exception
    finally:
        driver.quit()

#assumes driver is loaded and page is correct
def get_images():
    result = {}
    try:
        kanji_character_png_element = default_wait.until(EC.visibility_of_element_located(("xpath", kanji_png_xpath)))
        default_wait.until(EC.visibility_of_element_located((By.XPATH, kanji_png_xpath)))
        driver.execute_script("arguments[0].scrollIntoView();", kanji_character_png_element)
        time.sleep(1)
        kanji_character_png_element.screenshot(kanji_png_path)
        result['kanji_image_path'] = kanji_png_path
    except NoSuchElementException as e:
        logging.error(f"Error at getImages kanji image: {e}")
        raise NoSuchElementException
    except Exception as e:
        logging.error(f"Error at getImages kanji image: {e}")
        raise Exception
    try:
        examples = default_wait.until(EC.presence_of_all_elements_located(("xpath", f'{examples_xpath}/*')))  # Get all children of the <ul>
        images = []
        for ul_element in examples:
            img_data = ul_element.screenshot_as_png 
            img = Image.open(io.BytesIO(img_data)) 
            images.append(img)
        if len(images) == 0:
            raise NoExamplesException
        if images:
            total_height = sum(img.height for img in images)
            combined_img = Image.new('RGB', (images[0].width, total_height))
            current_height = 0
            for img in images:
                combined_img.paste(img, (0, current_height))
                current_height += img.height
            combined_img.save(examples_png_path)
            result['kanji_examples_path'] = examples_png_path
        return result
    except TimeoutException as e:
        raise NoExamplesException
    except NoExamplesException as e:
        raise NoExamplesException
    except NoSuchElementException as e:
        logging.error(f"Error at getImages: {e}")
        raise NoSuchElementException
    except Exception as e:
        logging.error(f"Error at getImages: {e}")
        raise Exception

#assumes driver is loaded and page is
def get_kanji_info():
    try:
        kanji_character_text = default_wait.until(EC.presence_of_element_located((By.XPATH, kanji_character_xpath))).text.split('\n')
        meaning = default_wait.until(EC.presence_of_element_located((By.XPATH, meaning_xpath))).text.split('\n')[1:]
        onyomi = default_wait.until(EC.presence_of_element_located((By.XPATH, onyomi_xpath))).text.split('\n')[1:]
        kunyomi = default_wait.until(EC.presence_of_element_located((By.XPATH, kunyomi_xpath))).text.split('\n')[1:]

        kanji_png_element = driver.find_element(By.XPATH, kanji_png_xpath)
        kanji_png_element.screenshot('kanji_character.png') 
        return {
            "Kanji": kanji_character_text,
            "Meaning": meaning,
            "Onyomi": onyomi,
            "Kunyomi": kunyomi
        }
    except NoSuchElementException as e:
        print(f"Error: {e}")
        raise NoSuchElementException
    except Exception as e:
        print(f"Error: {e}")
        raise Exception




def get_firefox_version():
    try:
        version = subprocess.check_output(["firefox", "--version"], stderr=subprocess.STDOUT)
        return version.decode().strip()
    except Exception as e:
        return f"Error getting Firefox version: {e}"

def get_geckodriver_version(geckodriver_path):
    try:
        version = subprocess.check_output([geckodriver_path, "--version"], stderr=subprocess.STDOUT)
        return version.decode().strip()
    except Exception as e:
        return f"Error getting geckodriver version: {e}"

print(f"Firefox Version: {get_firefox_version()}")
print(f"Geckodriver Version: {get_geckodriver_version(geckodriver_path)}")
print(f"Selenium Version: {selenium.__version__}")
raise Exception(f"Firefox Version: {get_firefox_version()}, Geckodriver Version: {get_geckodriver_version(geckodriver_path)},
      Selenium Version: {selenium.__version__}")

# Test
#result = search_images('絢')
result = search_images('乃')
print(result)
#search_images('絢')