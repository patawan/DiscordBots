import discord
import io
import aiohttp
from datetime import datetime
import boto3
import json
import pytz
import comics


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


intents = discord.Intents.default()
client = discord.Client(intents=intents)
heathbot_token = get_discord_token()


@client.event
async def on_ready():
    print("Logged in & connected")
    ch = comics.search("heathcliff", date=datetime.now(tz=pytz.timezone("US/Arizona")))
    comic_url = ch.image_url
    # todays_image = get_new_comic(comic_url)
    print(comic_url)
    channel = client.get_channel(1083473604185960548)
    print(channel)
    async with aiohttp.ClientSession() as session:
        async with session.get(comic_url) as resp:
            if resp.status != 200:
                return await channel.send("Could not download file...")
            data = io.BytesIO(await resp.read())
            await channel.send(file=discord.File(data, "HEATHCLIFF_RULES.png"))

    await client.close()


def post_new_comic(event, context):
    discord_token = get_discord_token()
    client.run(discord_token)
