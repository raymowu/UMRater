import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
import requests
from enum import Enum
from pymongo import MongoClient
from pagination import Pagination
import asyncio

load_dotenv()
token = os.getenv('DISCORD_TOKEN')
mongo_uri = os.getenv('MONGODB_URI')
db_name = os.getenv('DB_NAME')

mongodb_client = MongoClient(mongo_uri)
database = mongodb_client[db_name]
rating_db = database['Character Ratings']
print('Connected to MongoDB database!')

# The public Jikan API (api.jikan.moe) shut down on 2026-10-01. Tenrai serves the
# same Jikan v4 schema. Set ANIME_API_BASE_URL to use another Jikan-compatible API,
# e.g. https://jikan.lucashdo.com/v1 (jikan-edge).
ANIME_API_BASE_URL = os.getenv('ANIME_API_BASE_URL', 'https://api.tenrai.org/v1').rstrip('/')
CHARACTERS_URL = f"{ANIME_API_BASE_URL}/characters"
ANIMES_URL = f"{ANIME_API_BASE_URL}/anime"
REQUEST_TIMEOUT = 10  # seconds

class Client(commands.Bot):
    async def on_ready(self):
        print(f'Logged on Discord as {self.user}!')
        try:
            guild = discord.Object(id=368504766889984000)   # test server
            synced = await self.tree.sync()     # guild=guild
            # print(f'Synced {len(synced)} commands to guild {guild.id}')
        except Exception as e:
            print(f'Error syncing commands: {e}')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = Client(command_prefix="!", intents=intents)

# GUILD_ID = discord.Object(id=368504766889984000)

def find_first_index(data, condition):
    """
    Finds the index of the first element in the list that satisfies the condition.

    Args:
        data: The list to search.
        condition: A function that takes an element as input and returns True if the condition is met, False otherwise.

    Returns:
        The index of the first element that satisfies the condition, or -1 if no such element is found.
    """
    for index, element in enumerate(data):
        if condition(element):
            return index
    return -1

# returns of array of each 1-indexed page of each tier
def construct_tiers_indexes(user_ratings):
    if len(user_ratings) == 1:
        return [1]
    tiers_indexes = [1]
    i = 1
    while i < len(user_ratings):
        if user_ratings[i]['rating'] < user_ratings[i - 1]['rating']:
            tiers_indexes.append(i + 1)
        i += 1
    return tiers_indexes

def construct_tiers_indexes_server(server_ratings):
    if len(server_ratings) == 1:
        return [1]
    tiers_indexes = [1]
    i = 1
    while i < len(server_ratings):
        if server_ratings[i]['average_rating'] < server_ratings[i - 1]['average_rating']:
            tiers_indexes.append(i + 1)
        i += 1
    return tiers_indexes

def get_tier_image_url(tier):
    match tier:
        case 10:
            return 'https://i.imgur.com/ZQG5JHA.png'
        case 9:
            return 'https://i.imgur.com/edc4xFQ.png'
        case 8:
            return 'https://i.imgur.com/GqABw1t.png'
        case 6 | 7:
            return 'https://i.imgur.com/hQ54qRQ.png'
        case 5:
            return 'https://i.imgur.com/s1fFhWV.png'
        case 1 | 2 | 3 | 4:
            return 'https://i.imgur.com/UD4mhsm.png'
        case 0:
            return 'https://i.imgur.com/YKZhSks.png'

def get_tier_color(tier):
    match tier:
        case 10:
            return 0x97dcf7
        case 9:
            return 0xf74044
        case 8:
            return 0xf3b755
        case 6 | 7:
            return 0xf3db5e
        case 5:
            return 0xc8f361
        case 1 | 2 | 3 | 4:
            return 0xc9ea7b
        case 0:
            return 0x85877f

def get_characters_anime(id):
    try:
        res = requests.get(f'{CHARACTERS_URL}/{str(id)}/anime', timeout=REQUEST_TIMEOUT)
        data = res.json()
        return data['data'][0]['anime']['title']
    except Exception as e:
        print(f'Could not find anime for char id {id}')

