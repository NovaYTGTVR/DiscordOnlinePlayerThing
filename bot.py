import os
import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
PLAYFAB_TITLE_ID = os.getenv("PLAYFAB_TITLE_ID")
PLAYFAB_SECRET_KEY = os.getenv("PLAYFAB_SECRET_KEY")
PLAYFAB_SEGMENT_ID = os.getenv("PLAYFAB_SEGMENT_ID")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")


async def get_playfab_player_count() -> int | None:
    """Calls PlayFab Admin/GetSegmentPlayerCount and returns the count."""
    if not all([PLAYFAB_TITLE_ID, PLAYFAB_SECRET_KEY, PLAYFAB_SEGMENT_ID]):
        print("Missing PlayFab config in .env")
        return None

    url = f"https://{PLAYFAB_TITLE_ID}.playfabapi.com/Admin/GetSegmentPlayerCount"
    headers = {
        "X-SecretKey": PLAYFAB_SECRET_KEY,
        "Content-Type": "application/json",
    }
    payload = {"SegmentId": PLAYFAB_SEGMENT_ID}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=10) as resp:
                data = await resp.json()
                if resp.status == 200 and "data" in data:
                    return data["data"].get("ProfilesInSegment", 0)
                print(f"PlayFab error ({resp.status}): {data}")
                return None
    except Exception as e:
        print(f"PlayFab request failed: {e}")
        return None


@bot.tree.command(name="playercounter", description="Show current player count of the game")
async def playercounter(interaction: discord.Interaction):
    await interaction.response.defer()

    # --- PlayFab ---
    playfab_count = await get_playfab_player_count()

    # --- Photon placeholder ---
    # Photon Public Cloud has no public HTTP endpoint for live CCU.
    # To get real numbers you need either:
    #   1. A small always-running monitor client that reports the count, or
    #   2. Photon's paid Counter API (Premium+ plans)
    photon_count = None  # replace later when you have a reporter

    embed = discord.Embed(
        title="🎮 Live Player Counter",
        color=discord.Color.blurple(),
    )

    if playfab_count is not None:
        embed.add_field(
            name="PlayFab (Segment)",
            value=f"**{playfab_count}** players",
            inline=False,
        )
    else:
        embed.add_field(
            name="PlayFab",
            value="Could not fetch (check Title ID / Secret Key / Segment ID in .env)",
            inline=False,
        )

    if photon_count is not None:
        embed.add_field(
            name="Photon",
            value=f"**{photon_count}** players online",
            inline=False,
        )
    else:
        embed.add_field(
            name="Photon",
            value="Not connected yet (needs reporter or paid Counter API)",
            inline=False,
        )

    embed.set_footer(text="Data from PlayFab segment • Photon requires extra setup")
    await interaction.followup.send(embed=embed)


if __name__ == "__main__":
    if not DISCORD_TOKEN or DISCORD_TOKEN == "your_discord_bot_token_here":
        raise ValueError("Please set a real DISCORD_TOKEN in the .env file")
    bot.run(DISCORD_TOKEN)
