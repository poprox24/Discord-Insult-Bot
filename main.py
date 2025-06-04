import discord
from discord import IntegrationType
import os
from dotenv import load_dotenv
from openai import OpenAI
import json
import threading
import asyncio

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.dm_messages = True

bot = discord.Bot(intents=intents)
client = OpenAI(api_key=os.getenv("OPENAI_TOKEN"))

message_index = 0
messages = []
generating = False # Prevent multiple generate calls

# Generate The Messages
def generate_messages(callback=None):
    global generating
    if generating:
        return
    generating = True
    
    print("Attempting to generate new messages")
    response = client.chat.completions.create(
        model="gpt-4.1-mini-2025-04-14",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a bot that generates insults."
                    "Respond only in JSON, no other text. Keep the proper formatting, no ```json, just straight up json itself. Keep insults in the same key called messages."
                    "You can capitalize WHOLE WORDS in order to express sarcasm or disrespect. "
                    "Occasionally use obscure words."
                    "Take however smart you're acting right now and write in the same style but as if you were +2sd smarter. "
                    "Use late millenial slang not boomer slang. Mix in zoomer slang occasionally if tonally-inappropriate."
                    "You may OCASSIONALLY use {user_name} for personalized messages, I will convert it to the users username afterwards, like saying something bad about their name or similar. Do it occasionally"
                    "Idea: Hey {user_name}, your name sucks more than a vacuum cleaner. But you can be original and make it hit harder."
                )
            },
            {
                "role": "user",
                "content": "Generate a list of 20 insults, make them hit deep, make the insults/messages about 250 characters long."
            }
        ]
    )
    print("Response received successfully")

    #Save Response
    with open('response.json', 'w') as f:
        json.dump(json.loads(response.choices[0].message.content), f, indent=2)

    generating = False
    if callback:
        callback()


def load_messages():
    global messages
    try:
        with open("response.json", "r") as response:
            data = json.load(response)
            messages = data["messages"]
    except Exception as e:
        print("Failed to load messaged:", e)
        generate_messages(callback=load_messages) # Regenerates messages if the AI responded with something that it doesn't like
        return

    asyncio.get_event_loop().create_task(insult_loop())

async def dm_all_users(msg):
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
        try:
            user = await bot.fetch_user(user_id)
            user_name = user.display_name

            personalized_msg = msg.replace("{user_name}", str(user_name)) if "user_name" in msg else msg

            await user.send(personalized_msg)
            print(f"Dm sent to {user_id}")
        except Exception as e:
            print(f"Failed to dm {user_id}: {e}")


async def insult_loop():
    global message_index, messages

    while True:
        if message_index >= len(messages):
            message_index = 0
            generate_messages(callback=load_messages)
            return

        if not messages:
            generate_messages(callback=load_messages)
            return
        
        msg = messages[message_index]
        print(msg)
        await dm_all_users(msg)

        message_index += 1
        await asyncio.sleep(3600)


@bot.application_command(description="Opt Into Getting Insulted Every Hour",contexts={discord.InteractionContextType.private_channel,discord.InteractionContextType.guild,discord.InteractionContextType.bot_dm},integration_types={discord.IntegrationType.user_install,discord.IntegrationType.guild_install})
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
    
    try:
        load_messages()
    except Exception as e:
        print("Error on ready:", e)
        generate_messages(callback=load_messages)

bot.run(os.getenv("BOT_TOKEN"))