def get_character_by_name(name):
    # No 'limit' param: only the first result is used, and jikan-edge rejects it.
    params = {
        'q' : name,
    }
    res = requests.get(CHARACTERS_URL, params=params, timeout=REQUEST_TIMEOUT)
    res.raise_for_status()
    data = res.json()
    return data['data']

def get_character_by_id(id):
    try:
        res = requests.get(f"{CHARACTERS_URL}/{id}/full", timeout=REQUEST_TIMEOUT)
        data = res.json()
        return data['data']
    except Exception as e:
        print(e)

def search_anime(name):
    params = {
        'limit' : '9',
        'q' : name,
        'order_by' : 'favorites',
        'sort' : 'desc'
    }
    res = requests.get(ANIMES_URL, params=params, timeout=REQUEST_TIMEOUT)
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
                description="All-time favorites. Characters that stick with you long after the story ends.",
                value="10"
            ),
            discord.SelectOption(
                label="🥇 S Tier",
                description="Outstanding characters. Excellent writing, design, and development.",
                value="9"
            ),
            discord.SelectOption(
                label="🥇 A Tier",
                description="Great characters, just short of the very best.",
                value="8"
            ),
            discord.SelectOption(
                label="🥈 B Tier",
                description="Solid and enjoyable. Well-written, maybe a bit underrated.",
                value="6"
            ),
            discord.SelectOption(
                label="🥉 C Tier",
                description="Average. Some appeal, but nothing that stands out.",
                value="5"
            ),
            discord.SelectOption(
                label="🪑 D Tier",
                description="Weak characters. Flat, forgettable, or poorly handled.",
                value="1"
            ),
            discord.SelectOption(
                label="🗑️ F Tier",
                description="The worst of the worst. Nothing redeeming about them.",
                value="0"
            )
        ]
    )
    async def select_callback(self, select, interaction):
        if (rating_db.count_documents({"user_id": select.user.id, "server_id": select.guild.id, "mal_id": self.mal_id}) > 0):
            rating_db.find_one_and_update({
                "user_id": select.user.id, 
                "server_id": select.guild.id,
                "username": select.user.name, 
                "mal_id": self.mal_id}, 
                {'$set' : {"rating": int(interaction.values[0])}})
            await select.response.send_message("Rating updated!")
        else:
            rating_db.insert_one({
                "user_id": select.user.id, 
                "server_id": select.guild.id,
                "username": select.user.name, 
                "mal_id": self.mal_id, 
                "rating": int(interaction.values[0])
                })
            await select.response.send_message("Rating logged!")

@client.tree.command(name="add_character_rating", description="Add a rating for a character (IF WRONG CHARACTER, PUT FULL CHARACTER NAME)")
async def add_character_rating(interaction: discord.Interaction, name: str):
    # Discord requires a response within 3 seconds; the Jikan API can be slower,
    # so acknowledge first and send the real reply as a followup.
    await interaction.response.defer()
    try:
        char = await asyncio.to_thread(get_character_by_name, name)   # first result of search
    except Exception as e:
        print(f'Character search failed for "{name}": {e}')
        await interaction.followup.send("Couldn't reach the anime database right now, please try again in a moment.")
        return
    if len(char) == 0:
        embed = discord.Embed(title = "No results, please check spelling or put full name")
        await interaction.followup.send(embed=embed)
        return
    character = char[0]     # todo: make search feature better
    view = View()
    view.mal_id = character['mal_id']
    about = (character['about'] or '')[:4096]   # embed description limit
    embed = discord.Embed(title = character['name'], url = character['url'], description = about, color = discord.Colour.orange())
    embed.set_thumbnail(url=character['images']['jpg']['image_url'])
    embed.add_field(name="Anime", value=await asyncio.to_thread(get_characters_anime, character['mal_id']))
    embed.add_field(name="Kanji", value=character['name_kanji'])
    await interaction.followup.send(embed=embed, view=view)

