from dispatcher import RE_CITIES_TO, RE_CITIES_FROM

RESET_SCENARIO = {"reset_scenario": True}


def get_list_cities_from(context):
    text = "Название города неверно или рейсов из него нет.\nВот список городов, из которых есть рейсы:\n"
    for city in list(RE_CITIES_FROM.keys()):
        text += f'- {city}\n'
    return text, {}


def get_list_cities_to_or_reset(context):
    if context['five_flights'] == 'wrong_input':
        text = "Название города неверно или рейсов туда нет.\nВот список городов, в которые есть рейсы:\n"
        for city in list(RE_CITIES_TO.keys()):
            text += f'- {city}\n'
        return text, {}

    text = f"Рейсов между {context['city_from']} - {context['city_to']} нет!"
    return text, RESET_SCENARIO


def wrong_user_data(context):
    return "Вы не подтвердили корректность данных. Начните сначала.", RESET_SCENARIO
