import discord
from discord import IntegrationType
import os
from dotenv import load_dotenv
from openai import OpenAI
import json
import asyncio
import aiohttp

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.dm_messages = True
intents.presences = True
intents.members = True

bot = discord.Bot(intents=intents)
client = OpenAI(api_key=os.getenv("OPENAI_TOKEN"))

message_index = 0
messages = []
generating = False # Prevent multiple generate calls

# Generate The Messages
async def generate_messages(user_id, bio=None, username=None, displayname=None, pronouns=None, tag=None, callback=None):
    global generating
    if generating:
        return
    generating = True
    
    print("Attempting to generate new messages")

    # System prompt, check if personalized or not
    system_prompt = (
        "You are a bot that generates insults."
        "Respond only in JSON, no other text. Keep the proper formatting, no ```json, just straight up json itself. Keep insults in the same key called message."
        "You can capitalize WHOLE WORDS in order to express sarcasm or disrespect. "
        "Occasionally use obscure words."
        "Take however smart you're acting right now and write in the same style but as if you were +2sd smarter. "
        "Use late millenial slang not boomer slang. Mix in zoomer slang occasionally if tonally-inappropriate."
    )
    if bio or username or displayname or pronouns or tag:
        system_prompt += ( 
            "You are given info about the user to personalize messages, have fun with it"
            "If it includes a timestamp, it is in the UNIX timestamp format"
        )
    else:
        system_prompt += (
            "You may OCASSIONALLY use {user_name} for personalized messages, I will convert it to the users username afterwards, like saying something bad about their name or similar. Do it occasionally"
            "Idea: Hey {user_name}, your name sucks more than a vacuum cleaner. But you can be original and make it hit harder."
        )

    # User prompt, check if personalized or not
    if bio or username or displayname or pronouns or tag:
        user_content = (
            "Generate an insult, make it hit REALLY deep, make the insult/message about 300 characters long."
            f"This is info about the user so you can personalize the message - About me/Bio: {bio} | Username: {username} | Display name: {displayname} | Pronouns: {pronouns} | Guild Tag: {tag}"
        )
    else:
        user_content = "Generate an insult, make it hit REALLY deep, make the insult/message about 300 characters long."

    # Send chat request
    response = client.chat.completions.create(
        model="gpt-4.1-mini-2025-04-14",
        messages= [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
    )
    print("Response received successfully")

    #Save Response
    with open(f'{user_id}.json', 'w') as f:
        json.dump(json.loads(response.choices[0].message.content), f, indent=2)

    generating = False
    if callback:
        await callback(user_id)


async def dm_user(user_id):
    global message
    user = await bot.fetch_user(user_id)

    with open(f"{user_id}.json", "r") as response:
        message = json.load(response).get("message", [])
        user_name = user.display_name

        personalized_msg = message.replace("{user_name}", str(user_name)) if "user_name" in message else message

        await user.send(personalized_msg)


async def dm_all_users():
    userFile = "users.json"

    if not os.path.exists(userFile):
        print("No users.json file, doing nothing")
        return

    with open(userFile, 'r') as file:
        try:
            user_ids = json.load(file)
            if not isinstance(user_ids, list):
                print("Users.json corrupted, expected list")
                return
        except json.JSONDecodeError:
            print("Failed to decode users.json")
            return

    for user_id in user_ids:
        insult_file = f"{user_id}.json"
        if not os.path.exists(insult_file):
            print(f"No insult file for {user_id}")
            continue
        
        try:
            with open(insult_file, 'r') as f:
                insult_data = json.load(f)
        except Exception as e:
            print(f"Failed to read insult file for {user_id}: {e}")
            continue
        
        # get discord user object
        user = await bot.fetch_user(user_id)
        if not user:
            print(f"User {user_id} not found")
            continue

        # build the insult message text from the json insult_data
        # assuming insult_data looks like { "messages": ["insult1", "insult2", ...] }
        insults = insult_data.get("messages", [])
        insult_text = "\n".join(insults) if insults else "you suck lol"

        try:
            await user.send(insult_text)
            print(f"Sent insult to {user_id}")
        except Exception as e:
            print(f"Failed to send insult to {user_id}: {e}")

async def getUserData(user_id):
    user_info = await get_all_user_data(os.getenv("USER_TOKEN"), user_id)
    if user_info:
        bio = user_info["bio"]
        username = user_info["username"]
        displayname = user_info["display_name"]
        pronouns = user_info["pronouns"]
        tag = user_info["tag"]
        await generate_messages(user_id, bio, username, displayname, pronouns, tag, callback=dm_user)
    # If user info isn't available, go with basic username personalization
    else:
        await generate_messages(user_id, callback=dm_user)

# Get bio from user using user token // SELF BOTTING HELL YEA
async def get_all_user_data(user_token, target_user_id):
    headers = {
        "Authorization": user_token,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:139.0) Gecko/20100101 Firefox/139.0",
        "X-Super-Properties": "eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiRmlyZWZveCIsImRldmljZSI6IiIsInN5c3RlbV9sb2NhbGUiOiJlbi1VUyIsImJyb3dzZXJfdXNlcl9hZ2VudCI6Ik1vemlsbGEvNS4wIChXaW5kb3dzIE5UIDEwLjA7IFdpbjY0OyB4NjQ7IHJ2OjEzOS4wKSBHZWNrby8yMDEwMDEwMSBGaXJlZm94LzEzOS4wIiwiYnJvd3Nlcl92ZXJzaW9uIjoiMTM5LjAiLCJvc192ZXJzaW9uIjoiMTAiLCJyZWZlcnJlciI6IiIsInJlZmVycmluZ19kb21haW4iOiIiLCJyZWZlcnJlcl9jdXJyZW50IjoiaHR0cHM6Ly9kaXNjb3JkLmNvbS8iLCJyZWZlcnJpbmdfZG9tYWluX2N1cnJlbnQiOiJkaXNjb3JkLmNvbSIsInJlbGVhc2VfY2hhbm5lbCI6InN0YWJsZSIsImNsaWVudF9idWlsZF9udW1iZXIiOjQwNTY4OCwiY2xpZW50X2V2ZW50X3NvdXJjZSI6bnVsbCwiaGFzX2NsaWVudF9tb2RzIjpmYWxzZSwiY2xpZW50X2xhdW5jaF9pZCI6Ijc4YTIxYjQzLTRmY2ItNGYxMS1iMDljLTA1YjllYjA1NDU4ZiIsImNsaWVudF9oZWFydGJlYXRfc2Vzc2lvbl9pZCI6IjU0YzBmYTgzLTM0Y2MtNDI0Mi05NGYzLWI0YzYyNTIzODJjNSIsImNsaWVudF9hcHBfc3RhdGUiOiJmb2N1c2VkIn0="
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        # Check if friends
        async with session.get("https://discord.com/api/v10/users/@me/relationships") as resp:
            if resp.status != 200:
                print("Couldn't fetch relationships")
                return False
            relationships = await resp.json()
            is_friend = any(rel["type"] == 1 and str(rel["id"]) == str(target_user_id) for rel in relationships)

        # Fetch profile
        async with session.get(f"https://discord.com/api/v10/users/{target_user_id}/profile") as profile_resp:
            if profile_resp.status == 403:
                if is_friend:
                    print("403 but shares guild. Probably blocked")
                else:
                    print("Not friends and no shared guilds")
                return False
            elif profile_resp.status != 200:
                print(f"Unexpected status {profile_resp.status}")
                return None

            data = await profile_resp.json()
            user = data.get("user", {})
            profile = data.get("user_profile", {})

            # Grab user info
            bio = user.get("bio", None)
            username = user.get("username", None)
            displayname = user.get("global_name", None)
            pronouns = profile.get("pronouns", None)
            # User activity, returns a list of dicts
            guild = user.get("primary_guild", {})
            tag = guild.get("tag", "")

            return {
                "bio": bio,
                "username": username,
                "display_name": displayname,
                "pronouns": pronouns,
                "tag": tag
            }


@bot.slash_command(description="Opt Into Getting Insulted Every Hour",contexts={discord.InteractionContextType.private_channel,discord.InteractionContextType.guild,discord.InteractionContextType.bot_dm},integration_types={discord.IntegrationType.user_install,discord.IntegrationType.guild_install})
async def insult(ctx):
    new_user_name = ctx.user.name
    new_user_id = ctx.user.id

    userFile = "users.json"

    if os.path.exists(userFile):
        with open(userFile, 'r') as file:
            try:
                data = json.load(file)
                if not isinstance(data, list):
                    print("file data not a list, resetting")
                    data = []
            except json.JSONDecodeError:
                print("json decoding error, resetting")
                data = []
    else:
        print("file not found, creating new list")
        data = []

    if new_user_id not in data:
        print(f"{new_user_id}|{new_user_name} not in data, appending")
        await ctx.respond(f"You have been added to the list.", ephemeral=True)
        data.append(new_user_id)
        
        with open(userFile, 'w') as file:
            json.dump(data, file, indent=2)
        print("file saved")
    else:
        print(f"{new_user_id}|{new_user_name} already in list")
        await ctx.respond("Already in list, if you wish to opt out, use /imhurt.", ephemeral=True)

@bot.slash_command(description="Opt Out Of Getting Insulted Every Hour... Weak...",contexts={discord.InteractionContextType.private_channel,discord.InteractionContextType.guild,discord.InteractionContextType.bot_dm},integration_types={discord.IntegrationType.user_install,discord.IntegrationType.guild_install})
async def imhurt(ctx):
    userFile = "users.json"
    user_id_remove = ctx.user.id
    user_name_remove = ctx.user.name

    if os.path.exists(userFile):
        with open(userFile, 'r') as file:
            try:
                data = json.load(file)
                if not isinstance(data, list):
                    print("file data not a list, resetting")
                    data = []
            except json.JSONDecodeError:
                print("json decoding error, resetting")
                data = []
    else:
        print("File not found, nothing to remove")
        return

    if user_id_remove in data:
        data.remove(user_id_remove)
        print(f"{user_id_remove}|{user_name_remove} removed")
        await ctx.respond("You have been removed from the list", ephemeral=True)
    else:
        print(f"{user_id_remove}|{user_name_remove} not found")
        await ctx.respond("You are not in the list", ephemeral=True)

    with open(userFile, 'w') as file:
        json.dump(data, file, indent=2)

@bot.event
async def on_ready():
    print(f"{bot.user.name} is online.")
        
    userFile = "users.json"

    if not os.path.exists(userFile):
        print("No users.json file, doing nothing")
        return

    with open(userFile, 'r') as file:
        try:
            user_ids = json.load(file)
            if not isinstance(user_ids, list):
                print("Users.json corrupted, expected list")
                return
        except json.JSONDecodeError:
            print("Failed to decode users.json")
            return
        
        for user_id in user_ids:
            await getUserData(user_id)



bot.run(os.getenv("BOT_TOKEN"))