@client.tree.command(name="get_user_character_ratings", description="Show a user's character tier list")
async def get_user_character_ratings(interaction: discord.Interaction, username: str):
    await interaction.response.defer()
    user_ratings = list(rating_db.find({"username": username, "server_id": interaction.guild.id}).sort({"rating": -1}))
    if (len(user_ratings) == 0):
        await interaction.followup.send("This user has no character ratings :(")
        return
    tiers_indexes = construct_tiers_indexes(user_ratings)
    async def get_page(page: int):
        index = page - 1
        character = await asyncio.to_thread(get_character_by_id, user_ratings[index]['mal_id'])
        emb = discord.Embed(title=await asyncio.to_thread(get_characters_anime, character['mal_id']), url = character['url'], color = get_tier_color(user_ratings[index]['rating']))
        emb.set_author(name=f"{username}'s Character Tier List", icon_url='https://cdn-1.webcatalog.io/catalog/tiermaker/tiermaker-icon-filled-256.webp?v=1714776171487')
        emb.set_thumbnail(url=get_tier_image_url(user_ratings[index]['rating']))
        emb.set_image(url=character['images']['jpg']['image_url'])
        emb.add_field(name=character['name'], value=character['name_kanji'])
        n = Pagination.compute_total_pages(len(user_ratings), 1)
        return emb, n
    # asyncio.sleep(delay=0)
    await Pagination(interaction, tiers_indexes, get_page).navegate()
    # await interaction.followup.send("test", ephemeral=True)

@client.tree.command(name="get_server_character_ratings", description="Show a server's collective character tier list")
async def get_server_character_ratings(interaction: discord.Interaction):
    await interaction.response.defer()
    server_id = interaction.guild.id
    servername = interaction.guild.name
    server_ratings = list(rating_db.aggregate([
        {"$match": {"server_id": server_id}},
        {"$group": {
            "_id": "$mal_id",
            "count": {"$count": {}},
            "raters": {"$addToSet": "$username"},
            "average_rating": {"$avg": "$rating"}
            }
        },
        {"$project": {
            "mal_id": "$_id",
            "_id": 0,
            "raters": 1,
            "average_rating": 1
        }},
         {"$sort": {"average_rating": -1}}
    ]))
    if (len(server_ratings) == 0):
        await interaction.followup.send("This server has no character ratings :(")
        return
    tiers_indexes = construct_tiers_indexes_server(server_ratings)
    async def get_page(page: int):
        index = page - 1
        character = await asyncio.to_thread(get_character_by_id, server_ratings[index]['mal_id'])
        emb = discord.Embed(title=await asyncio.to_thread(get_characters_anime, character['mal_id']), url = character['url'], color = get_tier_color(round(server_ratings[index]['average_rating'])))
        emb.set_author(name=f"{servername}'s Character Tier List", icon_url='https://cdn-1.webcatalog.io/catalog/tiermaker/tiermaker-icon-filled-256.webp?v=1714776171487')
        emb.set_thumbnail(url=get_tier_image_url(round(server_ratings[index]['average_rating'])))
        emb.set_image(url=character['images']['jpg']['image_url'])
        emb.add_field(name=character['name'], value=character['name_kanji'])
        emb.add_field(name="Server Rating", value=f"{server_ratings[index]['average_rating']}/10", inline=False)
        emb.set_footer(text=f"Raters ({len(server_ratings[index]['raters'])}): {", ".join(server_ratings[index]['raters'])}")
        n = Pagination.compute_total_pages(len(server_ratings), 1)
        return emb, n
    # # asyncio.sleep(delay=0)
    await Pagination(interaction, tiers_indexes, get_page).navegate()
    # await interaction.followup.send("test", ephemeral=True)


@client.tree.command(name = "disconnect", description = "Close connection to the database and disconnect bot")
async def disconnect(interaction: discord.Interaction):
    mongodb_client.close()
    await interaction.response.send_message("Closed the connection to the database! Disconecting from Discord...")
    await client.close()
    quit()


client.run(token)

