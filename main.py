from flask import Flask, send_file
from PIL import Image, ImageFilter, ImageFont, ImageDraw
from werkzeug.middleware.proxy_fix import ProxyFix
import requests
import datetime
import math
import io
import os

#TODO: Remove this key
api_key = "YOUR_KEY_HERE"

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)

@app.route("/")
def default():
    return "Hello World!"

@app.route("/image/<username>")
def image(username):
    img = gen_image(username)
    buffer = io.BytesIO()
    img.save(buffer, "PNG")
    buffer.seek(0)

    return send_file(buffer, mimetype="image/png")

def gen_image(username: str):

    #Open the base image
    img = Image.open("data/base.png")
    img = img.filter(ImageFilter.GaussianBlur(7))
    font = ImageFont.truetype("data/font.ttf", 30)
    font_small = ImageFont.truetype("data/font.ttf", 20)
    draw = ImageDraw.Draw(img, "RGBA")

    #Add rounded boxes
    draw.rounded_rectangle((10, 10, img.width - 10, 100), 10, fill=(0, 0, 0, 128))
    draw.rounded_rectangle((10, 110, 945, img.height - 10), 10, fill=(0, 0, 0, 128))
    draw.rounded_rectangle((955, 110, img.width - 10, 423), 10, fill=(0, 0, 0, 128))
    draw.rounded_rectangle((955, 433, img.width - 10, 746), 10, fill=(0, 0, 0, 128))
    draw.rounded_rectangle((955, 756, img.width - 10, img.height - 10), 10, fill=(0, 0, 0, 128))

    #Add text
    draw.text((15, 20), "Hypixel Stats", font=font_small, fill="#FFFFFF")

    stats = get_stats(username)
    if stats["success"] == False:
        draw.text((15, 50), "Player not found", font=font, fill="#FF5555")
        return img
    
    guild  = get_guild(stats["player"]["uuid"])
    if guild["success"] == False or guild["guild"] is None:
        guild = None

    name: str = stats["player"]["displayname"]

    spacing = 0

    if "rank" in stats["player"]:
        #TODO: YT, Admin, Mod and other ranks
        pass

    if "newPackageRank" in stats["player"]:
        rank: str = stats["player"]["newPackageRank"]
        
        if "rankPlusColor" in stats["player"]:
            plus: str = hypixel_color(stats["player"]["rankPlusColor"])
        else:
            plus = "#FF5555"

        match (rank.upper()):
            case "MVP_PLUS": 
                if not "monthlyPackageRank" in stats["player"] or stats["player"]["monthlyPackageRank"] == "NONE":
                    draw.text((15, 50), "[MVP", font=font, fill="#55FFFF")
                    draw.text((15 + font.getlength("[MVP"), 50), "+", font=font, fill=plus)
                    draw.text((15 + font.getlength("[MVP+"), 50), "] " + name, font=font, fill="#55FFFF")
                    spacing = 15 + font.getlength("[MVP+] " + name)
                else:
                    draw.text((15, 50), "[MVP", font=font, fill="#55FFFF")
                    draw.text((15 + font.getlength("[MVP"), 50), "+", font=font, fill=plus)
                    draw.text((15 + font.getlength("[MVP+"), 50), "++", font=font, fill=plus)
                    draw.text((15 + font.getlength("[MVP++"), 50), "] " + name, font=font, fill="#55FFFF")
                    spacing = 15 + font.getlength("[MVP++] " + name)
            case "MVP":
                draw.text((15, 50), "[MVP] " + name, font=font, fill="#55FFFF")
                spacing = 15 + font.getlength("[MVP] " + name)
            case "VIP_PLUS":
                draw.text((15, 50), "[VIP", font=font, fill="#55FF55")
                draw.text((15 + font.getlength("[VIP"), 50), "+", font=font, fill="#FFAA00")
                draw.text((15 + font.getlength("[VIP+"), 50), "] " + name, font=font, fill="#55FF55")
                spacing = 15 + font.getlength("[VIP+] " + name)
            case "VIP":
                draw.text((15, 50), "[VIP] " + name, font=font, fill="#55FF55")
                spacing = 15 + font.getlength("[VIP] " + name)
            case _:
                draw.text((15, 50), name, font=font, fill="#AAAAAA")
                spacing = 15 + font.getlength(name)
    else:
        draw.text((15, 50), name, font=font, fill="#AAAAAA")
        spacing = 15 + font.getlength(name)

    if guild is not None:
        guild_tag: str = guild["guild"]["tag"]
        guild_color: str = hypixel_color(guild["guild"]["tagColor"])

        draw.text((spacing, 50), " [" + guild_tag + "]", font=font, fill=guild_color)

    network_lvl = nwk_lvl(stats["player"]["networkExp"])
    draw.text((15, 120), "Network Level: ", font=font, fill="white")
    #TODO: Change the color
    draw.text((15 + font.getlength("Network Level: "), 120), str(network_lvl), font=font, fill="white")
    
    if "achievementPoints" in stats["player"]:
        draw.text((15, 185), "Achievement Points: ", font=font, fill="white")
        draw.text((15 + font.getlength("Achievement Points: "), 185), "{:,}".format(stats["player"]["achievementPoints"]), font=font, fill="#55FF55")

    completions = 0
    for sub in stats["player"]["quests"]:
        if "completions" in stats["player"]["quests"][sub]:
            for completion in stats["player"]["quests"][sub]["completions"]:
                completions += 1

    draw.text((15, 220), "Quest Completions: ", font=font, fill="white")
    draw.text((15 + font.getlength("Quest Completions: "), 220), "{:,}".format(completions), font=font, fill="#55FF55")

    challenges = 0
    for num in stats["player"]["challenges"]["all_time"]:
        challenges += stats["player"]["challenges"]["all_time"][num]

    draw.text((15, 255), "Challenges Completed: ", font=font, fill="white")
    draw.text((15 + font.getlength("Challenges Completed: "), 255), "{:,}".format(challenges), font=font, fill="#55FF55")

    if "karma" in stats["player"]:
        draw.text((15, 315), "Karma: ", font=font, fill="white")
        draw.text((15 + font.getlength("Karma: "), 315), "{:,}".format(stats["player"]["karma"]), font=font, fill="#FF55FF")

    if "giftingMeta" in stats["player"] and "ranksGiven" in stats["player"]["giftingMeta"]:
        draw.text((15, 380), "Ranks Gifted: ", font=font, fill="white")
        draw.text((15 + font.getlength("Ranks Gifted: "), 380), "{:,}".format(stats["player"]["giftingMeta"]["ranksGiven"]), font=font, fill="#AA00AA")

    online = get_online_status(stats["player"]["uuid"])
    draw.text((15, 445), "Current Status: ", font=font, fill="white")
    if online["session"] is not None: 
        is_online = online["session"]["online"]
        if is_online:
            draw.text((15 + font.getlength("Current Status: "), 445), "Online", font=font, fill="#55FF55")

            if "gameType" in online["session"]:
                draw.text((15, 485), "In Game: ", font=font, fill="white")
                draw.text((15 + font.getlength("In Game: "), 485), online["session"]["gameType"], font=font, fill="#55FFFF")

                draw.text((15, 520), "Mode: ", font=font, fill="white")
                draw.text((15 + font.getlength("Mode: "), 520), online["session"]["mode"], font=font, fill="#55FFFF")
        else:
            draw.text((15 + font.getlength("Current Status: "), 445), "Offline", font=font, fill="#AAAAAA")

    #TODO: Add more stuff (Guild? Friends? Currently Online status?)

    if "firstLogin" in stats["player"]:
        first_login = datetime.datetime.fromtimestamp(stats["player"]["firstLogin"] / 1000)
        draw.text((15, img.height - 60), "First Login: ", font=font, fill="white")
        draw.text((15 + font.getlength("First Login: "), img.height - 60), first_login.strftime("%Y-%m-%d %H:%M:%S"), font=font, fill="white")

    if "lastLogin" in stats["player"]:
        last_login = datetime.datetime.fromtimestamp(stats["player"]["lastLogin"] / 1000)
        draw.text((15, img.height - 95), "Last Login: ", font=font, fill="white")
        draw.text((15 + font.getlength("Last Login: "), img.height - 95), last_login.strftime("%Y-%m-%d %H:%M:%S"), font=font, fill="white")

    #Bedwars Stats
    draw.text((965, 120), "Bedwars Stats", font=font_small, fill="#FFFFFF")

    if "Bedwars" in stats["player"]["stats"]:
        draw.text((965, 150), "Level: ", font=font, fill="white")
        stars = stars_color(stats["player"]["achievements"]["bedwars_level"])
        offset = 0
        for text in stars:
            draw.text((965 + font.getlength("Level: ") + offset, 150), text[0], font=font, fill=text[1])
            offset += font.getlength(text[0])

        draw.text((965, 185), "Wins: ", font=font, fill="white")
        draw.text((965 + font.getlength("Wins: "), 185), "{:,}".format(stats["player"]["stats"]["Bedwars"]["wins_bedwars"]), font=font, fill="#00AA00")

        draw.text((965, 220), "Losses: ", font=font, fill="white")
        draw.text((965 + font.getlength("Losses: "), 220), "{:,}".format(stats["player"]["stats"]["Bedwars"]["losses_bedwars"]), font=font, fill="#AA0000")

        draw.text((965, 255), "Played: ", font=font, fill="white")
        draw.text((965 + font.getlength("Played: "), 255), "{:,}".format(stats["player"]["stats"]["Bedwars"]["games_played_bedwars"]), font=font, fill="#AAAAAA")

        draw.text((965, 290), "Beds Broken: ", font=font, fill="white")
        draw.text((965 + font.getlength("Beds Broken: "), 290), "{:,}".format(stats["player"]["stats"]["Bedwars"]["beds_broken_bedwars"]), font=font, fill="#55FFFF")

        draw.text((965, 325), "Final Kills: ", font=font, fill="white")
        draw.text((965 + font.getlength("Final Kills: "), 325), "{:,}".format(stats["player"]["stats"]["Bedwars"]["final_kills_bedwars"]), font=font, fill="#FFAA00")

    #Skywars Stats
    draw.text((965, 450), "Skywars Stats", font=font_small, fill="#FFFFFF")

    if "SkyWars" in stats["player"]["stats"]:
        #TODO: Skywars level color (and prestige)
        draw.text((965, 480), "Level: ", font=font, fill="white")
        draw.text((965 + font.getlength("Level: "), 480), stats["player"]["stats"]["SkyWars"]["levelFormatted"][2:], font=font, fill="white")

        draw.text((965, 515), "Wins: ", font=font, fill="white")
        draw.text((965 + font.getlength("Wins: "), 515), "{:,}".format(stats["player"]["stats"]["SkyWars"]["wins"]), font=font, fill="#00AA00")

        draw.text((965, 550), "Losses: ", font=font, fill="white")
        draw.text((965 + font.getlength("Losses: "), 550), "{:,}".format(stats["player"]["stats"]["SkyWars"]["losses"]), font=font, fill="#AA0000")

        draw.text((965, 585), "Played: ", font=font, fill="white")
        draw.text((965 + font.getlength("Played: "), 585), "{:,}".format(stats["player"]["stats"]["SkyWars"]["games"]), font=font, fill="#AAAAAA")

        draw.text((965, 620), "Kills: ", font=font, fill="white")
        draw.text((965 + font.getlength("Kills: "), 620), "{:,}".format(stats["player"]["stats"]["SkyWars"]["kills"]), font=font, fill="#55FFFF")

        draw.text((965, 655), "Deaths: ", font=font, fill="white")
        draw.text((965 + font.getlength("Deaths: "), 655), "{:,}".format(stats["player"]["stats"]["SkyWars"]["deaths"]), font=font, fill="#FFAA00")

        draw.text((965, 690), "Assists: ", font=font, fill="white")
        draw.text((965 + font.getlength("Assists: "), 690), "{:,}".format(stats["player"]["stats"]["SkyWars"]["assists"]), font=font, fill="#FF55FF")

    #TNT Tag Stats
    draw.text((965, 766), "TNT Tag Stats", font=font_small, fill="#FFFFFF")

    if "TNTGames" in stats["player"]["stats"]:
        wins = stats["player"]["stats"]["TNTGames"]["wins_tntag"]
        losses = stats["player"]["stats"]["TNTGames"]["deaths_tntag"]
        played = wins + losses
        kills = stats["player"]["stats"]["TNTGames"]["kills_tntag"]

        draw.text((965, 796), "Wins: ", font=font, fill="white")
        draw.text((965 + font.getlength("Wins: "), 796), "{:,}".format(wins), font=font, fill="#00AA00")

        draw.text((965, 831), "Losses: ", font=font, fill="white")
        draw.text((965 + font.getlength("Losses: "), 831), "{:,}".format(losses), font=font, fill="#AA0000")

        draw.text((965, 866), "Played: ", font=font, fill="white")
        draw.text((965 + font.getlength("Played: "), 866), "{:,}".format(played), font=font, fill="#AAAAAA")

        draw.text((965, 901), "Kills: ", font=font, fill="white")
        draw.text((965 + font.getlength("Kills: "), 901), "{:,}".format(kills), font=font, fill="#55FFFF")

    skin = get_skin_render(stats["player"]["uuid"])
    img.paste(skin, (img.width - 10 - skin.width, img.height - 20 - skin.height), skin)

    return img 

