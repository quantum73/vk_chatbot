#!/usr/bin/env python 3

import logging
import random

import requests
import vk_api
from pony.orm import db_session
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

import actions
import handlers
# from models import UserState
from models import UserState, Registration

try:
    import settings
except ImportError:
    exit("Do cp settings.py.default and set token!")

log = logging.getLogger('bot')


def configure_logging():
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter(fmt="%(levelname)s %(message)s",
                                                  datefmt="%d-%m-%Y %H:%M"))
    stream_handler.setLevel(logging.INFO)
    log.addHandler(stream_handler)

    file_handler = logging.FileHandler('bot.log', encoding='utf8')
    file_handler.setFormatter(logging.Formatter(fmt="%(asctime)s %(levelname)s %(message)s",
                                                datefmt="%d-%m-%Y %H:%M"))
    file_handler.setLevel(logging.DEBUG)
    log.addHandler(file_handler)

    log.setLevel(logging.DEBUG)


class Bot:
    """
    Сценарий регистрации на конференцию "Skillbox Conf" через vk.com
    Use Python 3.7

    Поддерживает ответы на вопросы про дату, место проведения и сценарий регистрации:
    - спрашиваем имя
    - спрашиваем email
    - говорим об успешной регистрации
    Если шаг не пройден, задаем уточняющий вопрос пока шаг не будет пройден.
    """

    def __init__(self, group_id, token):
        """
        :param group_id: group id из группы vk
        :param token: секретный токен
        """
        self.group_id = group_id
        self.token = token
        self.vk = vk_api.VkApi(token=token)
        self.long_poller = VkBotLongPoll(self.vk, self.group_id)
        self.api = self.vk.get_api()

    def run(self):
        """Запуск бота"""
        for event in self.long_poller.listen():
            try:
                self.on_event(event)
            except Exception:
                log.exception("Ошибка в обработке события")

    @db_session
    def on_event(self, event):
        """
        Отправляет сообщение назад, если это текст.

        :param event: VkBotMessageEvent object
        :return: None
        """
        if event.type != VkBotEventType.MESSAGE_NEW:
            if event.type == VkBotEventType.MESSAGE_TYPING_STATE:
                log.info("Пользователь набирает сообщение")
            elif event.type == VkBotEventType.MESSAGE_REPLY:
                log.info("Пользователь отправил сообщение")
            return

        user_id = str(event.message.peer_id)
        text = event.message.text
        state = UserState.get(user_id=user_id)

        for intent in settings.INTENTS:
            log.debug(f'User gets {intent}')
            if any(token in text.lower() for token in intent['tokens']):
                if state is not None:
                    state.delete()

                if intent['answer']:
                    self.send_text(intent['answer'], user_id)
                else:
                    self.start_scenario(user_id, intent['scenario'], text)
                break
        else:
            if state is not None:
                self.continue_scenario(text, state, user_id)
            else:
                self.send_text(settings.DEFAULT_ANSWER, user_id)

    def send_text(self, text_to_send, user_id):
        self.api.messages.send(
            message=text_to_send,
            random_id=random.randint(0, 2 ** 20),
            peer_id=user_id,
        )

    def send_image(self, image, user_id):
        upload_url = self.api.photos.getMessagesUploadServer()['upload_url']
        upload_data = requests.post(url=upload_url, files={'photo': ('image.png', image, 'image/png')}).json()
        image_data = self.api.photos.saveMessagesPhoto(**upload_data)

        owner_id = image_data[0]['owner_id']
        media_id = image_data[0]['id']
        attachment = f'photo{owner_id}_{media_id}'

        self.api.messages.send(
            attachment=attachment,
            random_id=random.randint(0, 2 ** 20),
            peer_id=user_id,
        )

    def send_step(self, step, user_id, text, context):
        if 'text' in step:
            self.send_text(step['text'].format(**context), user_id)
        if 'image' in step:
            handler = getattr(handlers, step['image'])
            image = handler(text, context)
            self.send_image(image, user_id)

    def start_scenario(self, user_id, scenario_name, text):
        scenario = settings.SCENARIOS[scenario_name]
        first_step = scenario['first_step']
        step = scenario['steps'][first_step]
        self.send_step(step, user_id, text, context={})
        UserState(user_id=user_id, scenario_name=scenario_name, step_name=first_step, context={})

    def continue_scenario(self, text, state, user_id):
        steps = settings.SCENARIOS[state.scenario_name]['steps']
        step = steps[state.step_name]

        handler = getattr(handlers, step['handler'])
        if handler(text=text, context=state.context):
            # next step
            next_step = steps[step['next_step']]
            self.send_step(next_step, user_id, text, state.context)

            if next_step['next_step']:
                # switch to next step
                state.step_name = step['next_step']
            else:
                # finish scenario
                log.info('Куплен билет на номер {phone_number}'.format(**state.context))
                Registration(phone_number=state.context['phone_number'],
                             user_info=state.context['user_info'])
                state.delete()
        else:
            # retry current step
            if step['action'] is not None:
                action_func = getattr(actions, step['action'])
                text_to_send, kwargs = action_func(state.context)

                reset_scenario_flag = kwargs.get('reset_scenario', False)
                if reset_scenario_flag:
                    state.delete()
            else:
                text_to_send = step['failure_text'].format(**state.context)

            self.send_text(text_to_send, user_id)


if __name__ == '__main__':
    configure_logging()
    bot = Bot(settings.GROUP_ID, settings.TOKEN)
    bot.run()
