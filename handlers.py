"""
Handler - функция, которая принимает на вход text (текст входящего сообщения) и context (dict), а возвращает bool:
True если шаг пройден, False если данные введены неправильно.
"""
import datetime
import re
from dispatcher import RE_CITIES_FROM, RE_CITIES_TO, get_upcoming_flights
import logging

from generate_ticket import generate_ticket

log = logging.getLogger('bot')
re_number_flight = re_count_seats = re.compile(r'\d+')
re_confirm_answer = re.compile(r'[Дд][Аа]|[Нн][еЕ][тТ]]')
re_number_phone = re.compile(r'\+?\d{1,3}\-?\d{3}\-?\d{3}\-?\d{2}\-?\d{2}')
date_pattern = re.compile(r'\d\d-\d\d-\d{4}')


def five_flights_in_str(five_flights_dict):
    result = ''
    for n, info in five_flights_dict.items():
        result += f'#{n} {info["from_"]}-{info["to"]} {info["time"]} {info["date"]}\n'
    return result


def handle_city_from(text, context):
    for city_from, re_pattern in RE_CITIES_FROM.items():
        match = re.search(re_pattern, text)
        if match:
            context['city_from'] = city_from
            log.info(f'Город отправления выбранный пользователем: {city_from}')
            return True
    return False


def handle_city_to(text, context):
    for city_to, re_pattern in RE_CITIES_TO.items():
        match = re.search(re_pattern, text)
        if match:
            context['city_to'] = city_to
            log.info(f'Город назначения выбранный пользователем: {city_to}')

            five_flights = get_upcoming_flights(city_from=context['city_from'],
                                                city_to=context['city_to'],
                                                date=datetime.datetime.now().strftime("%d-%m-%Y"))
            context['five_flights'] = five_flights_in_str(five_flights_dict=five_flights)

            if not five_flights:
                return False
            else:
                return True

    context['five_flights'] = 'wrong_input'
    return False


def handle_date(text, context):
    match = re.search(date_pattern, text)
    if match:
        date = match.group()
        five_flights = get_upcoming_flights(city_from=context['city_from'],
                                            city_to=context['city_to'],
                                            date=date)
        context['five_flights'] = five_flights_in_str(five_flights_dict=five_flights)
        log.info(f'Дата вылета, введенная пользователем: {date}')

        return True
    return False


def handle_flight(text, context):
    match = re.search(re_number_flight, text)
    if match:
        number_flight = match.group()
        str_five_flights = context["five_flights"].strip()

        for line in str_five_flights.split('\n'):
            if number_flight == line[1]:
                flight = line[3:]
                date = flight.strip().split(' ')[-1]
                log.info(f'Пользователь выбрал рейс №{number_flight}: {flight}')
                context['date'] = date
                context['flight'] = flight
                return True
    return False


def handle_seats(text, context):
    match = re.search(re_count_seats, text)
    if match:
        count_seats = match.group()
        if 6 > int(count_seats) > 0:
            log.info(f'Выбрано мест = {count_seats}')
            context['seats'] = count_seats
            return True
    return False


def handle_comment(text, context):
    if len(text) > 200:
        return False

    context['comment'] = text
    context['user_info'] = (f"Город отправления: {context['city_from']}\n"
                            f"Город назначения: {context['city_to']}\n"
                            f"Дата: {context['date']}\n"
                            f"Рейс: {context['flight']}\n"
                            f"Количество мест: {context['seats']}\n"
                            f"Комментарий: {context['comment']}\n")
    return True


def handle_user_info(text, context):
    match = re.search(re_confirm_answer, text)
    if match:
        answer = match.group()
        if answer.lower() == "да":
            log.info("Данные корректны")
            return True
        log.info("Данные некорректны")
    return False


def handle_phone_number(text, context):
    match = re.search(re_number_phone, text)
    if match:
        phone_number = match.group()
        context['phone_number'] = phone_number
        log.info(f"Номер телефона пользователя: {phone_number}")
        return True
    return False


def handle_generate_ticket(text, context):
    return generate_ticket(context=context)
