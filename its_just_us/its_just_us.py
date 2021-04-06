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


async def getMessageText(msgId):
  conn = sqlite3.connect('dbs/schedules.db')
  c = conn.cursor() 

  sql = "SELECT schedule_text FROM schedules WHERE schedule_id = ?"
  c.execute(sql,(msgId,))
  msgTxt = c.fetchone()

  c.close()
  conn.close()
  if(msgTxt != None):
    return msgTxt[0]
  return msgTxt

async def updatePostedSchedules(msgId, scheduleId):
  conn = sqlite3.connect('dbs/posted_schedules.db')
  c = conn.cursor() 

  sql = "DELETE FROM posted_schedules"
  c.execute(sql)
  conn.commit()
  
  sql = "INSERT INTO posted_schedules VALUES(?,?)"
  c.execute(sql, (msgId, scheduleId))
  conn.commit()

  c.close()
  conn.close()

async def getPostedScheduleMessage(scheduleId):
  conn = sqlite3.connect('dbs/posted_schedules.db')
  c = conn.cursor() 

  sql = "SELECT message_id FROM posted_schedules"
  c.execute(sql)
  postedScheduleMessage = c.fetchone()
  if(postedScheduleMessage != None):
    postedScheduleMessage = postedScheduleMessage[0]
  else:
    c.close()
    conn.close()
    return None

  c.close()
  conn.close()
  return postedScheduleMessage

async def getCurrentScheduleMessage(scheduleId):
  conn = sqlite3.connect('dbs/schedules.db')
  c = conn.cursor() 

  sql = "SELECT message_id FROM schedules"
  c.execute(sql)
  currentScheduleMessage = c.fetchone()
  if(currentScheduleMessage != None):
    currentScheduleMessage = currentScheduleMessage[0]
  else:
    c.close()
    conn.close()
    return None

  c.close()
  conn.close()
  return currentScheduleMessage

@tasks.loop(seconds=60.0)
async def autoPostSchedule():
  current_time = strftime("%H:%M", gmtime())
  current_day = strftime("%A", time.localtime())
  if(current_time == "06:00") and (current_day == "Sunday"):
    conn = sqlite3.connect('dbs/schedules.db')
    c = conn.cursor()

    sql = "SELECT * FROM schedules"
    c.execute(sql)
    first_schedule = c.fetchall()[0]
    
    channelId = 625399512608800796 # test channel 724077902521696395 weekly-schedule 625399512608800796
    scheduleChannelId = 717868492313067560 # test channel 724077902521696395 weekly-sign-up 717868492313067560
    scheduleId = first_schedule[1]
    msgTxt = await getMessageText(scheduleId)
    if(msgTxt != None):
      msgTxt = msgTxt.split('\n\n\n\n')
      del msgTxt[-1]
      channelToSendTo = client.get_channel(channelId)
      currentChannel = client.get_channel(scheduleChannelId)
      try:
        oldMsgId = await getPostedScheduleMessage(scheduleId)
        oldMsg = await channelToSendTo.fetch_message(int(oldMsgId))
        await oldMsg.delete()

        oldScheduleMessageId = await getCurrentScheduleMessage(scheduleId)
        oldScheduleMessage = await currentChannel.fetch_message(int(oldScheduleMessageId))
        await oldScheduleMessage.delete()
      except Exception as e:
        print(e)
        await channelToSendTo.send("There was an error deleting the old schedule.")
      try:
        newMsg = await channelToSendTo.send(f"New Schedule! @everyone\n\n{msgTxt[0]}")
        await updatePostedSchedules(str(newMsg.id), scheduleId)
        c.execute("DELETE FROM schedules WHERE schedule_id = ?", (scheduleId,))
      except Exception as e:
        print(e)
        await channelToSendTo.send("There was an error posting the new schedule.")
    else:
      await channelToSendTo.author.send("Not a valid ID")

    conn.commit()
    c.close()
    conn.close()

@client.event
async def on_ready():
  print("Ready!")
  if(not autoPostSchedule.is_running()):
    print("Starting Auto Schedule Posting")
    autoPostSchedule.start()

# Run the bot
with open('tokens.json', 'r') as f:
  jsonInfoData = json.load(f)
TOKEN = jsonInfoData["bot"]
client.run(TOKEN)