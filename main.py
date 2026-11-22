import discord
from utils import WOW_CLASS_COLORS
from repo import get_character_equipment, get_valid_blizzard_token, get_character_summary
import aiohttp
import os
from discord.ext import commands



_TOKEN_CACHE: dict[str, str | float] = {
    "access_token": "",
    "expires_at": 0.0,
}



from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN", "")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")

@bot.command()
async def hello(ctx: commands.Context):
    await ctx.send("Hello!")


@bot.command(name="equip")
async def character_equip(ctx: commands.Context, first_name: str, last_name: str) -> None:
    async with aiohttp.ClientSession() as session:
        token = await get_valid_blizzard_token(session, _TOKEN_CACHE)
        equip = await get_character_equipment(session, token, first_name, last_name)

    if not equip or "error" in equip:
        error_embed = discord.Embed(
            title="Equipment Not Found",
            description=equip.get("error"),
            color=discord.Color.red()
        )
        await ctx.send(embed=error_embed)
        return


    embed = discord.Embed(
        title=f"Equipment:",
        description=f"**{first_name.lower().capitalize()} {last_name.lower().capitalize()}**",
        color=discord.Color.blue()
    )

    for piece in equip["equipment"]:
        embed.add_field(name=piece.get("slot"), value=piece.get("name"), inline=True)

    embed.set_footer(text=f"WoW: {equip['version'].capitalize()} Equipment Summary")

    await ctx.send(embed=embed)

    

@bot.command(name="char")
async def character_summary2(ctx: commands.Context, first_name: str, last_name: str) -> None:
    async with aiohttp.ClientSession() as session:
        token = await get_valid_blizzard_token(session, _TOKEN_CACHE)
        summary = await get_character_summary(session, token, first_name, last_name)

    if "error" in summary:
        error_embed = discord.Embed(
            title="Character Not Found",
            description=summary["error"],
            color=discord.Color.red(),
        )
        await ctx.send(embed=error_embed)
        return
    
    char_class: str = summary["class"]
    embed_color = WOW_CLASS_COLORS.get(char_class, 0x5865F2)

    raw_guild: str = summary['guild']
    guild_display: str = raw_guild.replace(" | Guild: ", "") if raw_guild else "None"

    embed = discord.Embed(
        title=f"{summary['first_name']} {summary['last_name']}:",
        description=f"Level **{summary['level']}** {summary['race']} {char_class}",
        color=embed_color
    )

    embed.add_field(name="Item Level", value=str(summary['ilvl']), inline=True)
    embed.add_field(name="XP Progress", value=f"{summary['xp_progress_pct']}%", inline=True)
    embed.add_field(name="Faction", value=summary['faction'], inline=True)
    embed.add_field(name="Ruleset", value=summary['ruleset'], inline=True)
    embed.add_field(name="Guild", value=guild_display, inline=True)

    embed.set_footer(text=f"WoW: {summary['version'].capitalize()} Character Summary")

    await ctx.send(embed=embed)




bot.run(TOKEN)