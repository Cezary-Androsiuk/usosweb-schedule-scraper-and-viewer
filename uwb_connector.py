import os
import json
import time
import traceback
from datetime import datetime
from playwright.sync_api import sync_playwright, Page

from PIL import Image

LOGIN = os.getenv("UWB_LOGIN")
PASSWORD = os.getenv("UWB_PASSWORD")

# LOGIN_URL = 'https://cas.uwb.edu.pl/cas/login'
USOSWEB_URL = 'https://usosweb.uwb.edu.pl/kontroler.php'
LOGOUT_URL = USOSWEB_URL + '?_action=logowaniecas/wyloguj'
LOGIN_URL = USOSWEB_URL + '?_action=logowaniecas'
TEST_SESSION_URL = USOSWEB_URL + '?_action=home/index'

IMAGE_OUTPUT_DIR = 'static/'
IMAGE_PREFIX = 'schedule-'
IMAGE_EXT = '.gif'

cookies = None
class InvalidImage(Exception):
    pass

def make_message(message: str):
    j = {'type': 'message', 'payload': message}
    return f'data: {json.dumps(j)}\n\n'

def make_time_name()->str:
    return datetime.now().strftime('%Y-%m-%d_%H-%M-%S.%f')[:-3]

def make_screenshot(page: Page, name:str=None):
    if not os.path.exists('error_screenshots/'):
        os.mkdir('error_screenshots/')

    if not name:
        name = make_time_name()

    page.screenshot(path=f"error_screenshots/{name}.png")

def schedule_image_name(schedule_date: str) -> str:
    return IMAGE_OUTPUT_DIR + IMAGE_PREFIX + str(schedule_date) + IMAGE_EXT

def download_image(page, image_url: str, path: str):
    response = page.request.get(image_url)
    if response.ok:
        with open(path, "wb") as f:
            f.write(response.body())

        # check if image is correct, method will be called again
        try:
            img = Image.open(path)
            img.verify()
        except Exception as e:
            raise InvalidImage
    else:
        raise Exception(f'Error while downloading image: {response.status}')
    
def download_schedule(schedule_date):
    global cookies
    with sync_playwright() as p:
        yield make_message('Oppening browser...');
        browser = p.chromium.launch(headless=False)
        yield make_message('Browser Oppened')
        try:

            yield make_message('Creating Context...')
            context = browser.new_context()
            if cookies:
                context.add_cookies(cookies=cookies)
            yield make_message('Context created')

            
            yield make_message('Oppening new tab...')
            page = context.new_page();
            yield make_message('New tab oppened')

            yield make_message('Going to schedule page...')
            schedule_url = f'{USOSWEB_URL}?_action=home/plan&plan_format=gif&plan_week_sel_week={schedule_date}'
            page.goto(schedule_url, wait_until="domcontentloaded")
            logout_button = page.locator(f'a[href="{LOGOUT_URL}"]')
            if not logout_button.is_visible():
                yield make_message('<span style="color: #dbfa4f;">Login failed!</span>')

                # check if current page is Logout page
                login_button = page.locator(f'div#actions > a[href^="{LOGIN_URL}"]')
                if not login_button.is_visible():
                    make_screenshot(page)
                    raise Exception("Can't determine current page")
                
                yield make_message('Oppening login page...')
                time.sleep(0.5)
                # go to login page
                login_button.click()
                time.sleep(1)

                yield make_message('Entering credentials...')
                page.locator("#username").fill(LOGIN)
                page.locator("#password").fill(PASSWORD)
                time.sleep(1)

                yield make_message('Waiting for login...')
                
                # press 'login' button
                page.locator(".form-button").click()
                time.sleep(0.2)

                logout_button = page.locator(f'a[href="{LOGOUT_URL}"]')
                if not logout_button.is_visible():
                    make_screenshot(page)
                    raise Exception("Login failed!")
            
            yield make_message('Logged in successfully')
            cookies = context.cookies()

            migration = page.locator('h1:has-text("USOSweb tymczasowo niedostępny")')
            if migration.is_visible():
                make_screenshot(page)
                raise Exception("USOSweb data migration... Try again in few minutes")
            
            yield make_message('Looking for an schedule image...')
            image_locator = page.locator("div.do_not_print > img.schedimg")
            image_url = image_locator.get_attribute("src")
            if not image_url:
                raise Exception("Image not found or Image does not have source")
                
            yield make_message(f'Image located, url: {image_url}')

            if not os.path.exists(IMAGE_OUTPUT_DIR):
                os.mkdir(IMAGE_OUTPUT_DIR)
            
            # assemble image path
            image_path = schedule_image_name(schedule_date)
            print(f'Image path: {image_path}')
            
            yield make_message(f'Downloading image...')

            it = 0
            image_is_valid = False
            while image_is_valid == False and it < 3:
                it += 1
                try:
                    download_image(page=page, image_url=image_url, path=image_path)
                    image_is_valid = True
                except InvalidImage:
                    yield make_message('<span style="color: #dbfa4f;">Downloading image failed!</span>')
                    yield make_message('Retrying to download image...')
                    pass

            yield make_message(f'Image downloaded correctly!')
            
            yield make_message(f'Closing browser...')
            
            browser.close()

            message = {'type': 'link', 'payload': f'{schedule_image_name(schedule_date)}'}
            yield f'data: {json.dumps(message)}\n\n'
        except Exception as e:
            # makes screenshot, saves error info and raise exception again to handle all errors in parent
            name = make_time_name()
            make_screenshot(page, name)

            full_traceback = traceback.format_exc()
            with open(f'error_screenshots/{name}.txt', 'w', encoding='utf-8') as file:
                file.write(full_traceback)

            raise e

def download_schedule_safe(schedule_date):
    '''
    Ensures to inform user about the error and to end stream if an error occur
    '''
    try:
        yield from download_schedule(schedule_date=schedule_date)
    except Exception as e:
        message = {'type': 'error', 'payload': str(e)}
        yield f'data: {json.dumps(message)}\n\n'
        raise e