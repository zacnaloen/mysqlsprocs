import discord
from discord.ext import commands
import asyncio
import datetime

intents = discord.Intents.default()
intents.guild_scheduled_events = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Replace with your guild ID, channel ID, and the Event Reminder role ID
your_guild_id = 123456789
your_channel_id = 987654321
event_reminder_role_id = 1122334455

# Dictionary to store event details and their reminder tasks
scheduled_events = {}

async def send_reminder(event):
    """
    Send a reminder for the event.
    """
    channel = bot.get_channel(your_channel_id)
    role_mention = f"<@&{event_reminder_role_id}>"
    await channel.send(f"Reminder: The event '{event.name}' is starting soon! {role_mention}")

async def schedule_reminder(event):
    """
    Schedule a reminder for the event.
    """
    event_id = event.id
    event_start = event.scheduled_start_time
    reminder_time = event_start - datetime.timedelta(minutes=15)
    current_time = datetime.datetime.utcnow()

    if reminder_time > current_time:
        delay = (reminder_time - current_time).total_seconds()
        task = bot.loop.create_task(send_reminder_after_delay(event_id, delay))
        # Store the task with the event
        scheduled_events[event_id] = (event, task)

async def send_reminder_after_delay(event_id, delay):
    """
    Wait for the specified delay and then send a reminder for the event.
    """
    await asyncio.sleep(delay)
    event, _ = scheduled_events.get(event_id, (None, None))
    if event:
        await send_reminder(event)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    await retrieve_and_schedule_events()

async def retrieve_and_schedule_events():
    guild = bot.get_guild(your_guild_id)
    events = await guild.fetch_scheduled_events()
    for event in events:
        await schedule_reminder(event)

@bot.event
async def on_scheduled_event_create(event):
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

bot.run('MTE3NDMxOTAzNDcwODI3OTMzNg.GZA8Jc.hjURDpo1XMSL-0vwBSuKPx1bHNttWnaDNR18W4')
