# Dynamic Schedule

import discord
from discord.ext import commands
import json 
import uuid
import sqlite3

async def is_author_bot(ctx):
  return not ctx.author.bot

class Schedule (commands.Cog):
  def __init__(self, client):
    self.client = client

  async def getDays(self, msgId):
    conn = sqlite3.connect('dbs/schedules.db')
    c = conn.cursor() 
    
    sql = "SELECT schedule_text FROM schedules WHERE schedule_id = ?"
    c.execute(sql,(msgId,))
    allDays = c.fetchone()[0]
    daysSplit = allDays.split("\n\n")
    daysSplit.pop(0)
    del daysSplit[-1]
    del daysSplit[-1]
    
    dayDict = {}

    for dayInfo in daysSplit:
      formatInfo = dayInfo.replace('__','').split('\n')
      dayNums = "\n".join(formatInfo[1:])
      dayDict[formatInfo[0]] = f'{dayNums}'

    c.close()
    conn.close()
    return dayDict
  
  async def getMessageText(self, msgId):
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

  async def updatePostedSchedules(self, msgId, scheduleId):
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

  async def getPostedScheduleMessage(self, scheduleId):
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

  async def checkIfScheduleExists(self, scheduleId):
    conn = sqlite3.connect('dbs/schedules.db')
    c = conn.cursor()

    sql = "SELECT * FROM schedules WHERE schedule_id = ?"
    c.execute(sql,(scheduleId,))
    checkIfExists = c.fetchone()

    c.close()
    conn.close()
    if(checkIfExists == None):
      return False
    else:
      return True

  async def updateDayInfo(self, scheduleId, scheduleTxt):
    conn = sqlite3.connect('dbs/schedules.db')
    c = conn.cursor()

    sql = "SELECT schedule_text,schedule_title,message_id FROM schedules WHERE schedule_id = ?"
    c.execute(sql,(scheduleId,))
    oldTxtFull = c.fetchone()
    oldScheduleText = oldTxtFull[0]
    scheduleTitle = oldTxtFull[1]
    oldTxtSplit = oldScheduleText.split('\n\n\n\n')

    newScheduleTxt = f"**__Schedule For:__ {scheduleTitle}**\n\n"
    for dayName in scheduleTxt:
      newScheduleTxt += f"__{dayName}__\n{scheduleTxt[dayName]}\n\n"
    newScheduleTxt += f"\n\n{oldTxtSplit[1]}"

    sql = "UPDATE schedules SET schedule_text = ? WHERE schedule_id = ?"
    c.execute(sql,(newScheduleTxt,scheduleId))
    conn.commit()

    c.close()
    conn.close()
    return [oldTxtFull[2], newScheduleTxt]


  @commands.command()
  @commands.check(is_author_bot)

  async def schedule(self, ctx):
    color = 0x43c91f
    args = ctx.message.content.split(' ')
    role_day_emoji_dict = {"artisans": "🎨", "world_travels":"🗺️", "assassins_league":"🗡️", "questers_mark":"☠️", "rogue_runners":"🏃‍♂️", "more_merrier":"👥", "sunday":"☀️", "monday":"🇲", "tuesday":"🇹","wednesday":"🇼","thursday":"🔨","friday":"🇫","saturday":"🇸", "confirm":"✅", "message":"🗨️", "delete":"❌", "remove_schedule":"🚫"}
    # Help message
    if('-help' in args):
      with open('cogs/help/help_message.json', 'r') as f:
        help_message = json.load(f)
      help_emb = discord.Embed(color = color)
      help_emb.add_field(name = "Help for the schedule command", value = help_message["schedule"].format(role_day_emoji_dict["artisans"],
      role_day_emoji_dict["world_travels"],
      role_day_emoji_dict["assassins_league"],
      role_day_emoji_dict["questers_mark"],
      role_day_emoji_dict["rogue_runners"],
      role_day_emoji_dict["more_merrier"],
      role_day_emoji_dict["sunday"],
      role_day_emoji_dict["monday"],
      role_day_emoji_dict["tuesday"],
      role_day_emoji_dict["wednesday"],
      role_day_emoji_dict["thursday"],
      role_day_emoji_dict["friday"],
      role_day_emoji_dict["saturday"],
      role_day_emoji_dict["confirm"],
      role_day_emoji_dict["message"],
      role_day_emoji_dict["delete"]))
      await ctx.send( embed = help_emb)
      return

    elif('-post' in args):
      if(ctx.author.id in [294574889652715520, 546432782252113921, 356227435425169418, 384008963504603137, 567077990987726890]):
        channelId = 625399512608800796 # test channel 724077902521696395 weekly-schedule 625399512608800796
        scheduleId = ctx.message.content.replace("!schedule -post ","")
        msgTxt = await self.getMessageText(scheduleId)
        if(msgTxt != None):
          msgTxt = msgTxt.split('\n\n\n\n')
          del msgTxt[-1]
          channelToSendTo = self.client.get_channel(channelId)
          try:
            oldMsgId = await self.getPostedScheduleMessage(scheduleId)
            oldMsg = await channelToSendTo.fetch_message(int(oldMsgId))
            await oldMsg.delete()
          except Exception as e:
            print(e)
            await ctx.send("There was an error deleting the old schedule.")
          try:
            newMsg = await channelToSendTo.send(f"New Schedule! @everyone\n\n{msgTxt[0]}")
            await self.updatePostedSchedules(str(newMsg.id), scheduleId)
          except Exception as e:
            print(e)
            await ctx.send("There was an error posting the new schedule.")
        else:
          await ctx.author.send("Not a valid ID")
      return
    
    elif('-edit' in args):
      if(ctx.author.id in [294574889652715520, 546432782252113921, 356227435425169418, 384008963504603137, 567077990987726890]):
        editArgs = ctx.message.content.split(",")
        editArgs[0] = editArgs[0][-6:]
        scheduleId = editArgs[0]
        del editArgs[0]
        scheduleExists = await self.checkIfScheduleExists(scheduleId)

        if(scheduleExists):
          # pre-set vars
          dayToEdit = False
          numToEdit = False
          timeToEdit = ""
          leaderToEdit = ""
          detailsToEdit = ""
          delDayInfo = False

          #reassign vars new values if given
          for options in editArgs:
            options = options.strip()
            if("-day" in options):
              options = options.replace("-day","").strip()
              dayList = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
              if(options in dayList):
                dayToEdit = options
            elif("-num" in options):
              options = options.replace("-num","").strip()
              if(options.isnumeric()):
                if(int(options) in [1,2,3]):
                  numToEdit = options
            elif("-leader" in options):
              options = options.replace("-leader","").strip()
              optionsSplit = options.split(' ')
              for leaderOption in optionsSplit:
                if("&" in leaderOption):
                  discordChar = "&"
                else:
                  discordChar = ""
                leaderId = leaderOption.replace("<","").replace("@","").replace("&","").replace("!","").replace(">","").strip()
                if(leaderId.isnumeric()):
                  leaderToEdit = f"<@{discordChar}{leaderId}>"
            elif("-time" in options):
              options = options.replace("-time","").strip()
              timeToEdit = options
            elif("-details" in options):
              options = options.replace("-details","").strip()
              detailsToEdit = options
            elif("-delete" in options):
              delDayInfo = True
          if(dayToEdit == False) or (numToEdit == False):
            await ctx.author.send("Either no day or time was given or the ones given are wrong. Both are required to edit an event.")
          elif(delDayInfo == True):
            oldMsgTxt = await self.getDays(scheduleId)
            oldMsgTxtSplit = oldMsgTxt[dayToEdit].split("\n")
            for msgIndex, dayInfo in enumerate(oldMsgTxtSplit):
              if(f"{numToEdit}." in dayInfo):
                oldMsgTxtSplit[msgIndex] = f"{numToEdit}."
                break
            txtToUpdate = "\n".join(oldMsgTxtSplit)
            oldMsgTxt[dayToEdit] = txtToUpdate
            newMsgInfo = await self.updateDayInfo(scheduleId, oldMsgTxt)

            msgToUpdate = await ctx.fetch_message(newMsgInfo[0])
            await msgToUpdate.edit(content=newMsgInfo[1]) 
          else:
            #new message text
            branches = ["Artisans Wing", "World Travels", "Assassins League", "Questers Mark", "Rogue Runners", "The More The Merrier"]
            oldMsgTxt = await self.getDays(scheduleId)
            oldMsgTxtSplit = oldMsgTxt[dayToEdit].split("\n")
            for msgIndex, dayInfo in enumerate(oldMsgTxtSplit):
              if(f"{numToEdit}." in dayInfo):
                if(detailsToEdit == ""):
                  branchInDetails = False
                  for potentialBranches in branches:
                    if(f"{potentialBranches} - " in dayInfo):
                      detailsToEdit = potentialBranches
                      branchInDetails = True
                      break
                  if(branchInDetails == False) and (dayInfo.strip() == f"{numToEdit}."):
                    detailsToEdit = "Default Event (1GP/1BP)"
                  elif(branchInDetails == False):
                    formattedDayInfo = dayInfo.split(' at ')
                    detailsToEdit = formattedDayInfo[0].replace(f"{numToEdit}. ", "").strip() 
                    formattedDayInfo = formattedDayInfo[1].strip().split(' - ')
                    if(timeToEdit == ""):
                      timeToEdit = formattedDayInfo[0].strip()
                    if(leaderToEdit == ""):
                      leaderToEdit = formattedDayInfo[1].strip()

                if(timeToEdit == ""):
                  timeToEdit = "12AM CST"
                if(leaderToEdit == ""):
                  leaderToEdit = f"<@{ctx.author.id}>"
                newMsgTxt = f"{numToEdit}. {detailsToEdit} at {timeToEdit} - {leaderToEdit}"
                oldMsgTxtSplit[msgIndex] = newMsgTxt
                break
            txtToUpdate = "\n".join(oldMsgTxtSplit)
            oldMsgTxt[dayToEdit] = txtToUpdate
            newMsgInfo = await self.updateDayInfo(scheduleId, oldMsgTxt)

            msgToUpdate = await ctx.fetch_message(newMsgInfo[0])
            await msgToUpdate.edit(content=newMsgInfo[1]) 
        else:
          await ctx.author.send(f"No schedule with that ID\n\nID Given: {scheduleId}")        
      await ctx.message.delete(delay=5)
      return
    
    scheduleId = str(uuid.uuid4().int)[:6]
    scheduleTitle = " ".join(args[1:]) + " ALL events based upon Central Time zone (CST/CDT)"
    msgBaseContent = "**__Schedule For:__ {0}**\n\n__Sunday__\n1.\n2.\n3.\n\n__Monday__\n1.\n2.\n3.\n\n__Tuesday__\n1.\n2.\n3.\n\n__Wednesday__\n1.\n2.\n3.\n\n__Thursday__\n1.\n2.\n3.\n\n__Friday__\n1.\n2.\n3.\n\n__Saturday__\n1.\n2.\n3.\n\n\n\nSchedule ID: {1}".format(scheduleTitle, scheduleId)
    base_msg = await ctx.send(msgBaseContent)
    for emoji in role_day_emoji_dict:
      await base_msg.add_reaction(role_day_emoji_dict[emoji])

    conn = sqlite3.connect('dbs/schedules.db')
    c = conn.cursor()
    sql = "INSERT INTO schedules VALUES(?,?,?,?,?,?)"
    c.execute(sql,(str(base_msg.id), str(scheduleId), scheduleTitle, "", "", msgBaseContent))
    conn.commit() 
    c.close()
    conn.close()

def setup(client):
  client.add_cog(Schedule(client))