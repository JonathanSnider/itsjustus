import discord
from discord.ext import commands, tasks
import asyncio
from time import gmtime, strftime
import datetime
from datetime import date
import time
import sqlite3
import json

client = commands.Bot(command_prefix = '!')
# Remove default help command
client.remove_command("help")
extensions = ["schedule_dynamic", "ScheduleListener", "santa"]
ext_len = len(extensions)
current_ext = 0
for cog in extensions:
  try:
    client.load_extension("cogs.{0}".format(cog))
    print("{0} was successfully loaded!".format(cog))
  except Exception as e:
    print("There was an error loading {0}: {1}".format(cog, e))


async def get_message_text(msg_id):
  conn = sqlite3.connect('dbs/schedules.db')
  c = conn.cursor() 

  sql = "SELECT schedule_text FROM schedules WHERE schedule_id = ?"
  c.execute(sql,(msg_id,))
  msg_txt = c.fetchone()

  c.close()
  conn.close()
  if(msg_txt != None):
    return msg_txt[0]
  return msg_txt

async def update_posted_schedules(msg_id, schedule_id):
  conn = sqlite3.connect('dbs/posted_schedules.db')
  c = conn.cursor() 

  sql = "DELETE FROM posted_schedules"
  c.execute(sql)
  conn.commit()
  
  sql = "INSERT INTO posted_schedules VALUES(?,?)"
  c.execute(sql, (msg_id, schedule_id))
  conn.commit()

  c.close()
  conn.close()

async def get_posted_schedule_message(schedule_id):
  conn = sqlite3.connect('dbs/posted_schedules.db')
  c = conn.cursor() 

  sql = "SELECT message_id FROM posted_schedules"
  c.execute(sql)
  posted_schedule_message = c.fetchone()
  if(posted_schedule_message != None):
    posted_schedule_message = posted_schedule_message[0]
  else:
    c.close()
    conn.close()
    return None

  c.close()
  conn.close()
  return posted_schedule_message

async def get_current_schedule_message(schedule_id):
  conn = sqlite3.connect('dbs/schedules.db')
  c = conn.cursor() 

  sql = "SELECT message_id FROM schedules"
  c.execute(sql)
  current_schedule_message = c.fetchone()
  if(current_schedule_message != None):
    current_schedule_message = current_schedule_message[0]
  else:
    c.close()
    conn.close()
    return None

  c.close()
  conn.close()
  return current_schedule_message

@tasks.loop(seconds=60.0)
async def auto_post_schedule():
  current_time = strftime("%H:%M", gmtime())
  current_day = strftime("%A", time.localtime())
  if(current_time == "06:00") and (current_day == "Sunday"):
    conn = sqlite3.connect('dbs/schedules.db')
    c = conn.cursor()

    sql = "SELECT * FROM schedules"
    c.execute(sql)
    first_schedule = c.fetchall()[0]
    
    channel_id = 625399512608800796 # test channel 724077902521696395 weekly-schedule 625399512608800796
    schedule_channel_id = 717868492313067560 # test channel 724077902521696395 weekly-sign-up 717868492313067560
    schedule_id = first_schedule[1]
    msg_txt = await get_message_text(schedule_id)
    if(msg_txt != None):
      msg_txt = msg_txt.split('\n\n\n\n')
      del msg_txt[-1]
      channel_to_send_to = client.get_channel(channel_id)
      current_channel = client.get_channel(schedule_channel_id)
      try:
        old_msg_id = await get_posted_schedule_message(schedule_id)
        old_msg = await channel_to_send_to.fetch_message(int(old_msg_id))
        await old_msg.delete()

        old_schedule_message_id = await get_current_schedule_message(schedule_id)
        old_schedule_message = await current_channel.fetch_message(int(old_schedule_message_id))
        await old_schedule_message.delete()
      except Exception as e:
        print(e)
        await channel_to_send_to.send("There was an error deleting the old schedule.")
      try:
        new_msg = await channel_to_send_to.send(f"New Schedule! @everyone\n\n{msg_txt[0]}")
        await update_posted_schedules(str(new_msg.id), schedule_id)
        c.execute("DELETE FROM schedules WHERE schedule_id = ?", (schedule_id,))
      except Exception as e:
        print(e)
        await channel_to_send_to.send("There was an error posting the new schedule.")
    else:
      await channel_to_send_to.author.send("Not a valid ID")

    conn.commit()
    c.close()
    conn.close()

@client.event
async def on_ready():
  print("Ready!")
  if(not auto_post_schedule.is_running()):
    print("Starting Auto Schedule Posting")
    auto_post_schedule.start()

# Run the bot
with open('tokens.json', 'r') as f:
  tokens = json.load(f)
TOKEN = tokens["bot"]
client.run(TOKEN)