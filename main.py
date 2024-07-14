import requests
from lxml import etree
import telebot
import threading
from time import sleep
from datetime import datetime, timedelta

bot = telebot.TeleBot('711607418:AAGdPiKLvacjcs65JnQFDCoHnN07kmOd7rc')


def prepare_to_send(text):
    text = text.replace('disconnect_100', '🟥')
    text = text.replace('disconnect_50', '🟨')
    text = text.replace('no_disconnect', '🟩')
    return text


def load_disconnects():
    data = {
        'search_type': 0,
        'city': 'с. Сальник (Калинівський Район/М.Калинівка)',
        'city_id': 521687503,
        'street': 'вулиця Берегова',
        'street_id': 9689,
        'house': 1,
        'house_id': 221970,
        'form_build_id': 'form-sqhRRQYTYry9bnbZ-XzPBbfijpqvrQMGaly55xGta7w',
        'form_id': 'disconnection_detailed_search_form',
        '_triggering_element_name': 'op',
        '_triggering_element_value': 'Показати',
        '_drupal_ajax': 1,
        'ajax_page_state[theme]': 'personal',
    }
    resp = requests.post('https://voe.com.ua/disconnection/detailed?ajax_form=1&_wrapper_format=drupal_ajax&_wrapper_format=drupal_ajax', data=data)

    res_payload_dict = resp.json()
    data = res_payload_dict[-1]['data']

    doc = etree.XML(data)

    xp_current_day = doc.xpath("//div[contains(@class, 'current_day')]")
    xp_disconnections = xp_current_day[1:]
    xp_other_day = doc.xpath("//div[contains(@class, 'other_day')]")
    xp_disconnections += xp_other_day[1:25]

    result = {}
    count = -1

    for day in xp_disconnections:
        count += 1
        if len(str(count)) == 1:
            num = f'0{count}'
        else:
            num = str(count)
        if 'has_disconnection' in day.attrib['class']:
            if 'confirm_1' in day.attrib['class']:
                result[num] = 'disconnect_100'
            elif 'confirm_0' in day.attrib['class']:
                result[num] = 'disconnect_50'
        else:
            result[num] = 'no_disconnect'

    text_result = ''
    for t in result:
        text_result += f'{t} {result[t]}  {t} {result[str(int(t)+24)]}\n'
        if t == '23':
            break
    return result, text_result


@bot.message_handler(commands=['load'])
def reload_list(message):
    result_dict, result = load_disconnects()
    result = prepare_to_send(result)

    bot.send_message(message.chat.id, result)
    print('message.chat.id', message.chat.id)


def send_reminder():
    while True:
        today = datetime.today() + timedelta(hours=3)
        res = ''
        try:
            f = open("disconects.txt", "r")
            res = f.read()
        except FileNotFoundError:
            f = open("disconects.txt", "w")
            f.close()
        
        if res == '':
            result_dict, result = load_disconnects()
            f = open("disconects.txt", "w")
            f.write(f"{today.day}.{today.month}:{result}")
            f.close()
            f = open("disconects.txt", "r")
            res = f.read()
            
        date_log = res.split(':')[0]
        disconnections = res.split(':')[1]

        if today.minute % 10 == 0:
            result_dict, result = load_disconnects()
            if date_log != f"{today.day}.{today.month}" or disconnections != result:
                f = open("disconects.txt", "w")
                f.write(f"{today.day}.{today.month}:{result}")
                f.close()

                result = prepare_to_send(result)
                bot.send_message(576030168, 'Графік змінився!')
                bot.send_message(576030168, result)
                bot.send_message(5864394563, 'Графік змінився!')
                bot.send_message(5864394563, result)

        if today.minute == 30:
            result_dict, result = load_disconnects()
            if int(date_log.split('.')[0]) == today.day and today.hour != 23:
                status_before = result_dict[str(today.hour) if len(str(today.hour)) > 1 else '0' + str(today.hour)]
                status = result_dict[str(today.hour+1) if len(str(today.hour+1)) > 1 else '0' + str(today.hour+1)]
            else:
                if int(date_log.split('.')[0]) == today.day and today.hour == 23:
                    status_before = result_dict['23']
                    status = result_dict['24']
                else:
                    status_before = result_dict[str(today.hour+23) if len(str(today.hour+23)) > 1 else '0' + str(today.hour+23)]
                    status = result_dict[str(today.hour+24) if len(str(today.hour+24)) > 1 else '0' + str(today.hour+24)]

            if status == 'disconnect_100' and status_before != 'disconnect_100':
                bot.send_message(576030168, 'Через пів години вимкнуть світло 🕯')
                bot.send_message(5864394563, 'Через пів години вимкнуть світло 🕯')
            elif status == 'disconnect_50' and status_before != 'disconnect_50':
                bot.send_message(576030168, 'Через пів години можливо вимкнуть світло 🕯')
                bot.send_message(5864394563, 'Через пів години можливо вимкнуть світло 🕯')
            elif status == 'no_disconnect':
                if status_before == 'disconnect_100':
                    bot.send_message(576030168, 'Через пів години увімкнуть світло 💡')
                    bot.send_message(5864394563, 'Через пів години увімкнуть світло 💡')
                elif status_before == 'disconnect_50':
                    bot.send_message(576030168, 'Якщо світло вимикали, через пів години увімкнуть світло 💡')
                    bot.send_message(5864394563, 'Якщо світло вимикали, через пів години увімкнуть світло 💡')

        sleep(40)


t = threading.Thread(target=send_reminder)
t.start()


if __name__ == '__main__':
    bot.infinity_polling()
