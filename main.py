from repo import *
from azeroth_bot import *
import discord
import os
from discord.ext import commands







from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN", "")

intents = discord.Intents.default()
intents.message_content = True

# Create bot instance
bot: AzerothBoth = AzerothBoth(command_prefix="!", intents=intents)

#bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")

@bot.command()
async def hello(ctx: commands.Context):
    await ctx.send("Hello!")



@bot.command(name="equip", aliases=["equipment", "gear"])
async def character_equip(ctx: commands.Context, first_name: str, last_name: str) -> None:
    assert bot.session is not None
    token = await bot.get_valid_blizzard_token()
    equip = await get_character_equipment(bot.session, token, first_name, last_name)

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


@bot.command(name="stats")
async def character_stats(ctx: commands.Context, first_name: str, last_name: str, mode = "effective") -> None:
    is_effective: bool = mode.lower() not in ("base", "raw", "false", "no", "0")

    assert bot.session is not None
    token = await bot.get_valid_blizzard_token()
    data = await get_character_stats(bot.session, token, first_name, last_name, is_effective)

    if not data or "error" in data:
        error_embed = discord.Embed(
            title="Character Stats Error",
            description=data.get("error", "An unexpected error has occurred."),
            color=discord.Color.red()
        )
        await ctx.send(embed=error_embed)
        return

    stat_type = "effective" if is_effective == True else "base"
    embed = discord.Embed(
        title=f"Character {stat_type.capitalize()} Stats",
        description="Results:",
        color=discord.Color.blue()
    )

    embed.add_field(name="**Name: **", value=f"**{data.get("name", "Unknown Name")}**", inline = False)
    embed.add_field(name="Strength", value=data.get("strength", 0), inline=True)
    embed.add_field(name="Agility", value=data.get("agility", 0), inline=True)
    embed.add_field(name="Stamina", value=data.get("stamina", 0), inline=True)
    embed.add_field(name="Intellect", value=data.get("intellect", 0), inline=True)
    embed.add_field(name="Spirit", value=data.get("spirit", 0), inline=True)
    embed.add_field(name="Armor", value=data.get("armor", 0), inline=True)

    embed.set_footer(text="WoW Forever Character Stats")

    await ctx.send(embed=embed)    

@bot.command(name="status")
async def realm_status(ctx: commands.Context, region = "us") -> None:
    region = region.strip().lower()

    assert bot.session is not None
    token = await bot.get_valid_blizzard_token()
    data = await get_realm_status(bot.session, token, region)

    if not data or "error" in data:
        error_embed = discord.Embed(
            title="Realm Status Error",
            description=data['error'],
            color=discord.Color.red()
        )
        await ctx.send(embed=error_embed)
        return


    status_data = data.get("rulesets", [])
    embed = discord.Embed(
        title="Server Status",
        color=discord.Color.blue()
    )

    for s in status_data:
        embed.add_field(name=s.get("name", "Unknown Name"), value=s.get("status", "Unknown Status"), inline=True)

    embed.set_footer(text="WoW Forever Server/Ruleset Status")

    await ctx.send(embed=embed)

@bot.command(name="char", aliases=["character"])
async def character_summary(ctx: commands.Context, first_name: str, last_name: str) -> None:

    
    token = await bot.get_valid_blizzard_token()
    assert bot.session is not None
    summary = await get_character_summary(bot.session, token, first_name, last_name)

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

@bot.command(name="item")
async def item_summary(ctx: commands.Context, item_id: str) -> None:

    assert bot.session is not None
    token = await bot.get_valid_blizzard_token()
    data = await get_item_summary(bot.session, token, item_id)

    if not data or "error" in data:
        error_embed = discord.Embed(
            title="Item Summary Error",
            description=data.get("error", "Unknown error."),
            color=discord.Color.red()
        )
        await ctx.send(embed=error_embed)
        return
    embed = discord.Embed(
        title="Item Summary:",
        color=discord.Color.blue()
    )
    embed.add_field(name="Name", value=data.get("name", "Unknown Name"), inline=True)
    embed.add_field(name="WowHead", value=data.get("wowhead_url", ""), inline=False)
    embed.add_field(name="Level", value=data.get("level",0), inline=True)
    embed.add_field(name="Id", value=data.get("id", 0), inline=True)
    embed.add_field(name="Required Level", value=data.get("req_level", 0), inline=True)
    embed.add_field(name="Item Class", value=data.get("item_class", "Unknown Item Class"), inline=True)
    embed.add_field(name="Item Subclass", value=data.get("item_subclass", "Unknown Item Subclass"), inline=True)
    embed.add_field(name="Vendor Price", value=data.get("purchase_price", 0))
    embed.set_footer(text="WoW Forever Item Summary")

    await ctx.send(embed=embed)

@bot.command(name="creature")
async def creature_summary(ctx: commands.Context, creature_id: str) -> None:
    assert bot.session is not None
    token = await bot.get_valid_blizzard_token()
    data = await get_creature_summary(bot.session, token, creature_id)

    if not data or "error" in data:
        error_embed = discord.Embed(
            title="Creature Summary Error:",
            description=data.get("error", "Unknown error."),
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
    

@bot.command(name="item_search", aliases=["search", "isearch", "is"])
async def item_search(ctx: commands.Context, *, search_query: str) -> None:
    
    assert bot.session is not None
    token = await bot.get_valid_blizzard_token()
    data = await search_items(bot.session, token, search_query)

    if not data or "error" in data:
        error_embed = discord.Embed(
            title="Item Search Error",
            description=data.get("error", "Unknown error."),
            color=discord.Color.red()
        )
        await ctx.send(embed=error_embed)
        return

    # Build embed response
    embed = discord.Embed(
        title="Item Search",
        description="Results:",
        color=discord.Color.blue()
    )
    for r in data.get("results", []):
        embed.add_field(name=r.get("id", 0), value=r.get("name", "Unknown Item"), inline=True)
    embed.set_footer(text="WoW Forever Item Search")

    await ctx.send(embed=embed)
        


@bot.command(name="creature_search", aliases=["csearch", "cs"])
async def creature_search(ctx: commands.Context, *, search_query: str) -> None:
    assert bot.session is not None
    token = await bot.get_valid_blizzard_token()
    data = await search_creatures(bot.session, token, search_query)

    if not data or "error" in data:
        error_embed = discord.Embed(
            title="Creature Search Error",
            description=data.get("error", "Unknown error."),
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
    assert bot.session is not None
    token = await bot.get_valid_blizzard_token()
    specs = await get_character_specs(bot.session, token, first_name, last_name)

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