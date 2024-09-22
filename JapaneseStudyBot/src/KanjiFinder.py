from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
class NoExamplesException(Exception):
    def __init__(self, message="No examples found."):
        self.message = message
        super().__init__(self.message)

import time
from PIL import Image
import io
import os

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

def initialize_driver():
    global driver
    global default_wait
    firefox_options = Options()
    #firefox_options.binary_location = r'C:\Program Files\Mozilla Firefox\firefox.exe'

    firefox_options.binary_location = os.path.join(os.path.dirname(__file__), '..', 'firefox', 'firefox.exe')
    geckodriver_path = os.path.join(os.path.dirname(__file__), '..', 'gecko', 'geckodriver.exe')
    firefox_options.add_argument('--headless')
    firefox_service = FirefoxService(executable_path=geckodriver_path)
    driver = webdriver.Firefox(service=firefox_service, options=firefox_options)
    default_wait = WebDriverWait(driver, 6)  # Wait up to 10 seconds


#grade can be "All", "N5", "N4", "N3", "N2", "N1", "1", "2", "3", "4", "5", "6"
def scrape_kanji_info(grade):
    initialize_driver()
    driver.get(f'https://www.yookoso.com/study/kanji-study/?grade={grade}')
    time.sleep(1)
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

def scrape_kanji_images(grade):
    initialize_driver()
    driver.get(f'https://www.yookoso.com/study/kanji-study/?grade={grade}')
    time.sleep(1)
    try:
        return get_images()
    except NoExamplesException as e:
        raise NoExamplesException
    except NoSuchElementException as e:
        print(f"Error: {e}")
        raise NoSuchElementException
    except Exception as e:
        print(f"Error: {e}")
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
        print(f"Error: {e}")
        raise NoSuchElementException
    except Exception as e:
        print(f"Error: {e}")
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
        print(f"Error: {e}")
        raise NoSuchElementException
    except Exception as e:
        print(f"Error: {e}")
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
        print(f"Error: {e}")
        raise NoSuchElementException
    except Exception as e:
        print(f"Error: {e}")
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

# Test
result = search_images('乃')
print(result)
#search_images('絢')