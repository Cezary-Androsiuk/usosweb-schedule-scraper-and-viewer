import os
import keyboard
import pickle
import time

import asyncio
import aiohttp
from playwright.async_api import async_playwright

LOGIN = os.getenv("UWB_LOGIN")
PASSWORD = os.getenv("UWB_PASSWORD")

SESSION_COOKIES_FILE = 'session_cookies.pkl'
STATIC_IMAGES_PATH = 'static/'
IMAGE_PREFIX = 'schedule-'
IMAGE_EXT = '.gif'

LOGIN_URL = 'https://cas.uwb.edu.pl/cas/login'
USOSWEB_URL = 'https://usosweb.uwb.edu.pl/kontroler.php'
LOGOUT_URL = USOSWEB_URL + '?_action=logowaniecas/wyloguj'
TEST_SESSION_URL = USOSWEB_URL + '?_action=home/index'


async def __create_cookies() -> bool:
    async with async_playwright() as p:
        print('Creating cookies...')
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto(LOGIN_URL, wait_until="domcontentloaded")
        time.sleep(0.2)

        # find credentials fields
        await page.locator("#username").fill(LOGIN)
        await page.locator("#password").fill(PASSWORD)
        time.sleep(0.2)

        # press 'login' button
        await page.locator(".form-button").click()
        time.sleep(0.2)
        
        print('  Logging in...')
        
        # wait for the redirect
        logout_element = page.locator('div#logout-menu')
        if not await logout_element.is_visible():
            print('  Logging in failed')
            return False;

        print('  Logged in')

        # save cookies
        cookies = await context.cookies()
        with open(SESSION_COOKIES_FILE, 'wb') as f:
            pickle.dump(cookies, f);
        
        print('  Cookies saved')
        
        await browser.close()

async def __contains_logout_href(page) -> bool:
    tested_element = page.locator(f'a[href="{LOGOUT_URL}"]')
    return await tested_element.is_visible()

async def __cookies_valid() -> bool:
    async with async_playwright() as p:
        print('Veryfing cookies...')
        browser = await p.chromium.launch(headless=True)
        
        # load cookies
        context = await browser.new_context()
        try:
            with open(SESSION_COOKIES_FILE, 'rb') as f:
                cookies = pickle.load(f)
        except FileNotFoundError:
            print('  No cookies to load')
            return False;
        except Exception as e:
            print(f'  Error while loading session cookies: {e}')
            return False
        
        print('  Cookies loaded')

        await context.add_cookies(cookies=cookies)
        page = await context.new_page()

        # open page
        await page.goto(TEST_SESSION_URL, wait_until="domcontentloaded")

        # verify 
        if await __contains_logout_href(page):
            print('  Cookies are valid')
            return True
        else:
            print('  Cookies are invalid')
            return False;

async def __correct_url(page, image_url: str) -> str:
    if image_url.startswith("//"):
        image_url = "https:" + image_url
    elif image_url.startswith("/"):
        # Potrzebujesz pełnego adresu URL
        base_url = page.url.split('/')[0] + "//" + page.url.split('/')[2]
        image_url = base_url + image_url
    return image_url

async def __download_image(page, image_url: str, path: str):
    response = await page.request.get(image_url)
    if response.ok:
        # 4. Zapisz obrazek do pliku
        with open(path, "wb") as f:
            f.write(await response.body())
        print('Image downloaded correctly')
    else:
        raise Exception(f'Error while downloading image: {response.status}')
    # async with aiohttp.ClientSession() as session:
    #     async with session.get(image_url) as response:
    #         if response.status == 200:
    #             # save to file
    #             with open(path, "wb") as f:
    #                 f.write(await response.read())
    #             print('Image downloaded correctly')
    #         else:
    #             raise Exception(f'Error while downloading image: {response.status}')

def schedule_image_name(schedule_date: str) -> str:
    return IMAGE_PREFIX + str(schedule_date) + IMAGE_EXT

async def update_cookies():
    if not await __cookies_valid():
        print('Cookies invalid')
        print('Createing new cookies..')
        await __create_cookies()

        if not await __cookies_valid():
            raise Exception("Can't start session!")
    
    print('Cookies Verified')

# 'schedule_date' need to be in format "YYYY-MM-DD"
# returns path to image
async def download_schedule_image(schedule_date: str):
    async with async_playwright() as p:
        print('Oppening schedule page...')
        browser = await p.chromium.launch(headless=True)

        # load cookies
        context = await browser.new_context()
        try:
            with open(SESSION_COOKIES_FILE, 'rb') as f:
                cookies = pickle.load(f)
        except Exception as e:
            raise Exception(f'Error while loading session cookies: {e}')
        
        print('  Cookies loaded')

        await context.add_cookies(cookies=cookies)
        page = await context.new_page()
        
        print('  Page created')

        schedule_url = f'{USOSWEB_URL}?_action=home/plan&plan_format=gif&plan_week_sel_week={schedule_date}'
        await page.goto(schedule_url, wait_until="domcontentloaded")

        print('  Redirected to page')

        if not await __contains_logout_href(page):
            raise Exception('Page loading failed')
        
        print('  Schedule page is open now')
        
        # print('Sleeping 2s...')
        # time.sleep(2)

        # locate image and read source
        image_locator = page.locator("div.do_not_print > img.schedimg")
        image_url = await image_locator.get_attribute("src")
        if not image_url:
            raise Exception("Image not found or Image does not have source")

        print(f'Scrapped url: {image_url}')
        # # correct URL if needed
        # image_url = await __correct_url(page=page, image_url=image_url)
        # print(f'Corrected url: {image_url}')

        # create path if not exist
        if not os.path.exists(STATIC_IMAGES_PATH):
            os.mkdir(STATIC_IMAGES_PATH)
        
        # assemble image path
        image_path = STATIC_IMAGES_PATH + schedule_image_name(schedule_date)
        print(f'Image path: {image_path}')

        # downlaod image
        await __download_image(page=page, image_url=image_url, path=image_path)

        print('Image downloaded')

        await browser.close()



async def main():
    try:
        await download_schedule_image('2025-10-06')
    except Exception as e:
        print(f'Downloading schedule failed! Reason: {e}')
    

if __name__ == '__main__':
    asyncio.run(main())