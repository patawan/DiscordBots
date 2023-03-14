import discord
from bs4 import BeautifulSoup
import io
import aiohttp
import requests
from datetime import date
import re
import asyncio
import boto3
import json


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

    url_object = soup.find(
        "img", attrs={"src": re.compile("https:\/\/assets\.amuniversal\.com/[\w]+")}
    )
    image_url = url_object["src"]

    return image_url


def get_discord_token():
    from botocore.exceptions import ClientError

    secret_name = "heathbot_token"
    region_name = "us-east-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    # Decrypts secret using the associated KMS key.
    secret_dict = json.loads(get_secret_value_response["SecretString"])
    return secret_dict["HEATHBOT_TOKEN"]


async def post_to_discord(token, url_to_post):
    intents = discord.Intents.default()
    client = discord.Client(intents=intents)
    await client.login(token=token)
    channel = client.get_channel(12324234183172)
    async with aiohttp.ClientSession() as session:
        async with session.get(url_to_post) as resp:
            if resp.status != 200:
                return await channel.send("Could not download file...")
            data = io.BytesIO(await resp.read())
            await channel.send(file=discord.File(data, "HEATHCLIFF_RULES.png"))


def post_new_comic(event, context):
    comic_url = generate_url()
    todays_image = get_new_comic(comic_url)
    heathbot_token = get_discord_token()
    asyncio.run(post_to_discord(token=heathbot_token, url_to_post=todays_image))
