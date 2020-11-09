from datetime import datetime
from copy import deepcopy
from unittest import TestCase
from unittest.mock import patch, Mock, ANY

from pony.orm import db_session, rollback
from vk_api.bot_longpoll import VkBotMessageEvent

import settings
from bot import Bot
from actions import get_list_cities_from, get_list_cities_to_or_reset, wrong_user_data
from dispatcher import get_upcoming_flights
from generate_ticket import generate_ticket
from handlers import five_flights_in_str


def isolate_db(test_func):
    def wrapper(*args, **kwargs):
        with db_session as session:
            test_func(*args, **kwargs)
            rollback()

    return wrapper


class Test1(TestCase):
    RAW_IVENT = {
        'type': 'message_new',
        'object': {'message': {'date': 1593428756, 'from_id': 359473367, 'id': 68, 'out': 0, 'peer_id': 359473367,
                               'text': 'hi bot', 'conversation_message_id': 67, 'fwd_messages': [], 'important': False,
                               'random_id': 0, 'attachments': [], 'is_hidden': False},
                   'client_info': {'button_actions': ['text', 'vkpay', 'open_app', 'location', 'open_link'],
                                   'keyboard': True, 'inline_keyboard': True, 'lang_id': 0}},
        'group_id': 196646424,
        'event_id': '93e3e4c1d2be4f06567995ed755ff8289cdbc5d9'}

    def test_run(self):
        count = 5
        obj = {}
        events = [obj] * count
        long_poller_mock = Mock(return_value=events)
        long_poller_listen_mock = Mock()
        long_poller_listen_mock.listen = long_poller_mock

        with patch('bot.vk_api.VkApi'):
            with patch('bot.VkBotLongPoll', return_value=long_poller_listen_mock):
                bot = Bot('', '')
                bot.on_event = Mock()
                bot.send_image = Mock()
                bot.run()

                bot.on_event.assert_called()
                bot.on_event.assert_any_call(obj)

                assert bot.on_event.call_count == count

    TEST_CITY_FROM = 'Москва'
    TEST_CITY_TO = 'Лондон'
    TEST_DATE = '20-07-2020'
    TEST_FIVE_FLIGTHS = five_flights_in_str(
        get_upcoming_flights(city_from=TEST_CITY_FROM, city_to=TEST_CITY_TO, date=TEST_DATE))
    TEST_FLIGTH = '1'
    for i in TEST_FIVE_FLIGTHS.strip().split('\n'):
        if TEST_FLIGTH == i[1]:
            TEST_NAME_FLIGTH = i[3:]
    TEST_SEATS = '2'
    TEST_COMMENT = 'Бла бла'
    TEST_INFO = (f"Город отправления: {TEST_CITY_FROM}\n"
                 f"Город назначения: {TEST_CITY_TO}\n"
                 f"Дата: {TEST_NAME_FLIGTH.strip().split(' ')[-1]}\n"
                 f"Рейс: {TEST_NAME_FLIGTH}\n"
                 f"Количество мест: {TEST_SEATS}\n"
                 f"Комментарий: {TEST_COMMENT}\n")
    TEST_NUMBER_PHONE = '89998881122'

    INPUTS = [
        'Привет',
        '/help',
        '/ticket',
        'Мслкц',
        TEST_CITY_FROM,
        'Something',
        TEST_CITY_TO,
        'wrong_date',
        TEST_DATE,
        '0',
        TEST_FLIGTH,
        '100',
        TEST_SEATS,
        's' * 201,
        TEST_COMMENT,
        'да',
        '9031unj4109',
        TEST_NUMBER_PHONE,
    ]

    EXPECTED_OUTPUTS = [
        settings.DEFAULT_ANSWER,
        settings.INTENTS[1]['answer'],
        settings.SCENARIOS['buy_ticket']['steps']['step1']['text'],
        get_list_cities_from(context=None)[0],
        settings.SCENARIOS['buy_ticket']['steps']['step2']['text'],
        get_list_cities_to_or_reset(context={'five_flights': 'wrong_input'})[0],
        settings.SCENARIOS['buy_ticket']['steps']['step3']['text'],
        settings.SCENARIOS['buy_ticket']['steps']['step3']['failure_text'],
        settings.SCENARIOS['buy_ticket']['steps']['step4']['text'].format(five_flights=TEST_FIVE_FLIGTHS),
        settings.SCENARIOS['buy_ticket']['steps']['step4']['failure_text'],
        settings.SCENARIOS['buy_ticket']['steps']['step5']['text'],
        settings.SCENARIOS['buy_ticket']['steps']['step5']['failure_text'],
        settings.SCENARIOS['buy_ticket']['steps']['step6']['text'],
        settings.SCENARIOS['buy_ticket']['steps']['step6']['failure_text'],
        settings.SCENARIOS['buy_ticket']['steps']['step7']['text'].format(user_info=TEST_INFO),
        settings.SCENARIOS['buy_ticket']['steps']['step8']['text'],
        settings.SCENARIOS['buy_ticket']['steps']['step8']['failure_text'],
        settings.SCENARIOS['buy_ticket']['steps']['finish']['text'].format(phone_number=TEST_NUMBER_PHONE),
    ]

    @isolate_db
    def test_run_ok(self):
        send_mock = Mock()
        api_mock = Mock()
        api_mock.messages.send = send_mock

        events = []
        for input_text in self.INPUTS:
            event = deepcopy(self.RAW_IVENT)
            event['object']['message']['text'] = input_text
            events.append(VkBotMessageEvent(event))

        long_poller_mock = Mock()
        long_poller_mock.listen = Mock(return_value=events)

        with patch('bot.VkBotLongPoll', return_value=long_poller_mock):
            bot = Bot('', '')
            bot.api = api_mock
            bot.send_image = Mock()
            bot.run()

        assert send_mock.call_count == len(self.INPUTS)

        real_outputs = []
        for call in send_mock.call_args_list:
            args, kwargs = call
            real_outputs.append(kwargs['message'])

        assert real_outputs == self.EXPECTED_OUTPUTS

    def test_generate_image(self):
        context = {
            "city_from": "Москва",
            "city_to": "Лондон",
            "date": "31-08-2020",
            "flight": "Москва-Лондон 10:05 11-09-2020",
            "seats": "1",
        }
        ticket_file = generate_ticket(context=context)
        with open("files/ticket-example.png", "rb") as f:
            ticket_example = f.read()

        assert ticket_file.read() == ticket_example
