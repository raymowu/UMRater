import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
from discord import app_commands
import requests
import json
from enum import Enum
from fastapi import FastAPI
from pymongo import MongoClient

load_dotenv()
token = os.getenv('DISCORD_TOKEN')
mongo_uri = os.getenv('MONGODB_URI')
db_name = os.getenv('DB_NAME')

mongodb_client = MongoClient(mongo_uri)
database = mongodb_client[db_name]
print('Connected to MongoDB database!')

CHARACTERS_URL = "https://api.jikan.moe/v4/characters"
ANIMES_URL = "https://api.jikan.moe/v4/anime"

class Rating(Enum):
    Z = '10'
    S = '9'
    A = '8'
    B = '7'
    C = '5'
    D = '1'
    F = '0'

class Client(commands.Bot):
    async def on_ready(self):
        print(f'Logged on Discord as {self.user}!')
        try:
            guild = discord.Object(id=368504766889984000)   # test server
            synced = await self.tree.sync(guild=guild)
            print(f'Synced {len(synced)} commands to guild {guild.id}')
        except Exception as e:
            print(f'Error syncing commands: {e}')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = Client(command_prefix="!", intents=intents)

GUILD_ID = discord.Object(id=368504766889984000)

def get_characters_anime(id):
    try:
        res = requests.get(f'{CHARACTERS_URL}/{str(id)}/anime')
        data = res.json()
        return data['data'][0]['anime']['title']
    except Exception as e:
        print(f'Could not find anime for char id {id}')

def search_character(name):
    params = {
        'limit' : '9',
        'q' : name,
        # 'letter' : name[0]
        # 'order_by' : 'name',
        # 'sort' : 'desc'
    }
    res = requests.get(CHARACTERS_URL, params=params)
    data = res.json()
    return data['data']

def search_anime(name):
    params = {
        'limit' : '9',
        'q' : name,
        'order_by' : 'favorites',
        'sort' : 'desc'
    }
    res = requests.get(ANIMES_URL, params=params)
    data = res.json()
    return data['data']

class View(discord.ui.View):
    mal_id = int()
    @discord.ui.select(
        placeholder = "Choose a Rating!",
        min_values = 1,
        max_values = 1,
        options = [
            discord.SelectOption(
                label="💎 Z Tier",
                description="These are the waifus that live rent-free in your heart forever. ",
                value = Rating.Z
            ),
            discord.SelectOption(
                label="🥇 S Tier",
                description="These are the ultimate queens. They’re perfect in every way.",
                value = Rating.S
            ),
            discord.SelectOption(
                label="🥇 A Tier",
                description="Exceptional and lovable, just a hair’s breadth from perfection.",
                value = Rating.A
            ),
            discord.SelectOption(
                label="🥈 B Tier",
                description="Strong contenders. Cute, fun, lovable, maybe even a little underrated.",
                value = Rating.B
            ),
            discord.SelectOption(
                label="🥉 C Tier",
                description="They’re… okay. Maybe you see the appeal, maybe not.",
                value = Rating.C
            ),
            discord.SelectOption(
                label="🪑 D Tier",
                description="These are the waifus that make you squint and ask, “Really?”",
                value = Rating.D
            ),
            discord.SelectOption(
                label="🗑️ F Tier",
                description="Nope. Hard pass. Absolutely not waifu material — not even ironically.",
                value = Rating.F
            )
        ]
    )
    async def select_callback(self, select, interaction):
        for guild in client.guilds:
            for member in guild.members:
                print(f"asdf: {member.id}")
        print(select.guild_id)
        print(select.user.name)
        print(self.mal_id)
        print(interaction.values[0])
        database['Waifu Ratings'].insert_one({
            "user_id": select.user.id, 
            "username": select.user.name, 
            "mal_id": self.mal_id, 
            "rating": int(interaction.values[0])})
        await select.response.send_message("Rating logged!")

@client.tree.command(name="add_waifu_rating", description="Add a rating for a waifu (IF WRONG WAIFU, PUT FULL WAIFU NAME)", guild=GUILD_ID)
async def test(interaction: discord.Interaction, name: str):
    char = search_character(name)   # first result of search
    if len(char) == 0:
        embed = discord.Embed(title = "No results, please check spelling or put full name")
        await interaction.response.send_message(embed=embed)
        return
    character = char[0]     # todo: make search feature better
    view = View()
    view.mal_id = character['mal_id']
    embed = discord.Embed(title = character['name'], url = character['url'], description = character['about'], color = discord.Colour.orange())
    embed.set_thumbnail(url=character['images']['jpg']['image_url'])
    embed.add_field(name="Anime", value=get_characters_anime(character['mal_id']))
    embed.add_field(name="Kanji", value=character['name_kanji'])
    await interaction.response.send_message(embed=embed, view=view)


client.run(token)

