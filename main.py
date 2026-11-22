from pydoc import text

import discord
from utils import WOW_CLASS_COLORS
from repo import get_character_equipment, get_character_specs, get_creature_summary, get_valid_blizzard_token, get_character_summary, search_creatures
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


# @bot.command(name="spec")
# async def character_spec(ctx: commands.Context, first_name: str, last_name: str) -> None:
#     async with aiohttp.ClientSession() as session:
#         token = await get_valid_blizzard_token(session, _TOKEN_CACHE)
#         spec = await get_character_specs(session, token, first_name, last_name)

#         if not spec or len(spec) == 0:
#             error_embed = discord.Embed(
#                 title="Specializations Not Found",
#                 description="WoW API Error",
#                 color=discord.Color.red()
#             )
#             await ctx.send(embed=error_embed)
#             return

#         embed = discord.Embed(
#             title="Specialization:",
#             description=f"**{spec[0]}**",
#             color=discord.Color.blue()
#         )

#         spec = spec[1:]

        


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
async def character_summary(ctx: commands.Context, first_name: str, last_name: str) -> None:
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

@bot.command(name="creature")
async def creature_summary(ctx: commands.Context, creature_id: str) -> None:
    async with aiohttp.ClientSession() as session:
        token = await get_valid_blizzard_token(session, _TOKEN_CACHE)
        data = await get_creature_summary(session, token, creature_id)

    if not data or "error" in data:
        error_embed = discord.Embed(
            title="Creature Summary Error:",
            description=data.get("error", "Unknown error"),
            color=discord.Color.red()
        )
        await ctx.send(embed=error_embed)
        return

    embed = discord.Embed(
        title="Creature Summary:",
        color=discord.Color.blue()
    )

    embed.add_field(name="Name", value=data.get("name", "Unknown Name"), inline=True)
    embed.add_field(name="WowHead Link", value=data.get("wowhead_url",""), inline=False)
    embed.add_field(name="Type", value=data.get("type", "Unknown Type"), inline=True)
    embed.add_field(name="Family", value=data.get("family", "Unknown Family"), inline=True)
    embed.add_field(name="Tameable?", value=data.get("tameable", "Unknown"), inline=True)

    embed.set_footer(text="WoW Forever Creature Summary")

    await ctx.send(embed=embed)
    



@bot.command(name="csearch")
async def creature_search(ctx: commands.Context, *, search_query: str) -> None:
    async with aiohttp.ClientSession() as session:
        token = await get_valid_blizzard_token(session, _TOKEN_CACHE)
        data = await search_creatures(session, token, search_query)

    if not data or "error" in data:
        error_embed = discord.Embed(
            title="Creature Search Results:",
            description=data.get("error", "Unknown error"),
            color=discord.Color.red()
        )
        await ctx.send(embed=error_embed)
        return

    embed = discord.Embed(
        title="Creature Search Results:",
        description="Search WoW Forever Creatures",
        color=discord.Color.blue()
    )

    for r in data.get("results", []):
        embed.add_field(name=r.get("id", 0), value=r.get("name", "Unknown Creature"), inline=True)

    embed.set_footer(text=f"WoW Forever Creature Search")

    await ctx.send(embed=embed)
        
    

@bot.command(name="specs", aliases=["spec", "talents"])
async def character_specs(ctx: commands.Context, first_name: str, last_name: str) -> None:
    async with aiohttp.ClientSession() as session:
        token = await get_valid_blizzard_token(session, _TOKEN_CACHE)
        specs = await get_character_specs(session, token, first_name, last_name)

    if not specs or "error" in specs:
        error_embed = discord.Embed(
            title="Specializations Not Found",
            description=specs.get("error", "Unknown error"),
            color=discord.Color.red(),
        )
        await ctx.send(embed=error_embed)
        return

    embed = discord.Embed(
        title="Specializations:",
        description=f"**{specs['character']}**",
        color=discord.Color.blue(),
    )

    trees: list[dict] = specs.get("trees", [])
    for tree_data in trees:
        tree_name: str = tree_data.get("tree", "Unknown Tree")
        talents: list[dict[str, str | int]] = tree_data.get("talents", [])

        total_points: int = sum(int(t.get("rank", 0)) for t in talents)
        talent_lines: list[str] = [
            f"• {t.get('name', 'Unknown')} ({t.get('rank', 0)})"
            for t in talents
        ]

        field_value: str = "\n".join(talent_lines) if talent_lines else "No points spent"
        # Discord caps individual embed field values at 1024 characters
        if len(field_value) > 1024:
            field_value = field_value[:1021] + "..."

        embed.add_field(
            name=f"{tree_name} ({total_points})",
            value=field_value,
            inline=True,
        )

    embed.set_footer(text=f"WoW {specs['version'].capitalize()} Specialization Summary")

    await ctx.send(embed=embed)




bot.run(TOKEN)