def get_stats(username: str):
    touuid = "https://api.mojang.com/users/profiles/minecraft/" + username
    uuid = requests.get(touuid).json()["id"]
    url = "https://api.hypixel.net/v2/player?key=" + api_key + "&uuid=" + uuid
    response = requests.get(url)
    data = response.json()
    return data

def get_guild(uuid: str):
    url = "https://api.hypixel.net/v2/guild?key=" + api_key + "&player=" + uuid
    response = requests.get(url)
    data = response.json()
    return data

def get_online_status(uuid: str):
    url = "https://api.hypixel.net/status?key=" + api_key + "&uuid=" + uuid
    response = requests.get(url)
    data = response.json()
    return data

def nwk_lvl(exp):
    base = 10000
    growth = 2500
    reversePqPrefix = -(base - 0.5 * growth) / growth
    reverseConst = reversePqPrefix ** 2
    result = 1 + reversePqPrefix + math.sqrt(reverseConst + (2 / growth) * exp)
    return math.floor(result)

def get_skin_render(uuid: str):
    if os.path.exists("data/cache/" + uuid + ".png"):
        return Image.open("data/cache/" + uuid + ".png")

    #TODO: Full render or head render - Customize the img
    url = "https://starlightskins.lunareclipse.studio/render/ultimate/" + uuid + "/full?cameraPosition={\"x\":\"-16.04\",\"y\":\"16.57\",\"z\":\"-27.5\"}&cameraFocalPoint={\"x\":\"0.31\",\"y\":\"18.09\",\"z\":\"1.32\"}"
    #Save the image to a cache
    response = requests.get(url)
    img = Image.open(io.BytesIO(response.content))
    img.save("data/cache/" + uuid + ".png")
    return img

