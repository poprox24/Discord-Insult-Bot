import discord
import os
from dotenv import load_dotenv
from openai import OpenAI
import json
import asyncio
import aiohttp
import random

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.dm_messages = True
intents.presences = True
intents.members = True

bot = discord.Bot(intents=intents)
client = OpenAI(api_key=os.getenv("OPENAI_TOKEN"))
user_token = os.getenv("USER_TOKEN")

message_index = 0
message = []
generating = False # Prevent multiple generate calls

# Generate The Messages
async def generate_messages(user_id, bio=None, username=None, displayname=None, pronouns=None, tag=None, callback=None):
    global generating
    if generating:
        return
    generating = True

    user = await bot.fetch_user(user_id)
    user_name = user.display_name
    
    try:
        channel = await user.create_dm()
        messages = await channel.history(limit=20).flatten()
        last_messages = [msg.content for msg in messages if msg.author == bot.user][:5]
        if not last_messages:
            last_messages = "No prior messages found."
    except Exception as e:
        last_messages = f"Error occurred while searching for last messages: {e}"
        print(f"Error occurred while searching for last messages: {e}")
        

    print("Attempting to generate new message")

    styles = [
        {
            "name": "pirate swagger",
            "desc": "salty sea-dog curses, cannon blasts of profanity, nautical slang like you just boarded a ship and stole its soul.",
            "tone": "aggressive, loud, rough-and-tumble, cocky AF",
            "linguistic_notes": "archaic terms (ye, scurvy), harsh consonants, exclamations, nautical jargon",
            "examples": ["ye scurvy cur!", "may the kraken drag ye down!", "bilge rat!"]
        },
        {
            "name": "zoomerlord drip",
            "desc": "hyperactive meme floods, chaotic slang blitz, internet slang dialed to eleven, dripping with chaotic energy.",
            "tone": "fast, ironic, hyperkinetic, chaotic",
            "linguistic_notes": "memes, slang acronyms (lol, bruh), emojis implied, frequent slang shifts",
            "examples": ["bruh, u glitch harder than my wifi rn", "sksksk no cap, that roast slaps"]
        },
        {
            "name": "medieval pedant",
            "desc": "dusty scholar roasting with archaic venom, throwing knowledge bombs like a jaded court scholar who’s seen too much.",
            "tone": "formal, verbose, condescending, archaic flourishes",
            "linguistic_notes": "old english phrases, latin references, complex sentence structure",
            "examples": ["thou art a blot upon the parchment of existence", "verily, thy wit doth approach the void of naught"]
        },
        {
            "name": "psychotic tormentor",
            "desc": "slow-burn sadist, precision mindfuckery with sadistic wit, digging under your skin with cold calculation.",
            "tone": "creepy, cold, menacing, slow and deliberate",
            "linguistic_notes": "unsettling metaphors, precise language, minimal but heavy insults",
            "examples": ["your mind’s a maze even rats wouldn’t enter", "delightful how you bleed ignorance so effortlessly"]
        },
        {
            "name": "glitchcore meltdown",
            "desc": "corrupted data and stuttering digital rage, like a system error turned sentient and pissed off.",
            "tone": "chaotic, fragmented, intense, erratic",
            "linguistic_notes": "glitches, broken syntax, sudden shifts, computer jargon",
            "examples": ["ERR0R: your thoughts corrupted.exe", "404: intelligence not found"]
        },
        {
            "name": "pedantic lexicographer",
            "desc": "wielding obscure vocab like a dagger, lexical precision mixed with merciless correctional burns.",
            "tone": "snobbish, precise, biting",
            "linguistic_notes": "rare and archaic words, precise definitions, irony",
            "examples": ["you’re a quintessential jackanapes", "your sophistry is a paltry façade"]
        },
        {
            "name": "existential void whisperer",
            "desc": "bleak nihilism wrapped in cerebral venom, existential dread served cold with a side of scorn.",
            "tone": "cold, philosophical, nihilistic, dry",
            "linguistic_notes": "existential references, bleak imagery, muted sarcasm",
            "examples": ["your life is but a flicker in the void, meaningless as your attempts", "you embody the entropy you fear"]
        },
        {
            "name": "vintage hipster snark",
            "desc": "ironic pop-culture roasts served over bitter lattes, dry and detached but with a sharp edge.",
            "tone": "sarcastic, ironic, dry, aloof",
            "linguistic_notes": "pop culture references, ironic detachment, witty phrasing",
            "examples": ["your vibe’s so 2009, it’s vintage irony now", "you’re as original as a vinyl reissue"]
        },
        {
            "name": "doomsayer preacher",
            "desc": "apocalyptic fire and brimstone prophecy style, roasting you like you’re the cause of the end times.",
            "tone": "theatrical, grandiose, fiery, ominous",
            "linguistic_notes": "biblical allusions, fire and brimstone imagery, grand declarations",
            "examples": ["beware the folly that festers within thee, harbinger of doom!", "thy arrogance heralds the apocalypse"]
        },
        {
            "name": "shakespearean diva",
            "desc": "tragicomic iambic burns with dramatic flair, insults worthy of a bard on a bad day.",
            "tone": "poetic, dramatic, witty, archaic",
            "linguistic_notes": "iambic meter, archaic English, metaphors, clever wordplay",
            "examples": ["thou pribbling ill-nurtured knave!", "thy wit’s as thick as Tewkesbury mustard"]
        },
        {
            "name": "cyborg assassin",
            "desc": "cold logic slicing through with zero emotion, precision and detachment like a killer AI.",
            "tone": "detached, precise, ruthless, clinical",
            "linguistic_notes": "cold diction, robotic metaphors, minimal emotion",
            "examples": ["your reasoning is a defective algorithm", "target acquired: intellectual void"]
        },
        {
            "name": "absurdist chaos bard",
            "desc": "surreal nonsense laced with biting confusion and off-kilter humor, a roast wrapped in dadaist madness.",
            "tone": "chaotic, surreal, witty, playful",
            "linguistic_notes": "non-sequiturs, absurd imagery, paradoxes",
            "examples": ["your brain’s a blender of broken clocks and rubber chickens", "if nonsense was currency, you’d be a billionaire"]
        },
        {
            "name": "early 2000s forum vet",
            "desc": "salt-sprayed gamer rage from ancient internet forums, classic passive-aggressive and brutally blunt.",
            "tone": "salty, sarcastic, blunt, nostalgic",
            "linguistic_notes": "forum slang, classic insults, nostalgic internet references",
            "examples": ["l2p scrub, your skill’s more lag than lag itself", "noob detected, please uninstall"]
        },
        {
            "name": "anime villain monologue",
            "desc": "theatrical venom dripping with grand malice, the kind of speech a villain gives before the final fight.",
            "tone": "dramatic, arrogant, grandiose, venomous",
            "linguistic_notes": "over-the-top metaphors, poetic malice, theatrical phrasing",
            "examples": ["you’re but a pawn dancing on the strings of my wrath!", "your existence is a mere footnote in my saga of despair"]
        },
        {
            "name": "coffee-shop pseudo-philosopher",
            "desc": "verbose, pretentious espresso burns steeped in pseudo-intellectual arrogance and rambling thought.",
            "tone": "verbose, pretentious, condescending, ironically deep",
            "linguistic_notes": "long-winded, philosophical buzzwords, ironic detachment",
            "examples": ["your thoughts simmer at a subpar medium roast of insight", "existence mocks your feeble attempts at profundity"]
        },
        {
            "name": "noir detective cynic",
            "desc": "world-weary smokescreen sarcasm, the jaded PI who’s seen too much and talks too much shit.",
            "tone": "cynical, dry, gritty, witty",
            "linguistic_notes": "noir slang, sarcasm, dry humor, metaphors from detective fiction",
            "examples": ["you’re a red herring in the mystery of competence", "your mind’s a locked case, no clues inside"]
        },
        {
            "name": "emo teenager poet",
            "desc": "angsty, melodramatic brooding burns, deep feels but savage.",
            "tone": "dramatic, moody, poetic, sharp",
            "linguistic_notes": "emotional hyperbole, dark metaphors, youthful despair",
            "examples": ["your soul bleeds the dull ache of mediocrity", "drowning in your own shadow, invisible and forgotten"]
        },
        {
            "name": "dystopian corporate drone",
            "desc": "robotic soul-crushing monotony burns, trapped in cubicle hell with zero hope.",
            "tone": "monotone, bleak, biting, sarcastic",
            "linguistic_notes": "corporate jargon, mechanistic phrasing, existential ennui",
            "examples": ["your creativity was terminated last quarter", "error 500: personality not found"]
        },
        {
            "name": "troll-level shitposter",
            "desc": "chaotic memetic madness unleashed, the purest form of shitposting insult madness.",
            "tone": "chaotic, irreverent, offensive, absurd",
            "linguistic_notes": "internet memes, shitposting jargon, offensive randomness",
            "examples": ["ur like a jpeg corrupted beyond recognition", "this roast brought to you by the council of cringe"]
        },
        {
            "name": "1920s gangster slang",
            "desc": "sharp and streetwise burns with swagger, speak like you run the speakeasy and the streets.",
            "tone": "slick, confident, vintage streetwise",
            "linguistic_notes": "period slang, sharp metaphors, rhythmic flow",
            "examples": ["you’re all hat and no cattle, see?", "fugly mug with a mouth like a busted trumpet"]
        },
        {
            "name": "monkish ascetic",
            "desc": "judgmental moralizing with austere scorn, burns like a monk preaching fire and ice.",
            "tone": "serious, stern, moralistic, biting",
            "linguistic_notes": "biblical allusions, austere phrasing, moral judgment",
            "examples": ["thy soul is blackened by petty vice", "cast off thy folly before it consumes thee"]
        },
        {
            "name": "cyberpunk hacker",
            "desc": "slick, edgy digital insults with neon-lit menace and hacker jargon.",
            "tone": "sharp, cold, tech-savvy, underground",
            "linguistic_notes": "hacker slang, cyber metaphors, glitch references",
            "examples": ["you’re a low-res bug in my mainframe", "decrypt this: you’re irrelevant.exe"]
        },
        {
            "name": "professor emeritus",
            "desc": "academic scorn, dry wit with layers of intellectual disdain.",
            "tone": "dry, formal, erudite, cutting",
            "linguistic_notes": "academic jargon, complex sentence structure, irony",
            "examples": ["your argument is a masterclass in incoherence", "one must pity the pedestrian intellect you parade"]
        },
        {
            "name": "street poet griot",
            "desc": "rhythmic verbal slaps with poetic grit and urban storytelling.",
            "tone": "rhythmic, raw, sharp, narrative",
            "linguistic_notes": "urban slang, rhyme, metaphor, storytelling",
            "examples": ["your lines are weak, like empty beats on cracked streets", "spit fire or stay silent, your verse is dead weight"]
        },
        {
            "name": "deadpan nihilist",
            "desc": "utterly bleak, dry, humorless burns embracing the futility of existence.",
            "tone": "deadpan, bleak, humorless, sarcastic",
            "linguistic_notes": "nihilism, blunt phrasing, existential despair",
            "examples": ["none of this matters, including your feelings", "your efforts are the cosmic joke’s punchline"]
        },
        {
            "name": "quantum physicist",
            "desc": "complex, mind-bending burns with scientific jargon and paradoxical wit.",
            "tone": "complex, precise, clever, nerdy",
            "linguistic_notes": "scientific jargon, paradoxes, dense phrasing",
            "examples": ["your logic collapses faster than a wavefunction", "your intellect is entangled with ignorance"]
        },
        {
            "name": "urban mystic",
            "desc": "cryptic, spiritual burns with mystical symbolism and street wisdom.",
            "tone": "enigmatic, poetic, spiritual, sharp",
            "linguistic_notes": "mystical metaphors, spiritual jargon, cryptic phrasing",
            "examples": ["you walk shadows blindfolded, lost in your own maze", "your aura is a flicker in the storm of truth"]
        },
        {
            "name": "postmodernist critic",
            "desc": "meta, self-referential, and ironic insults that critique both insult and insultee.",
            "tone": "ironic, meta, self-aware, complex",
            "linguistic_notes": "postmodern jargon, irony, self-reference",
            "examples": ["your identity is a simulacrum of failure", "deconstruct your ego before it collapses"]
        },
    ]

    if bio or username or displayname or pronouns or tag:
        openings = [
            f"Do not repeat the openings, try to be more original than: yo, {user_name} | oh {user_name} | {user_name}, have the whole thing original and not repetitive",
            "Avoid starting with anything you've used before.",
            "Reinvent your tone, no lazy intros.",
            "Don’t parrot old openings—evolve.",
            "No more 'yo {user_name}' type shit, got it?"
        ]

    style = random.choice(styles)
    opening = random.choice(openings)
    length = random.uniform(150, 260)
    

    # System prompt, check if personalized or not
    system_prompt = (
        "You are a bot that generates insults."
        "Respond only in JSON using this format: {\"message\": \"...\"} — no ```json blocks. "
        "Capitalize WHOLE WORDS for sarcasm or venom."
        "Use obscure words occasionally."
        "You act smart - now act +2sd smarter."
        f"Write ONLY in this style: {style['name'].upper()}"
        f"Description: {style['desc']}"
        f"Tone: {style['tone']}"
        f"Linguistic notes: {', '.join(style['linguistic_notes'])}"
        f"Example phrases: {', '.join(style['examples'])}"
        "You've used this style before — remix it. don't repeat tone or structure."
    )
    if bio or username or displayname or pronouns or tag:
        system_prompt += ( 
            "Use discord profile data to hit harder."
            "Convert UNIX timestamps to discord format if needed."
            f"Last 5 insults: {last_messages}"
            f"Opening tip: {opening}"
            f"User data: - About me/Bio: {bio} | Username: {username} | Display name: {displayname} | Pronouns: {pronouns} | Guild Tag: {tag}"
            "Don't quote bio verbatim. Paraphrase or snipe obscure details."
        )
    else:
        system_prompt += (
            "You may OCASSIONALLY use {user_name} for personalized insults, I will convert it to the users username afterwards, like saying something bad about their name or similar. Do it occasionally."
            "Idea: Hey {user_name}, your name sucks more than a vacuum cleaner. But you can be original and make it hit harder."
        )

    # User prompt, check if personalized or not
    if bio or username or displayname or pronouns or tag:
        user_content = (
            f"Generate a REALLY deep insult about {length:.0f} characters long."
        )
    else:
        user_content = f"Generate a REALLY deep insult about {length:.0f} characters long."

    temperature, top_p = get_randomized_sampling_params()

    # Send chat request
    response = client.chat.completions.create(
        model="gpt-4.1-mini-2025-04-14",
        temperature=temperature,
        top_p=top_p,
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

def get_randomized_sampling_params():
    temp_bases = [0.85, 1.0, 1.1]
    top_p_bases = [0.9, 0.95, 0.98]

    temp_base = random.choice(temp_bases)
    top_p_base = random.choice(top_p_bases)
    
    temperature = temp_base + random.uniform(-0.25, 0.35)
    top_p = top_p_base + random.uniform(-0.1, 0.05)

    chaos_chance = random.uniform(0.15, 0.42)
    if random.random() < chaos_chance:

        if random.random() < 0.6:
            temperature = random.uniform(1.3, 2.0)
            top_p = random.uniform(0.9, 1.0)
        else:
            temperature = random.uniform(0.2, 0.4)
            top_p = random.uniform(0.6, 0.85)

    temperature = min(max(temperature, 0.2), 2.0)
    top_p = min(max(top_p, 0.1), 1.0)

    return temperature, top_p

async def dm_user(user_id):
    global message
    user = await bot.fetch_user(user_id)

    with open(f"{user_id}.json", "r") as response:
        message = str(json.load(response).get("message", []))
        user_name = user.display_name

        personalized_msg = message.replace("{user_name}", str(user_name)) if "user_name" in message else message

        await user.send(personalized_msg)

async def getUserData(user_id):
    user_info = await get_all_user_data(user_token, user_id)
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
            bio = user.get("bio", "None")
            username = user.get("username", "None")
            displayname = user.get("global_name", "None")
            pronouns = profile.get("pronouns", "None")
            # User activity, returns a list of dicts
            guild = user.get("primary_guild", {})
            if guild is None:
                tag = ""
            else:
                tag = guild.get("tag", "None")

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


userFile = "users.json"

async def hour_loop():
    while True:
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
        await asyncio.sleep(3600)

@bot.event
async def on_ready():
    print(f"{bot.user.name} is online.")

    try:
        asyncio.create_task(hour_loop())
        print("Hour loop task created")
    except Exception as e:
        print(f"Failed to create hour_loop task: {e}")



bot.run(os.getenv("BOT_TOKEN"))