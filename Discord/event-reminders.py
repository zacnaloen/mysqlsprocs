import discord
from discord.ext import commands
import asyncio
import datetime
from dotenv import load_dotenv
import os
import json

# Load environment variables from .env file
load_dotenv()

# Retrieve the bot token from environment variables
bot_token = os.getenv('DISCORD_BOT_TOKEN')

intents = discord.Intents.default()
intents.guilds = True
intents.guild_scheduled_events = True
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

config_file = 'bot_config.json'


def load_config():
    try:
        with open(config_file, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


def save_config(config):
    with open(config_file, 'w') as file:
        json.dump(config, file, indent=4)

# Dictionary to store event details and their reminder tasks
scheduled_events = {}


@bot.event
async def on_scheduled_event_create(event):
    await schedule_reminder(event)


async def schedule_reminder(event):
    guild_id = event.guild.id  # Get the guild ID from the event
    event_start = event.start_time  # Corrected attribute name
    reminder_time = event_start - datetime.timedelta(minutes=15)
    current_time = datetime.datetime.utcnow()

    if reminder_time > current_time:
        delay = (reminder_time - current_time).total_seconds()
        task = bot.loop.create_task(send_reminder_after_delay(guild_id, event.id, delay))
        # Store the task with the event
        scheduled_events[event.id] = (event, task)


async def retrieve_and_schedule_events(guild):
    events = await guild.fetch_scheduled_events()
    for event in events:
        await schedule_reminder(event)


async def send_reminder(guild_id, event):
    config = load_config()
    guild_config = config.get(str(guild_id), {})
    channel_id = guild_config.get('channel_id')
    role_id = guild_config.get('role_id')

    if channel_id and role_id:
        channel = bot.get_channel(channel_id)
        role_mention = f"<@&{role_id}>"
        await channel.send(f"Reminder: The event '{event.name}' is starting soon! {role_mention}")


async def send_reminder_after_delay(guild_id, event_id, delay):
    await asyncio.sleep(delay)
    event, _ = scheduled_events.get(event_id, (None, None))
    if event:
        await send_reminder(guild_id, event)


@bot.command(name='setchannel')
@commands.has_permissions(administrator=True)
async def set_channel(ctx):
    guild_id = str(ctx.guild.id)
    config = load_config()
    config[guild_id] = config.get(guild_id, {})
    config[guild_id]['channel_id'] = ctx.channel.id
    save_config(config)
    await ctx.send(f"Channel set to {ctx.channel.name}")


@bot.command(name='setrole')
@commands.has_permissions(administrator=True)
async def set_role(ctx, role: discord.Role):
    try:
        guild_id = str(ctx.guild.id)
        config = load_config()
        config[guild_id] = config.get(guild_id, {})
        config[guild_id]['role_id'] = role.id
        save_config(config)
        await ctx.send(f"Role set to {role.name}")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")


@bot.command(name='showconfig')
@commands.has_permissions(administrator=True)
async def show_config(ctx):
    guild_id = str(ctx.guild.id)
    config = load_config()
    guild_config = config.get(guild_id, {})
    message = f"Channel ID: {guild_config.get('channel_id', 'Not Set')}\n"
    message += f"Role ID: {guild_config.get('role_id', 'Not Set')}"
    await ctx.send(message)


async def retrieve_and_schedule_events():
    guild = bot.get_guild(your_guild_id)
    events = await guild.fetch_scheduled_events()
    for event in events:
        await schedule_reminder(event)


@bot.event
async def on_scheduled_event_update(before, after):
    if before.id in scheduled_events:
        _, task = scheduled_events[before.id]
        task.cancel()
    await schedule_reminder(after)


@bot.event
async def on_scheduled_event_delete(event):
    if event.id in scheduled_events:
        _, task = scheduled_events[event.id]
        task.cancel()
        del scheduled_events[event.id]
        # Remove the Event Reminder role from all members after the event
        await remove_event_reminder_role_from_all_members(event)


async def remove_event_reminder_role_from_all_members(event):
    guild = bot.get_guild(your_guild_id)
    role = guild.get_role(event_reminder_role_id)
    for member in guild.members:
        if role in member.roles:
            await member.remove_roles(role)


@bot.event
async def on_scheduled_event_user_add(event, user):
    guild = bot.get_guild(your_guild_id)
    role = guild.get_role(event_reminder_role_id)
    member = guild.get_member(user.id)
    if role not in member.roles:
        await member.add_roles(role)


@bot.event
async def on_scheduled_event_user_remove(event, user):
    guild = bot.get_guild(your_guild_id)
    role = guild.get_role(event_reminder_role_id)
    member = guild.get_member(user.id)
    if role in member.roles:
        await member.remove_roles(role)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send('Command not found.')
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send('You do not have the correct permissions to run this command.')
    else:
        await ctx.send('An error occurred: {}'.format(str(error)))


bot.run(bot_token)