#AHHHHHHHHHHHHHHhh
def stars_color(stars: int):
    if stars < 100: return format_stars(stars, "✫", hypixel_color("GRAY"))
    elif stars < 200: return format_stars(stars, "✫", hypixel_color("WHITE"))
    elif stars < 400: return format_stars(stars, "✫", hypixel_color("AQUA"))
    elif stars < 500: return format_stars(stars, "✫", hypixel_color("DARK_GREEN"))
    elif stars < 300: return format_stars(stars, "✫", hypixel_color("GOLD"))
    elif stars < 600: return format_stars(stars, "✫", hypixel_color("DARK_AQUA"))
    elif stars < 700: return format_stars(stars, "✫", hypixel_color("DARK_RED"))
    elif stars < 800: return format_stars(stars, "✫", hypixel_color("LIGHT_PURPLE"))
    elif stars < 900: return format_stars(stars, "✫", hypixel_color("BLUE"))
    elif stars < 1000: return format_stars(stars, "✫", hypixel_color("DARK_PURPLE"))
    elif stars < 1100: return format_stars(stars, "✫", hypixel_color("RED"), hypixel_color("GOLD"), hypixel_color("YELLOW"), hypixel_color("GREEN"), hypixel_color("AQUA"), hypixel_color("LIGHT_PURPLE"), hypixel_color("DARK_PURPLE"))
    elif stars < 1200: return format_stars(stars, "✪", hypixel_color("GRAY"), hypixel_color("WHITE"), hypixel_color("WHITE"), hypixel_color("WHITE"), hypixel_color("WHITE"), hypixel_color("GRAY"), hypixel_color("GRAY"))
    elif stars < 1300: return format_stars(stars, "✪", hypixel_color("GRAY"), hypixel_color("YELLOW"), hypixel_color("YELLOW"), hypixel_color("YELLOW"), hypixel_color("YELLOW"), hypixel_color("GOLD"), hypixel_color("GRAY"))
    elif stars < 1400: return format_stars(stars, "✪", hypixel_color("GRAY"), hypixel_color("AQUA"), hypixel_color("AQUA"), hypixel_color("AQUA"), hypixel_color("AQUA"), hypixel_color("DARK_AQUA"), hypixel_color("GRAY"))
    elif stars < 1500: return format_stars(stars, "✪", hypixel_color("GRAY"), hypixel_color("GREEN"), hypixel_color("GREEN"), hypixel_color("GREEN"), hypixel_color("GREEN"), hypixel_color("DARK_GREEN"), hypixel_color("GRAY"))
    elif stars < 1600: return format_stars(stars, "✪", hypixel_color("GRAY"), hypixel_color("DARK_AQUA"), hypixel_color("DARK_AQUA"), hypixel_color("DARK_AQUA"), hypixel_color("DARK_AQUA"), hypixel_color("BLUE"), hypixel_color("GRAY"))
    elif stars < 1700: return format_stars(stars, "✪", hypixel_color("GRAY"), hypixel_color("RED"), hypixel_color("RED"), hypixel_color("RED"), hypixel_color("RED"), hypixel_color("DARK_RED"), hypixel_color("GRAY"))
    elif stars < 1800: return format_stars(stars, "✪", hypixel_color("GRAY"), hypixel_color("LIGHT_PURPLE"), hypixel_color("LIGHT_PURPLE"), hypixel_color("LIGHT_PURPLE"), hypixel_color("LIGHT_PURPLE"), hypixel_color("DARK_PURPLE"), hypixel_color("GRAY"))
    elif stars < 1900: return format_stars(stars, "✪", hypixel_color("GRAY"), hypixel_color("BLUE"), hypixel_color("BLUE"), hypixel_color("BLUE"), hypixel_color("BLUE"), hypixel_color("DARK_BLUE"), hypixel_color("GRAY"))
    elif stars < 2000: return format_stars(stars, "✪", hypixel_color("GRAY"), hypixel_color("DARK_PURPLE"), hypixel_color("DARK_PURPLE"), hypixel_color("DARK_PURPLE"), hypixel_color("DARK_PURPLE"), hypixel_color("DARK_GRAY"), hypixel_color("GRAY"))
    elif stars < 2100: return format_stars(stars, "✪", hypixel_color("DARK_GRAY"), hypixel_color("GRAY"), hypixel_color("WHITE"), hypixel_color("WHITE"), hypixel_color("GRAY"), hypixel_color("GRAY"), hypixel_color("DARK_GRAY"))
    elif stars < 2200: return format_stars(stars, "⚝", hypixel_color("WHITE"), hypixel_color("WHITE"), hypixel_color("YELLOW"), hypixel_color("YELLOW"), hypixel_color("GOLD"), hypixel_color("GOLD"), hypixel_color("GOLD"))
    elif stars < 2300: return format_stars(stars, "⚝", hypixel_color("GOLD"), hypixel_color("GOLD"), hypixel_color("WHITE"), hypixel_color("WHITE"), hypixel_color("AQUA"), hypixel_color("DARK_AQUA"), hypixel_color("DARK_AQUA"))
    elif stars < 2400: return format_stars(stars, "⚝", hypixel_color("DARK_PURPLE"), hypixel_color("DARK_PURPLE"), hypixel_color("LIGHT_PURPLE"), hypixel_color("LIGHT_PURPLE"), hypixel_color("GOLD"), hypixel_color("YELLOW"), hypixel_color("YELLOW"))
    elif stars < 2500: return format_stars(stars, "⚝", hypixel_color("AQUA"), hypixel_color("AQUA"), hypixel_color("WHITE"), hypixel_color("WHITE"), hypixel_color("GRAY"), hypixel_color("GRAY"), hypixel_color("DARK_GRAY"))
    elif stars < 2600: return format_stars(stars, "⚝", hypixel_color("WHITE"), hypixel_color("WHITE"), hypixel_color("GREEN"), hypixel_color("GREEN"), hypixel_color("DARK_GRAY"), hypixel_color("DARK_GRAY"), hypixel_color("DARK_GRAY"))
    elif stars < 2700: return format_stars(stars, "⚝", hypixel_color("DARK_RED"), hypixel_color("DARK_RED"), hypixel_color("RED"), hypixel_color("RED"), hypixel_color("LIGHT_PURPLE"), hypixel_color("LIGHT_PURPLE"), hypixel_color("DARK_PURPLE"))
    elif stars < 2800: return format_stars(stars, "⚝", hypixel_color("YELLOW"), hypixel_color("YELLOW"), hypixel_color("WHITE"), hypixel_color("WHITE"), hypixel_color("DARK_GRAY"), hypixel_color("DARK_GRAY"), hypixel_color("DARK_GRAY"))
    elif stars < 2900: return format_stars(stars, "⚝", hypixel_color("GREEN"), hypixel_color("GREEN"), hypixel_color("DARK_GREEN"), hypixel_color("DARK_GREEN"), hypixel_color("GOLD"), hypixel_color("GOLD"), hypixel_color("YELLOW"))
    elif stars < 3000: return format_stars(stars, "⚝", hypixel_color("AQUA"), hypixel_color("AQUA"), hypixel_color("DARK_AQUA"), hypixel_color("DARK_AQUA"), hypixel_color("BLUE"), hypixel_color("BLUE"), hypixel_color("DARK_BLUE"))
    elif stars < 3100: return format_stars(stars, "⚝", hypixel_color("YELLOW"), hypixel_color("YELLOW"), hypixel_color("GOLD"), hypixel_color("GOLD"), hypixel_color("RED"), hypixel_color("RED"), hypixel_color("DARK_RED"))
    elif stars < 3200: return format_stars(stars, "✥", hypixel_color("BLUE"), hypixel_color("BLUE"), hypixel_color("AQUA"), hypixel_color("AQUA"), hypixel_color("GOLD"), hypixel_color("GOLD"), hypixel_color("YELLOW"))
    elif stars < 3300: return format_stars(stars, "✥", hypixel_color("RED"), hypixel_color("DARK_RED"), hypixel_color("GRAY"), hypixel_color("GRAY"), hypixel_color("DARK_RED"), hypixel_color("RED"), hypixel_color("RED"))
    elif stars < 3400: return format_stars(stars, "✥", hypixel_color("BLUE"), hypixel_color("BLUE"), hypixel_color("BLUE"), hypixel_color("LIGHT_PURPLE"), hypixel_color("RED"), hypixel_color("RED"), hypixel_color("DARK_RED"))
    elif stars < 3500: return format_stars(stars, "✥", hypixel_color("DARK_GREEN"), hypixel_color("GREEN"), hypixel_color("LIGHT_PURPLE"), hypixel_color("LIGHT_PURPLE"), hypixel_color("DARK_PURPLE"), hypixel_color("DARK_PURPLE"), hypixel_color("DARK_GREEN"))
    elif stars < 3600: return format_stars(stars, "✥", hypixel_color("RED"), hypixel_color("RED"), hypixel_color("DARK_RED"), hypixel_color("DARK_RED"), hypixel_color("DARK_GREEN"), hypixel_color("GREEN"), hypixel_color("GREEN"))
    elif stars < 3700: return format_stars(stars, "✥", hypixel_color("GREEN"), hypixel_color("GREEN"), hypixel_color("GREEN"), hypixel_color("AQUA"), hypixel_color("BLUE"), hypixel_color("BLUE"), hypixel_color("DARK_BLUE"))
    elif stars < 3800: return format_stars(stars, "✥", hypixel_color("DARK_RED"), hypixel_color("DARK_RED"), hypixel_color("RED"), hypixel_color("RED"), hypixel_color("AQUA"), hypixel_color("DARK_AQUA"), hypixel_color("DARK_AQUA"))
    elif stars < 3900: return format_stars(stars, "✥", hypixel_color("DARK_BLUE"), hypixel_color("DARK_BLUE"), hypixel_color("BLUE"), hypixel_color("DARK_PURPLE"), hypixel_color("DARK_PURPLE"), hypixel_color("LIGHT_PURPLE"), hypixel_color("DARK_BLUE"))
    elif stars < 4000: return format_stars(stars, "✥", hypixel_color("RED"), hypixel_color("RED"), hypixel_color("GREEN"), hypixel_color("GREEN"), hypixel_color("AQUA"), hypixel_color("BLUE"), hypixel_color("BLUE"))
    elif stars < 4100: return format_stars(stars, "✥", hypixel_color("DARK_PURPLE"), hypixel_color("DARK_PURPLE"), hypixel_color("RED"), hypixel_color("RED"), hypixel_color("GOLD"), hypixel_color("GOLD"), hypixel_color("YELLOW"))
    elif stars < 4200: return format_stars(stars, "✥", hypixel_color("YELLOW"), hypixel_color("YELLOW"), hypixel_color("GOLD"), hypixel_color("RED"), hypixel_color("LIGHT_PURPLE"), hypixel_color("LIGHT_PURPLE"), hypixel_color("DARK_PURPLE"))
    elif stars < 4300: return format_stars(stars, "✥", hypixel_color("DARK_BLUE"), hypixel_color("BLUE"), hypixel_color("DARK_AQUA"), hypixel_color("AQUA"), hypixel_color("WHITE"), hypixel_color("GRAY"), hypixel_color("GRAY"))
    elif stars < 4400: return format_stars(stars, "✥", hypixel_color("BLACK"), hypixel_color("DARK_PURPLE"), hypixel_color("DARK_GRAY"), hypixel_color("DARK_GRAY"), hypixel_color("DARK_PURPLE"), hypixel_color("DARK_PURPLE"), hypixel_color("BLACK"))
    elif stars < 4500: return format_stars(stars, "✥", hypixel_color("DARK_GREEN"), hypixel_color("DARK_GREEN"), hypixel_color("GREEN"), hypixel_color("YELLOW"), hypixel_color("GOLD"), hypixel_color("DARK_PURPLE"), hypixel_color("LIGHT_PURPLE"))
    elif stars < 4600: return format_stars(stars, "✥", hypixel_color("WHITE"), hypixel_color("WHITE"), hypixel_color("AQUA"), hypixel_color("AQUA"), hypixel_color("DARK_AQUA"), hypixel_color("DARK_AQUA"), hypixel_color("DARK_AQUA"))
    elif stars < 4700: return format_stars(stars, "✥", hypixel_color("DARK_AQUA"), hypixel_color("AQUA"), hypixel_color("YELLOW"), hypixel_color("YELLOW"), hypixel_color("GOLD"), hypixel_color("LIGHT_PURPLE"), hypixel_color("DARK_PURPLE"))
    elif stars < 4800: return format_stars(stars, "✥", hypixel_color("WHITE"), hypixel_color("DARK_RED"), hypixel_color("RED"), hypixel_color("RED"), hypixel_color("BLUE"), hypixel_color("DARK_BLUE"), hypixel_color("BLUE"))
    elif stars < 4900: return format_stars(stars, "✥", hypixel_color("DARK_PURPLE"), hypixel_color("DARK_PURPLE"), hypixel_color("RED"), hypixel_color("GOLD"), hypixel_color("YELLOW"), hypixel_color("AQUA"), hypixel_color("DARK_AQUA"))
    elif stars < 5000: return format_stars(stars, "✥", hypixel_color("DARK_GREEN"), hypixel_color("GREEN"), hypixel_color("WHITE"), hypixel_color("WHITE"), hypixel_color("GREEN"), hypixel_color("GREEN"), hypixel_color("DARK_GREEN"))
    else: return format_stars(stars, "✥", hypixel_color("DARK_RED"), hypixel_color("DARK_RED"), hypixel_color("DARK_PURPLE"), hypixel_color("BLUE"), hypixel_color("BLUE"), hypixel_color("DARK_BLUE"), hypixel_color("BLACK"))

