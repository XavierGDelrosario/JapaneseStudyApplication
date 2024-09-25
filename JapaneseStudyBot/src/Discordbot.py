import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import time
from selenium.common.exceptions import NoSuchElementException
from KanjiFinder import scrape_kanji_images
from KanjiFinder import search_images
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

TOKEN = os.getenv("DISCORD_TOKEN")
intents = discord.Intents.default()
intents.messages = True  # Enable message intents

class MyClient(discord.Client):
    n1_id = 1287322325242482719
    n2_id = 1287322342195859467
    n3_id = 1287322367068209195
    n4_id = 1287322385422352489
    n5_id = 1287322399485857814
    
    def __init__(self, **options):
        super().__init__(intents=intents, **options)
        self.scheduler = AsyncIOScheduler()
        self.scheduler.start()

    async def on_ready(self):
        print(f'Logged in as {self.user}')
        self.scheduler.add_job(self.send_daily_message, 'cron', hour=12, minute=0)

    async def on_message(self, message):
        if message.author == self.user:
            return
        time.sleep(1)
        await message.channel.send("お探しします。少々お待ちください。")
        if message.content.startswith('!random'):
            await self.handle_random(message)
        elif message.content.startswith('!search'):
            await self.handle_search(message)
        elif message.content.startswith('!daily'):
            await self.send_daily_message()
        else:
            time.sleep(5)
            await message.channel.send("その命令がわかりません。申し訳ございません。")

    async def handle_random(self, message):
        try:
            result = {}
            message_parts = message.content.split()
            if len(message_parts) < 2:
                result = scrape_kanji_images("All")
            else:
                result = scrape_kanji_images(message_parts[1].upper())
            await message.channel.send(file=discord.File(result['kanji_image_path']))
            if os.path.exists(result['kanji_examples_path']):
                await message.channel.send(file=discord.File(result['kanji_examples_path']))
        except NoSuchElementException as e:
            await message.channel.send("Invalid command")
        except Exception as e:
            await message.channel.send(f"Error occurred: {e}")

    async def handle_search(self, message):
        try:
            result = {}
            message_parts = message.content.split()
            if len(message_parts) < 2:
                raise ValueError()
            result = search_images(message_parts[1])
            await message.channel.send(file=discord.File(result['kanji_image_path']))
            if os.path.exists(result['kanji_examples_path']):
                await message.channel.send(file=discord.File(result['kanji_examples_path']))
        except ValueError as e:
            raise
        except NoSuchElementException as e:
            await message.channel.send("Invalid command")
        except Exception as e:
            await message.channel.send(f"Error occurred: {e}")

    async def send_daily_message(self):
        for i in range(1, 6):  # Loop from 1 to 5
            channel_id = getattr(self, f'n{i}_id') 
            channel = self.get_channel(channel_id)
            if channel:
                try: 
                    result = scrape_kanji_images(f'N{i}')
                    await channel.send(file=discord.File(result['kanji_image_path']))
                    if os.path.exists(result['kanji_examples_path']):
                        await channel.send(file=discord.File(result['kanji_examples_path']))
                except Exception as e:
                    print(f'Error occurred: {e}')
   
client = MyClient()
client.run(TOKEN)