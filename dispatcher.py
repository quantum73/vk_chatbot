import calendar
import datetime
import re
from collections import OrderedDict

RE_CITIES_FROM = {
    'Москва': re.compile(r'[Мм]оскв[ауые]?'),
    'Барселона': re.compile(r'[Бб]арселон[ауые]?'),
    'Пекин': re.compile(r'[Пп]екин[ауые]?')
}
RE_CITIES_TO = {
    'Лондон': re.compile(r'[Лл]ондон[ауые]?'),
    'Нью-Йорк': re.compile(r'[Нн]ью-йорк[ауые]?'),
    'Берлин': re.compile(r'[Бб]ерлин[ауые]?'),
    'Мельбурн': re.compile(r'[Мм]ельбурн[ауые]?'),
}


def create_flights_list():
    curr_date = datetime.datetime.now()
    curr_year = curr_date.year
    curr_month = curr_date.month
    fligths = OrderedDict()

    calendar_obj = calendar.Calendar(firstweekday=0)
    idx_dict = 1

    for year in [curr_year, curr_year + 1]:
        for n_month in range(curr_month, 13):
            city_from_1, city_from_2, city_from_3 = list(RE_CITIES_FROM.keys())
            city_to_1, city_to_2, city_to_3, _ = list(RE_CITIES_TO.keys())

            for month_day, week_day in calendar_obj.itermonthdays2(year=year, month=n_month):

                if month_day == 11 or month_day == 20:
                    date = datetime.date(year=year, month=n_month, day=month_day)
                    time = datetime.time(hour=10, minute=5)

                    if datetime.datetime.combine(date, time) > curr_date:
                        fligths[f'flight_{idx_dict}'] = {
                            "from_": city_from_1,
                            "to": city_to_1,
                            "date": date.strftime("%d-%m-%Y"),
                            "time": time.strftime("%H:%M"),
                        }

                        idx_dict += 1

                if month_day == 5 or month_day == 17:
                    date = datetime.date(year=year, month=n_month, day=month_day)
                    time = datetime.time(hour=22, minute=45)

                    if datetime.datetime.combine(date, time) > curr_date:
                        fligths[f'flight_{idx_dict}'] = {
                            "from_": city_from_2,
                            "to": city_to_2,
                            "date": date.strftime("%d-%m-%Y"),
                            "time": time.strftime("%H:%M"),
                        }

                        idx_dict += 1

                if (week_day == 2 or week_day == 5) and month_day != 0:
                    date = datetime.date(year=year, month=n_month, day=month_day)
                    time = datetime.time(hour=17, minute=30)

                    if datetime.datetime.combine(date, time) > curr_date:
                        fligths[f'flight_{idx_dict}'] = {
                            "from_": city_from_3,
                            "to": city_to_3,
                            "date": date.strftime("%d-%m-%Y"),
                            "time": time.strftime("%H:%M"),
                        }

                        idx_dict += 1

    return fligths


flights = create_flights_list()


def get_upcoming_flights(city_from, city_to, date):
    five_flights = {}

    idx = 1
    for _, info in flights.items():
        city_name_condition = (info['from_'].lower() == city_from.lower()
                               and info['to'].lower() == city_to.lower())

        if city_name_condition:
            dates_condition = (datetime.datetime.strptime(info['date'], '%d-%m-%Y')
                               > datetime.datetime.strptime(date, '%d-%m-%Y'))

            if dates_condition:
                five_flights[idx] = info
                idx += 1

        if idx > 5:
            break

    return five_flights