#TODO: Fix
def format_stars(level: int, star: str, *colors):
    level = str(level)
    text_list = []

    if len(colors) == len(level) + 3:
        digits = list(level) 

        #text_list.append(("[", colors[0]))
        for digit in digits:
            text_list.append((digit, colors[digit + 1]))
        #text_list.append((star, colors[-2]))
        #text_list.append(("]", colors[-1]))
    else:
        #text_list.append(("[" + level + star + "]", colors[0] if len(colors) > 0 else "#AAAAAA"))
        text_list.append((level + star, colors[0] if len(colors) > 0 else "#AAAAAA"))
    
    return text_list

def hypixel_color(color: str):
    match (color.upper()):
        case "AQUA": return "#55FFFF"
        case "BLACK": return "#000000"
        case "BLUE": return "#5555FF"
        case "DARK_AQUA": return "#00AAAA"
        case "DARK_BLUE": return "#0000AA"
        case "DARK_GRAY": return "#555555"
        case "DARK_GREEN": return "#00AA00"
        case "DARK_PURPLE": return "#AA00AA"
        case "DARK_RED": return "#AA0000"
        case "GOLD": return "#FFAA00"
        case "GRAY": return "#AAAAAA"
        case "GREEN": return "#55FF55"
        case "LIGHT_PURPLE": return "#FF55FF"
        case "RED": return "#FF5555"
        case "WHITE": return "#FFFFFF"
        case "YELLOW": return "#FFFF55"
        case _: return "#FF5555"

if __name__ == "__main__":
    app.run(debug=True,port=5000)