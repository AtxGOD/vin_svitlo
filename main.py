import requests
from lxml import etree
import telebot
import threading
from time import sleep
from datetime import datetime, timedelta

bot = telebot.TeleBot('711607418:AAGdPiKLvacjcs65JnQFDCoHnN07kmOd7rc')

MEMBERS = {
    576030168: ['own',
                {
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
                }],
    5864394563: ['natasha',
                {
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
                }],
    5567513364: ['mama', {
                    'search_type': 0,
                    'city': 'м. Вінниця (Вінницька Область/М.Вінниця)',
                    'city_id': 510100000,
                    'street': 'вулиця Академіка Янгеля',
                    'street_id': 1730,
                    'house': 85,
                    'house_id': 43598,
                    'form_build_id': 'form-0Q76a3fnG_kc3Y__roT7kVSW_d5sWNMrq_jJaEukkik',
                    'form_id': 'disconnection_detailed_search_form',
                    '_triggering_element_name': 'op',
                    '_triggering_element_value': 'Показати',
                    '_drupal_ajax': 1,
                    'ajax_page_state[theme]': 'personal',
                }],
    1461586134: ['ala', {
                    'search_type': 0,
                    'city': 'м. Вінниця (Вінницька Область/М.Вінниця)',
                    'city_id': 510100000,
                    'street': 'вулиця Данила Галицького',
                    'street_id': 1078,
                    'house': 16,
                    'house_id': 31703,
                    'form_build_id': 'form-nqpbXmqhUp57lGVhqo5rhltagaBSRor-KnOiWau8H0M',
                    'form_id': 'disconnection_detailed_search_form',
                    '_triggering_element_name': 'op',
                    '_triggering_element_value': 'Показати',
                    '_drupal_ajax': 1,
                    'ajax_page_state[theme]': 'personal',
                }],
}


def prepare_to_send(text):
    text = text.replace('disconnect_100', '🟥')
    text = text.replace('disconnect_50', '🟨')
    text = text.replace('no_disconnect', '🟩')
    return text


def load_disconnects(data):
    resp = False
    for i in range(5):
        resp = requests.post(
            'https://voe.com.ua/disconnection/detailed?ajax_form=1&_wrapper_format=drupal_ajax&_wrapper_format=drupal_ajax',
            data=data
        )
        if resp.status_code == 200:
            break
        else:
            print('sleep(2)')
            sleep(2)

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
    print('message.chat.id', message.chat.id)
    result_dict, result = load_disconnects(MEMBERS[message.chat.id][1])
    result = prepare_to_send(result)

    bot.send_message(message.chat.id, result)


def send_reminder():
    while True:
        for member in MEMBERS:
            print(f'start send to member: {member}')
            today = datetime.today() + timedelta(hours=3)
            res = ''
            try:
                f = open(MEMBERS[member][0] + ".txt", "r")
                res = f.read()
            except FileNotFoundError:
                f = open(MEMBERS[member][0] + ".txt", "w")
                f.close()

            if res == '':
                result_dict, result = load_disconnects(MEMBERS[member][1])
                f = open(MEMBERS[member][0] + ".txt", "w")
                f.write(f"{today.day}.{today.month}:{result}")
                f.close()
                f = open(MEMBERS[member][0] + ".txt", "r")
                res = f.read()

            date_log = res.split(':')[0]
            disconnections = res.split(':')[1]
            result_dict, result = False, False

            if today.minute % 10 == 0:
                result_dict, result = load_disconnects(MEMBERS[member][1])
                if date_log != f"{today.day}.{today.month}" or disconnections != result:
                    f = open(MEMBERS[member][0] + ".txt", "w")
                    f.write(f"{today.day}.{today.month}:{result}")
                    f.close()

                    result = prepare_to_send(result)
                    bot.send_message(member, 'Графік змінився!')
                    bot.send_message(member, result)

            if today.minute == 30:
                if not result_dict:
                    result_dict, result = load_disconnects(MEMBERS[member][1])
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
                    bot.send_message(member, 'Через пів години вимкнуть світло 🕯')
                elif status == 'disconnect_50' and status_before != 'disconnect_50':
                    bot.send_message(member, 'Через пів години можливо вимкнуть світло 🕯')
                elif status == 'no_disconnect':
                    if status_before == 'disconnect_100':
                        bot.send_message(member, 'Через пів години увімкнуть світло 💡')
                    elif status_before == 'disconnect_50':
                        bot.send_message(member, 'Якщо світло вимикали, через пів години увімкнуть світло 💡')

            print(f'end send to member: {member}')

        sleep(30)


t = threading.Thread(target=send_reminder)
t.start()


if __name__ == '__main__':
    bot.infinity_polling()
