from flask import Flask, render_template, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import requests
from bs4 import BeautifulSoup

from concurrent.futures import ThreadPoolExecutor
import threading

app = Flask(__name__)

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")


last_data = {
    "token_info": None,
    "liquidity_infos": ["Нет данных"] * 5
}


def get_dex_info(url):
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    try:
        driver.get(url)
        elements = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, '[class="truncate"]'))
        )
        unwanted_texts = ["Search network, dex or tokens"]

        liquidity_info = []
        for element in elements:
            text = element.text.strip()
            if text and not any(unwanted in text for unwanted in unwanted_texts):
                liquidity_info.append(text)

        return liquidity_info[0] if liquidity_info else "Нет данных"
    finally:
        driver.quit()


def update_data_in_background():
    global last_data
    urls = [
        "https://www.geckoterminal.com/en/ton/pools/EQDRanLglGDiS5m-oHcER6ZKqpVWkkmHMkryFunjcIX2aJeT",
        "https://www.geckoterminal.com/ton/pools/EQCjzPfYbNMnFbSDAe0tNSVIv-xwDY1zCOqXwqGsHsWSSBFu",
        "https://www.geckoterminal.com/ton/pools/EQD6tTEqOXEjdldE7RrjKjtXirH0jtOpmdldQDC10bvWHizM",
        "https://www.geckoterminal.com/ton/pools/EQBEcpt6LdHe4p0Ce5S2XUO7WgwGwg9pxUq58zjfP2XADuxK",
        "https://www.geckoterminal.com/ton/pools/EQCcxACHx5jG7JK5hF6XDK0EIrVS9gp8rk1q6r9oGCiuEMrs"
    ]

    with ThreadPoolExecutor() as executor:
        liquidity_infos = list(executor.map(get_dex_info, urls))

    token_address = "EQAWVv2x6txoc5Nel9CltbfYSBMOOf0R9sb7GnqY-4ncmjcQ"
    token_info = get_token_info(token_address)

    last_data = {
        "token_info": token_info,
        "liquidity_infos": liquidity_infos
    }


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/update_data')
def update_data():

    data = {
        "token_info": last_data["token_info"],
        "liquidity_info": last_data["liquidity_infos"][0],
        "liquidity_info1": last_data["liquidity_infos"][1],
        "liquidity_info2": last_data["liquidity_infos"][2],
        "liquidity_info3": last_data["liquidity_infos"][3],
        "liquidity_info4": last_data["liquidity_infos"][4],
    }

    threading.Thread(target=update_data_in_background).start()

    return jsonify(data)


def get_token_info(token_address):
    url = f"https://tonviewer.com/{token_address}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return None
    soup = BeautifulSoup(response.content, 'html.parser')
    classes_to_track = {
        "Token Name and Symbol": "bdtytpm nygz236 t1g1t0q6 b1qs25iq t1wzd7oa",
    }
    token_info = {}
    for description, class_name in classes_to_track.items():
        elements = soup.find_all('div', class_=class_name)
        if elements:
            cleaned_texts = []
            for element in elements:
                text = element.get_text(strip=True)
                try:
                    value = int(''.join(filter(str.isdigit, text.split('.')[0])))
                    cleaned_texts.append(161803398 - value)
                except ValueError:
                    cleaned_texts.append(f"Unable to convert text to number: {text}")
            token_info[description] = (class_name, cleaned_texts)
    return token_info


if __name__ == '__main__':
    update_data_in_background()
    app.run(debug=True)
