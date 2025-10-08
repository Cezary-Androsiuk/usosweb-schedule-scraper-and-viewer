import os
import keyboard
import requests
from bs4 import BeautifulSoup
import pickle

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time

LOGIN = os.getenv("UWB_LOGIN")
PASSWORD = os.getenv("UWB_PASSWORD")

SESSION_COOKIES_FILE = 'session_cookies.pkl'

LOGIN_URL = 'https://cas.uwb.edu.pl/cas/login'
LOGOUT_URL = 'https://usosweb.uwb.edu.pl/kontroler.php?_action=logowaniecas/wyloguj'
TEST_SESSION_URL = 'https://usosweb.uwb.edu.pl/kontroler.php?_action=home/index'


# https://usosweb.uwb.edu.pl/kontroler.php?_action=home/plan&plan_format=gif&plan_week_sel_week=2025-10-06


def create_new_session_cookies():
    chrome_options = Options()

    # 2. Dodaj argument uruchamiający tryb headless
    chrome_options.add_argument("--headless")

    # 3. (Opcjonalnie, ale zalecane) Dodaj inne argumenty, które poprawiają stabilność w tle
    chrome_options.add_argument("--window-size=1920,1080") # Ustawia stały rozmiar okna
    chrome_options.add_argument("--disable-gpu") # Ważne w niektórych systemach (zwłaszcza Windows)

    driver = webdriver.Chrome(options=chrome_options)

    try:
        # Otwórz stronę logowania
        driver.get(LOGIN_URL)
        
        # --- KROK 1: Ustawianie wartości w polach input ---
        print("Szukam pola na nazwę użytkownika i hasło...")
        # Użyj WebDriverWait, aby upewnić się, że pola są załadowane
        wait = WebDriverWait(driver, 10)
        
        # Znajdź pole 'username' po jego ID i wpisz wartość
        username_field = wait.until(EC.visibility_of_element_located((By.ID, 'username')))
        username_field.send_keys(LOGIN)
        print(f"Wpisano login: {LOGIN}")

        # Znajdź pole 'password' po jego ID i wpisz wartość
        password_field = driver.find_element(By.ID, 'password')
        password_field.send_keys(PASSWORD)
        print("Wpisano hasło.")

        # --- KROK 2: Aktywacja (kliknięcie) przycisku ---
        print("Szukam przycisku logowania...")
        
        # Znajdź przycisk. Najlepiej użyć unikalnego selektora, np. name, class lub XPath.
        # W tym przypadku szukamy <input> z atrybutem type="submit" lub podobnym.
        # Jeśli to <input type="button">, możesz go znaleźć tak samo.
        login_button = driver.find_element(By.NAME, 'submit') # Zmień selektor, jeśli jest inny
        login_button.click()
        print("Kliknięto przycisk logowania.")

        # --- KROK 3: Odczytanie cookies po przekierowaniu ---
        
        # Czekamy chwilę, aby dać przeglądarce czas na przekierowanie i załadowanie nowej strony.
        # Lepszym podejściem jest czekanie na konkretny element na nowej stronie.
        print("\nCzekam na przekierowanie po zalogowaniu...")
        
        # Przykład inteligentnego czekania: poczekaj, aż pojawi się przycisk "Wyloguj"
        # To potwierdza, że jesteśmy na nowej stronie i zalogowani.
        wait.until(
            EC.visibility_of_element_located((By.XPATH, "//h1[text()='Log In Successful']"))
        )
        print("Przekierowanie zakończone sukcesem!")

        # Teraz, gdy jesteś na nowej stronie, możesz odczytać ciasteczka
        print("Pobieram ciasteczka z bieżącej sesji...")
        cookies = driver.get_cookies()
        

        if cookies:
            with open(SESSION_COOKIES_FILE, 'wb') as f:
                pickle.dump(cookies, f)
            
        else:
            print("Nie znaleziono żadnych ciasteczek.")


    except Exception as e:
        print(f"Wystąpił błąd: {e}")

    finally:
        # Na koniec zamknij przeglądarkę
        # time.sleep(5) # Krótka pauza, żeby zobaczyć efekt
        print('Closing chrome driver...')
        driver.quit()


