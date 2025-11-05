import os
import json
import time
import asyncio
import traceback
from datetime import datetime
from playwright.sync_api import sync_playwright, Page

from PIL import Image

# collect login and password from environment variables
LOGIN = os.getenv("UWB_LOGIN")
PASSWORD = os.getenv("UWB_PASSWORD")

USOSWEB_URL = 'https://usosweb.uwb.edu.pl/kontroler.php'
LOGOUT_URL = USOSWEB_URL + '?_action=logowaniecas/wyloguj'
LOGIN_URL = USOSWEB_URL + '?_action=logowaniecas'

IMAGE_OUTPUT_DIR = 'static/'
IMAGE_PREFIX = 'schedule-'
IMAGE_EXT = '.gif'

ERROR_OUTPUT_DIR = 'errors/'

cookies = None
# browser_endpoint = None

# # global instance of browser
# async def startBrowser():
#     global browser_endpoint
#     with sync_playwright() as p:
#         browser = p.chromium.launch_server(port=9222)
#         browser_endpoint = browser.ws_endpoint
#         print(f"Browser server started at: {browser_endpoint}")
#         try:
#             while True: pass
#         except KeyboardInterrupt:
#             browser.close()

        
class InvalidImage(Exception):
    pass

# method for formatting yelded text
def make_message(message: str):
    j = {'type': 'message', 'payload': message}
    return f'data: {json.dumps(j)}\n\n'



# current time as string
def make_time_name()->str:
    return datetime.now().strftime('%Y-%m-%d_%H-%M-%S.%f')[:-3]

# makes screenshot on the page for later debug purposes 
# called when something went wrong
def make_screenshot(page: Page, name:str=None):
    if not os.path.exists(ERROR_OUTPUT_DIR):
        os.mkdir(ERROR_OUTPUT_DIR)

    if not name:
        name = make_time_name()

    page.screenshot(path=f"{ERROR_OUTPUT_DIR}{name}.png")

# generate shedule image name for saving
def schedule_image_name(schedule_date: str) -> str:
    return IMAGE_OUTPUT_DIR + IMAGE_PREFIX + str(schedule_date) + IMAGE_EXT

# download image from the page
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
    
def login(page):
    # check if there is any login button
    # after logout user should be redirected to page with loging button
    login_button = page.locator(f'div#actions > a[href^="{LOGIN_URL}"]')
    if not login_button.is_visible():
        raise Exception("Can't determine current page")
    
    yield make_message('Oppening login page...')
    time.sleep(0.5)
    # go to login page by their href
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

    # check if after login page contains logout phrases - check if user is logged in
    logout_button = page.locator(f'a[href="{LOGOUT_URL}"]')
    if not logout_button.is_visible():
        raise Exception("Login failed!")

def download_schedule(schedule_date):
    global cookies
    # global browser_endpoint

    yield make_message('Oppening browser...');
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # browser = p.chromium.connect(browser_endpoint)
        yield make_message('Browser Oppened')
        try:

            yield make_message('Creating Context...')
            # add cookies from ealier session
            context = browser.new_context()
            if cookies:
                context.add_cookies(cookies=cookies)
            yield make_message('Context created')

            
            yield make_message('Oppening new tab...')
            page = context.new_page();
            yield make_message('New tab oppened')

            yield make_message('Going to schedule page...')
            # change url to shedule url
            schedule_url = f'{USOSWEB_URL}?_action=home/plan&plan_format=gif&plan_week_sel_week={schedule_date}'
            page.goto(schedule_url, wait_until="domcontentloaded")

            # check if page contains Logout phrases - check if user is logged in
            logout_button = page.locator(f'a[href="{LOGOUT_URL}"]')
            if not logout_button.is_visible():
                yield make_message('<span style="color: #dbfa4f;">Login failed!</span>')
                yield from login(page=page)
                # if login was successful then script can be continued
            
            yield make_message('Logged in successfully')
            cookies = context.cookies()

            # inform about possible data migration
            # yup, that happened once
            migration = page.locator('h1:has-text("USOSweb tymczasowo niedostępny")')
            if migration.is_visible():
                raise Exception("USOSweb data migration... Try again in few minutes")
            
            yield make_message('Looking for an schedule image...')
            image_locator = page.locator("div.do_not_print > img.schedimg")
            image_url = image_locator.get_attribute("src")
            if not image_url:
                raise Exception("Image not found or Image does not have source")
                
            yield make_message(f'Image located, url: {image_url}')

            # ensure output directory exist
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

            if not image_is_valid:
                raise Exception("Can't download image");

            yield make_message(f'Image downloaded correctly!')
            
            yield make_message(f'Closing browser...')
            
            browser.close()

            # send link to downloaded image - that ends connection with javascirpt
            message = {'type': 'link', 'payload': f'{schedule_image_name(schedule_date)}'}
            yield f'data: {json.dumps(message)}\n\n'

        except Exception as e:
            # makes screenshot, saves error info and raise exception again to handle all errors in parent
            name = make_time_name()

            make_screenshot(page, name)

            full_traceback = traceback.format_exc()
            with open(f'{ERROR_OUTPUT_DIR}{name}.txt', 'w', encoding='utf-8') as file:
                file.write(full_traceback)

            raise e

def download_schedule_safe(schedule_date):
    '''
    Ensures to inform user about the error and to end stream if an error occur
    '''
    try:
        yield from download_schedule(schedule_date=schedule_date)
    except Exception as e:
        # send message about what failed - that ends connection with javascirpt
        message = {'type': 'error', 'payload': str(e)}
        yield f'data: {json.dumps(message)}\n\n'