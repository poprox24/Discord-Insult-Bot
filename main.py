import discord
import os
from dotenv import load_dotenv
from openai import OpenAI
import json
import threading

load_dotenv()
bot = discord.Bot()

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
                    "You are a bot that generates insults and reminders to drink water. "
                    "Respond only in JSON, no other text. Keep the proper formatting, no ```json, just straight up json itself. Keep insults and water in the same key called messages."
                    "You can capitalize WHOLE WORDS in order to express sarcasm or disrespect. "
                    "Occasionally use obscure words."
                    "Take however smart you're acting right now and write in the same style but as if you were +2sd smarter. "
                    "Use late millenial slang not boomer slang. Mix in zoomer slang occasionally if tonally-inappropriate."
                )
            },
            {
                "role": "user",
                "content": "Generate a list of 5 insults, make them hit deep, occasionally generate messages reminding user to drink water"
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

    insult()


def insult():
    global message_index, messages

    if message_index >= len(messages):
        message_index = 0
        generate_messages(callback=load_messages)
        return

    if not messages:
        generate_messages(callback=load_messages)
        return
    
    msg = messages[message_index]
    print(f"{message_index + 1}. {msg}")

    message_index += 1

    threading.Timer(5.0, insult).start()

@bot.event
async def on_ready():
    print(f"{bot.user} is online.")
    
    try:
        load_messages()
    except Exception as e:
        print("Error on ready:", e)
        generate_messages(callback=load_messages)

print("testing insult function")
bot.run(os.getenv("BOT_TOKEN"))