def start_session_invalid():
    session = requests.Session()
    try:
        page_response = session.get(LOGIN_URL)
        page_response.raise_for_status()

        soup = BeautifulSoup(page_response.text, 'html.parser')

        # read token from Login Form
        execution = soup.find('input', {'name': 'execution'})
        if not execution or not execution.get('value'):
            print(f"Can't find execution value in page response: {page_response.text}")
            return
        
        execution_token = execution.get('value')
        print(f'execution token: {execution_token[:20]}...')

        # headers = {
        #     "Referer": 'cas.uwb.edu.pl',
        #     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'
        # }
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-encoding': 'gzip, deflate, br, zstd',
            'accept-language': 'pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7',
            'cache-control': 'no-cache',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://cas.uwb.edu.pl',
            'pragma': 'no-cache',
            'priority': 'u=0, i',
            'referer': 'https://cas.uwb.edu.pl/cas/login',
            'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
            # 'cookie' jest zarządzany przez obiekt session, więc nie musisz go dodawać ręcznie
            # 'content-length' jest obliczany automatycznie przez requests
        }

        payload = {
            'username': LOGIN,
            'password': PASSWORD,
            'execution': execution_token,
            # other fields
            '_eventId': 'submit',
            'geolocation': ''
        }

        print(f'payload: {payload}')

        print('Sending login form...')
        login_response = session.post(LOGIN_URL, headers=headers, data=payload)
        login_response.raise_for_status()

        with open('result.html', 'w', encoding="utf-8") as f:
            f.write(login_response.text)

        print("cases:")
        print("Nieprawidłowe hasło" in login_response.text)
        print("cas/login" in login_response.url)
        print('Udane logowanie' not in login_response.text)

        if ("Nieprawidłowe hasło" in login_response.text or "cas/login" in login_response.url) and ('Udane logowanie' not in login_response.text):
            print("Logowanie nieudane. Sprawdź dane lub logikę skryptu.")
            return None

        print("Logowanie zakończone sukcesem!")
        
        with open(SESSION_FILE, 'wb') as f:
            pickle.dump(session, f)
        print('session saved')

        with open('cookie.json', 'w') as f:
            f.write(session.cookies.get_dict())
        print('cookies saved')

    except requests.exceptions.RequestException as e:
        print(f"Network error occur: {e}")
        return


def is_session_valid(session: requests.Session):
    try: 
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://usosweb.uwb.edu.pl/kontroler.php'
        }
        response = session.get(TEST_SESSION_URL, headers=headers, allow_redirects=True)
        response.raise_for_status()

        with open('result_is_session_valid.html', 'w', encoding="utf-8") as f:
            f.write(response.text)

        if 'Wyloguj' in response.text:
            return True
        else:
            return False
    except Exception as e:
        print(f'Error while checking if session is valid! {e}')
    
    return False
    
def load_session() -> requests.Session | None:
    try:
        with open(SESSION_COOKIES_FILE, 'rb') as f:
            cookies = pickle.load(f)
        print('Session cookies loaded')
    except FileNotFoundError:
        print('No session cookies found!')
        return None;
    except Exception as e:
        print(f'Error while loading session cookies: {e}')
        return None;

    session = requests.Session()
    
    for cookie in cookies:
        session.cookies.set(cookie['name'], cookie['value'])
    print(f'cookies set: {session.cookies}')

    return session
    

def open_session() -> requests.Session:
    print('Loading old session...')
    session = load_session();
    
    if session and is_session_valid(session):
        return session
    
    print('Old session invalid')

    # Create new session if old is invalid
    print('Creating new session...')
    create_new_session_cookies()
    print('Loading new session...')
    session = load_session()

    if session and is_session_valid(session):
        return session
    
    # if new created session is invalid to, then exit
    print('New session also invalid')
    print("Can't open session")
    exit(1)

    

        
        

        


def end_seesion():
    print('Loading session...')
    session = load_session();
    
    if not session or not is_session_valid(session):
        print('Session invalid, cannot be closed')
        return
    
    
    print('Closing old session...')
    session = requests.Session()
    try:
        logout_response = session.get(LOGOUT_URL)
        logout_response.raise_for_status()

        with open('result_end_session.html', 'w', encoding="utf-8") as f:
            f.write(logout_response.text)

        if 'Udane wylogowanie' in logout_response.text:
            print('Session successfully ended!')

    except requests.exceptions.RequestException as e:
        print(f"Network error occur: {e}")
        return
    finally:
        if os.path.exists(SESSION_COOKIES_FILE):
            os.remove(SESSION_COOKIES_FILE);


if __name__ == "__main__":
    print('Choose an action (keys 1,2 or 3):')
    print('1. start session')
    print('2. continue session')
    print('3. end session')
    print('0. exit')

    actionChoosen = False
    while not actionChoosen:
        action = keyboard.read_key()

        actionChoosen = True
        if action == '1':
            print('Starting session...')
            open_session()
            # start_session_invalid()
        elif action == '2':
            print('Continuing session...')
        elif action == '3':
            print('Ending session...')
            end_seesion()
        elif action == '0':
            exit(0)
        else:
            actionChoosen = False