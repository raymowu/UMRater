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
rating_db = database['Waifu Ratings']
print('Connected to MongoDB database!')

CHARACTERS_URL = "https://api.jikan.moe/v4/characters"
ANIMES_URL = "https://api.jikan.moe/v4/anime"

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
        res = requests.get(f'{CHARACTERS_URL}/{str(id)}/anime')
        data = res.json()
        return data['data'][0]['anime']['title']
    except Exception as e:
        print(f'Could not find anime for char id {id}')

def get_character_by_name(name):
    params = {
        'limit' : '9',
        'q' : name,
    }
    res = requests.get(CHARACTERS_URL, params=params)
    data = res.json()
    return data['data']

def get_character_by_id(id):
    try:
        res = requests.get(f"{CHARACTERS_URL}/{id}/full")
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
                value = "10"
            ),
            discord.SelectOption(
                label="🥇 S Tier",
                description="These are the ultimate queens. They’re perfect in every way.",
                value = "9"
            ),
            discord.SelectOption(
                label="🥇 A Tier",
                description="Exceptional and lovable, just a hair’s breadth from perfection.",
                value = "8"
            ),
            discord.SelectOption(
                label="🥈 B Tier",
                description="Strong contenders. Cute, fun, lovable, maybe even a little underrated.",
                value = "6"
            ),
            discord.SelectOption(
                label="🥉 C Tier",
                description="They’re… okay. Maybe you see the appeal, maybe not.",
                value = "5"
            ),
            discord.SelectOption(
                label="🪑 D Tier",
                description="These are the waifus that make you squint and ask, “Really?”",
                value = "1"
            ),
            discord.SelectOption(
                label="🗑️ F Tier",
                description="Nope. Hard pass. Absolutely not waifu material — not even ironically.",
                value = "0"
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

@client.tree.command(name="add_waifu_rating", description="Add a rating for a waifu (IF WRONG WAIFU, PUT FULL WAIFU NAME)")
async def add_waifu_rating(interaction: discord.Interaction, name: str):
    char = get_character_by_name(name)   # first result of search
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

@client.tree.command(name="get_user_waifu_ratings", description="Show a user's waifu tier list")
async def get_user_waifu_ratings(interaction: discord.Interaction, username: str):
    # await interaction.response.defer()
    user_ratings = list(rating_db.find({"username": username, "server_id": interaction.guild.id}).sort({"rating": -1}))
    if (len(user_ratings) == 0):
        await interaction.response.send_message("This user has no waifu ratings :(")
        return
    tiers_indexes = construct_tiers_indexes(user_ratings)
    async def get_page(page: int):
        index = page - 1
        character = get_character_by_id(user_ratings[index]['mal_id'])
        emb = discord.Embed(title=get_characters_anime(character['mal_id']), url = character['url'], color = get_tier_color(user_ratings[index]['rating']))
        emb.set_author(name=f"{username}'s Waifu Tier List", icon_url='https://cdn-1.webcatalog.io/catalog/tiermaker/tiermaker-icon-filled-256.webp?v=1714776171487')
        emb.set_thumbnail(url=get_tier_image_url(user_ratings[index]['rating']))
        emb.set_image(url=character['images']['jpg']['image_url'])
        emb.add_field(name=character['name'], value=character['name_kanji'])
        n = Pagination.compute_total_pages(len(user_ratings), 1)
        return emb, n
    # asyncio.sleep(delay=0)
    await Pagination(interaction, tiers_indexes, get_page).navegate()
    # await interaction.followup.send("test", ephemeral=True)

@client.tree.command(name="get_server_waifu_ratings", description="Show a server's collective waifu tier list")
async def get_server_waifu_ratings(interaction: discord.Interaction):
    # await interaction.response.defer()
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
        await interaction.response.send_message("This server has no waifu ratings :(")
        return
    tiers_indexes = construct_tiers_indexes_server(server_ratings)
    async def get_page(page: int):
        index = page - 1
        character = get_character_by_id(server_ratings[index]['mal_id'])
        emb = discord.Embed(title=get_characters_anime(character['mal_id']), url = character['url'], color = get_tier_color(round(server_ratings[index]['average_rating'])))
        emb.set_author(name=f"{servername}'s Waifu Tier List", icon_url='https://cdn-1.webcatalog.io/catalog/tiermaker/tiermaker-icon-filled-256.webp?v=1714776171487')
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

