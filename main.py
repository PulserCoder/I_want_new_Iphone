import re

import requests
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
import schedule
import time
import asyncio
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from webdriver_manager.chrome import ChromeDriverManager

API_TOKEN = '7499180535:AAFCLQgZUn2pM3OWyIdw-56ki223pY78cjA'
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

tracked_items = {}
chat_id = '738279824'  # Замените на ваш реальный чат ID


def get_price(url):
    try:
        options = Options()
        options.headless = True
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get(url)
        time.sleep(5)  # Даем время странице полностью загрузиться

        # Попробуем несколько вариантов селекторов
        selectors = [
            'h3[data-auto="snippet-price-current"] span[class="_3qYEe"] + span',  # первоначальный селектор
            'h3[data-auto="snippet-price-current"]',  # альтернативный селектор
        ]

        price_element = None
        for selector in selectors:
            try:
                price_element = driver.find_element(By.CSS_SELECTOR, selector)
                if price_element:
                    break
            except:
                continue

        if price_element:
            price_text = price_element.text.strip()
            price_text = re.sub(r'[^\d]', '', price_text)  # Удаление всех символов, кроме цифр
            price = float(price_text)
            driver.quit()
            return price
        else:
            print("Не удалось найти элемент с ценой")
            driver.quit()
            return None
    except Exception as e:
        print(f"Ошибка при получении цены: {e}")
        if 'driver' in locals():
            driver.quit()
        return None
async def send_message(chat_id, text):
    await bot.send_message(chat_id, text, parse_mode='html')


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.reply("Добро пожаловать в Price Tracker Bot!")


@dp.message_handler(commands=['track'])
async def track_item(message: types.Message):
    url = message.get_args()
    if url:
        current_price = get_price(url)
        if current_price is not None:
            tracked_items[url] = current_price
            await message.reply(f"Отслеживаю новый товар: {url} с ценой {current_price}")
        else:
            await message.reply(f"Не удалось получить цену для {url}. Пожалуйста, проверьте ссылку.")
    else:
        await message.reply("Пожалуйста, укажите URL для отслеживания.")


async def check_price_change():
    global tracked_items, chat_id  # Сделать переменные доступными в глобальной области видимости
    for url, last_price in tracked_items.items():
        current_price = get_price(url)
        if current_price is not None:
            if current_price != last_price:
                await send_message(chat_id, f"<b>Цена изменилась для {url}: {last_price} -> {current_price}</b>\n<u>пифпифпиф</u")
            else:
                await send_message(chat_id, f"Цена для {url} осталась прежней: {current_price}")
            tracked_items[url] = current_price
        else:
            await send_message(chat_id, f"Не удалось получить текущую цену для {url}")


async def scheduler():
    while True:
        schedule.run_pending()
        await asyncio.sleep(1)


def run_check():
    asyncio.create_task(check_price_change())


schedule.every(10).minutes.do(run_check)


async def on_startup(dp):
    asyncio.create_task(scheduler())


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup)
