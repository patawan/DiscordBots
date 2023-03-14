import discord
from bs4 import BeautifulSoup
import io
import aiohttp
import requests
from datetime import date
import re


def generate_url(base_url="https://www.gocomics.com/heathcliff") -> str:
    today = date.today()
    year = today.year
    month = today.month
    day = today.day
    comic_url = f"{base_url}/{year}/{month}/{day}"

    return comic_url


def get_new_comic(url: str) -> str:
    r = requests.get(url)
    soup = BeautifulSoup(r.content, "html.parser")
    # get picture url page

    url_object = soup.find_all(
        "img", attrs={"src": re.compile("https:\/\/assets\.amuniversal\.com/[\w]+")}
    )
    image_url = url_object["src"]

    return image_url


async def post_to_discord(url_to_post):
    client = discord.Client()
    channel = client.get_channel(12324234183172)
    async with aiohttp.ClientSession() as session:
        async with session.get(url_to_post) as resp:
            if resp.status != 200:
                return await channel.send("Could not download file...")
            data = io.BytesIO(await resp.read())
            await channel.send(file=discord.File(data, "HEATHCLIFF_RULES.png"))


def post_new_comic():
    comic_url = generate_url()
    todays_image = get_new_comic(comic_url)
    post_to_discord(todays_image)
