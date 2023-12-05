import telebot
from telebot import types
import requests
from bs4 import BeautifulSoup
import datetime
import pycountry

bot = telebot.TeleBot('TOKEN')
url = 'https://between-us-girls.ru/5-bukv-tinkoff-segodnya-otvet/?ysclid=lpplbfr1su592345016'

# Словарь для хранения фраз на разных языках
phrases = {
    'ru': {
        'welcome': "Привет, {user_name}! Выберите язык:",
        'selected_language': "Вы выбрали русский язык.",
        'button_text': "Нажми кнопку, чтобы узнать слово для игры 5 букв в Тинькофф.",
        'error_parsing': "Произошла ошибка при парсинге. Попробуйте еще раз позже.",
        'error_request': "Ошибка при запросе к сайту: {e}",
        'data_not_found': "Данные для сегодня не найдены на странице.",
        'learn_word_button': "🟢Узнать слово",
        'developer_button': "🟠Разработчик"
    },
    'en': {
        'welcome': "Hello, {user_name}! Choose your language:",
        'selected_language': "You have selected English language.",
        'button_text': "Press the button to get a word for the 5-letter game in Tinkoff.",
        'error_parsing': "An error occurred while parsing. Please try again later.",
        'error_request': "Error making a request to the website: {e}",
        'data_not_found': "No data found for today on the page.",
        'learn_word_button': "🟢Learn the word",
        'developer_button': "🟠Developer"
    }
}

@bot.message_handler(commands=['start'])
def handle_start(message):
    user_name = message.from_user.first_name
    markup = types.InlineKeyboardMarkup()
    russian_button = types.InlineKeyboardButton(text="🇷🇺 Русский", callback_data='lang_ru')
    english_button = types.InlineKeyboardButton(text="🇺🇸 English", callback_data='lang_en')
    markup.add(russian_button, english_button)
    bot.send_message(message.chat.id, phrases['ru']['welcome'].format(user_name=user_name), reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def callback_choose_language(call):
    user_language = call.data.split('_')[1]
    
    if user_language in phrases:
        bot.send_message(call.message.chat.id, phrases[user_language]['selected_language'])
    else:
        bot.send_message(call.message.chat.id, phrases['ru']['welcome'])
        return

    markup = types.InlineKeyboardMarkup()
    get_word_button = types.InlineKeyboardButton(text=phrases[user_language]['learn_word_button'], callback_data='get_word')
    developer_button = types.InlineKeyboardButton(text=phrases[user_language]['developer_button'], url='https://t.me/pizzaway')
    markup.add(get_word_button, developer_button)
    bot.send_message(call.message.chat.id, phrases[user_language]['button_text'], reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'get_word')
def callback_get_word(call):
    try:
        date, word = scrape_word()
        formatted_text = f"<b>{date}</b> — <code>{word}</code>"
        bot.send_message(call.message.chat.id, formatted_text, parse_mode='HTML')
    except ValueError as e:
        bot.send_message(call.message.chat.id, phrases[call.message.from_user.language_code]['error_parsing'])

def scrape_word():
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        rows = soup.find_all('tr')
        today_date = datetime.datetime.now().strftime("%d.%m.%Y")

        for row in rows:
            date_cell = row.find('td')
            if date_cell and today_date in date_cell.text:
                cells = row.find_all('td')
                if len(cells) >= 3:
                    date = cells[0].text.strip()
                    word = cells[1].text.strip()
                    return date, word

        raise ValueError(phrases['ru']['data_not_found'])

    except requests.exceptions.RequestException as e:
        raise ValueError(phrases['ru']['error_request'].format(e))
    except Exception as e:
        raise ValueError(phrases['ru']['error_parsing'])

if __name__ == "__main__":
    bot.polling(none_stop=True)

