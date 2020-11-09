from io import BytesIO

from PIL import Image, ImageFont, ImageDraw

BLACK = (0, 0, 0, 255)


def generate_ticket(context):
    city_from = context['city_from']
    city_to = context['city_to']
    date = context['date']
    flight = context['flight']
    seats = context['seats']

    base = Image.open("files/ticket_base.png").convert("RGBA")

    # fonts types
    font_from_to = ImageFont.truetype("files/roboto.ttf", 25)
    font_date = ImageFont.truetype("files/roboto.ttf", 14)
    font_seats = ImageFont.truetype("files/roboto.ttf", 22)
    font_flight = ImageFont.truetype("files/roboto.ttf", 14)

    # drawing information
    draw = ImageDraw.Draw(base)
    draw.text((140, 150), city_from, font=font_from_to, fill=BLACK)
    draw.text((140, 205), city_to, font=font_from_to, fill=BLACK)
    draw.text((137, 272), date, font=font_date, fill=BLACK)
    draw.text((360, 264), seats, font=font_seats, fill=BLACK)
    draw.text((142, 330), flight, font=font_flight, fill=BLACK)

    temp_file = BytesIO()
    base.save(temp_file, 'png')
    temp_file.seek(0)

    return temp_file
