import discord
import aiohttp
import asyncio
import os
from flask import Flask
from threading import Thread
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.environ["TOKEN"]

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

cache_data = None
cache_time = None

TRIGGERS = [
    "де той піздюк",
    "де піздюк",
    "де vulture",
    "де той піздюк?",
    "де піздюк?",
    "де vulture?",
    "where is vulture",
    "where is vulture?",
]

app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

Thread(target=run_flask).start()

# BOT FUNCTIONS
async def get_vulture():
    global cache_data, cache_time
    if cache_data and (datetime.utcnow() - cache_time).seconds < 300:
        return cache_data
    url = "https://whereisvulture.com/data/vulture-locations.json"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            data = await r.json()
    cache_data = data
    cache_time = datetime.utcnow()
    return data

async def send_vulture_timer(channel):
    data = await get_vulture()
    cop1_raw = data["cop1"]
    cop2_raw = data["cop2"]

    cop1 = cop1_raw.split(" (")[0].lower()
    cop2 = cop2_raw.split(" (")[0].lower()

    grid1 = cop1_raw.split("Grid ")[1].replace(")", "")
    grid2 = cop2_raw.split("Grid ")[1].replace(")", "")

    img1_url = f"https://whereisvulture.com/assets/{cop1}.png"
    img2_url = f"https://whereisvulture.com/assets/{cop2}.png"

    embed_info = discord.Embed(
        title="📍 Vulture Location",
        color=0x2ecc71
    )
    embed_info.add_field(name="Локація 1", value=f"**{cop1.upper()}**\nGrid {grid1}", inline=True)
    embed_info.add_field(name="Локація 2", value=f"**{cop2.upper()}**\nGrid {grid2}", inline=True)
    embed_info.add_field(name="До наступного переїзду", value="...", inline=False)

    embed_img1 = discord.Embed(color=0x2ecc71)
    embed_img1.set_image(url=img1_url)
    embed_img2 = discord.Embed(color=0x2ecc71)
    embed_img2.set_image(url=img2_url)

    info_msg = await channel.send(embed=embed_info)
    await channel.send(embed=embed_img1)
    await channel.send(embed=embed_img2)

    while True:
        now_utc = datetime.utcnow().replace(tzinfo=timezone.utc)
        gmt2 = timezone(timedelta(hours=2))
        now_gmt2 = now_utc.astimezone(gmt2)

        today_target = now_gmt2.replace(hour=14, minute=0, second=0, microsecond=0)
        if now_gmt2.weekday() == 0 and now_gmt2 < today_target:
            next_move = today_target
        else:
            days_until_monday = (7 - now_gmt2.weekday()) % 7
            if now_gmt2.weekday() == 0:
                days_until_monday = 7
            next_move = today_target + timedelta(days=days_until_monday)

        time_left = next_move - now_gmt2
        hours, remainder = divmod(time_left.seconds, 3600)
        minutes, _ = divmod(remainder, 60)

        if time_left.days >= 1:
            time_str = f"{time_left.days} дн. {hours} год. {minutes} хв."
        else:
            total_hours = hours + time_left.days * 24
            time_str = f"{total_hours} год. {minutes} хв."

        embed_info.set_field_at(2, name="До наступного переїзду", value=time_str, inline=False)
        await info_msg.edit(embed=embed_info)
        await asyncio.sleep(60)

@client.event
async def on_ready():
    print(f"Бот запущений як {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    msg = message.content.lower()
    if any(x in msg for x in TRIGGERS):
        await send_vulture_timer(message.channel)

client.run(TOKEN)