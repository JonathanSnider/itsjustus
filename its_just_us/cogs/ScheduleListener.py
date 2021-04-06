import discord
from discord.ext import commands
import json 
import sqlite3
import itertools

async def is_author_bot(channel):
  return not channel.author.bot

class ScheduleListener (commands.Cog):
  def __init__(self, client):
    self.client = client

  async def getDays(self, msgId):
    conn = sqlite3.connect('dbs/schedules.db')
    c = conn.cursor() 
    
    sql = "SELECT schedule_text FROM schedules WHERE message_id = ?"
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

  async def checkForDay(self, msgId, userId):
    conn = sqlite3.connect('dbs/schedules.db')
    c = conn.cursor() 

    sql = "SELECT person_day FROM schedules WHERE message_id = ?"
    c.execute(sql,(msgId,))
    allDaySelections = c.fetchone()[0].split(',')
    
    stringToDel = "{0} = ".format(userId)
    daySelected = "None"
    for name in allDaySelections:
      if(userId in name):
        daySelected = name.replace(stringToDel, '')
        break

    c.close()
    conn.close()
    return daySelected

  async def checkForRole(self, msgId, userId):
    conn = sqlite3.connect('dbs/schedules.db')
    c = conn.cursor() 

    sql = "SELECT person_role FROM schedules WHERE message_id = ?"
    c.execute(sql,(msgId,))
    allRoleSelections = c.fetchone()[0].split(',')
    
    stringToDel = "{0} = ".format(userId)
    roleSelected = "None"
    for name in allRoleSelections:
      if(userId in name):
        roleSelected = name.replace(stringToDel, '')
        break

    c.close()
    conn.close()
    return roleSelected

  async def returnRoleAndDay(self, msgId, userId):
    daySelected = await self.checkForDay(msgId, userId)
    roleSelected = await self.checkForRole(msgId, userId)

    confirmReady = False
    if(daySelected != "None") and (roleSelected != "None"):
      confirmReady = True

    conn = sqlite3.connect('dbs/schedules.db')
    c = conn.cursor() 

    sql = "SELECT schedule_id,schedule_title FROM schedules WHERE message_id = ?"
    c.execute(sql,(msgId,))
    scheduleTuple = c.fetchone()
    scheduleId = scheduleTuple[0]
    scheduleTitle = scheduleTuple[1]

    c.close()
    conn.close()

    return {"daySelected":daySelected, "roleSelected":roleSelected, "confirmReady":confirmReady, "scheduleId":scheduleId, "scheduleTitle":scheduleTitle}

  async def deleteSchedule(self, msgId):
    conn = sqlite3.connect('dbs/schedules.db')
    c = conn.cursor() 

    sql = "DELETE FROM schedules WHERE message_id = ?"
    c.execute(sql,(msgId,))
    conn.commit()
    c.close()
    conn.close()

  @commands.Cog.listener()
  async def on_raw_reaction_add(self, payload):
    if(str(payload.user_id) != "724076679483490444"):
      role_emoji_dict = {"Artisans Wing": "🎨", "World Travels":"🗺️", "Assassins League":"🗡️", "Questers Mark":"☠️", "Rogue Runners":"🏃‍♂️", "The More The Merrier":"👥"}
      day_emoji_dict = {"Sunday":"☀️", "Monday":"🇲", "Tuesday":"🇹","Wednesday":"🇼","Thursday":"🔨","Friday":"🇫","Saturday":"🇸"}

      conn = sqlite3.connect('dbs/schedules.db')
      c = conn.cursor()

      sql = "SELECT message_id FROM schedules"
      c.execute(sql)
      idResults = c.fetchall()
      for messageId in idResults:
        if(str(payload.message_id) == messageId[0]):
          channel = self.client.get_channel(payload.channel_id)
          scheduleMessage = await channel.fetch_message(payload.message_id)
          userToMessage = await scheduleMessage.guild.fetch_member(payload.user_id)
          for roleKey in role_emoji_dict:
            if(role_emoji_dict[roleKey] == str(payload.emoji)):
              sql = "SELECT person_role FROM schedules WHERE message_id = {0}".format(messageId[0])
              c.execute(sql,)
              allRoleSelections = c.fetchone()
              allRoleSelections = allRoleSelections[0].split(",")
              count = 0
              for name in allRoleSelections:
                if(str(payload.user_id) in name):
                  allRoleSelections[count] = "{0} = {1}".format(payload.user_id, roleKey)
                  break
                count+=1
                if(count == len(allRoleSelections)):
                  allRoleSelections.append("{0} = {1}".format(payload.user_id, roleKey))
              allRolesUpdated = ",".join(allRoleSelections[0:])
              sql = "UPDATE schedules SET person_role = ? WHERE message_id = ?"
              c.execute(sql,(allRolesUpdated, messageId[0]))
              conn.commit()
              roleAndDay = await self.returnRoleAndDay(str(payload.message_id), str(payload.user_id))
              await userToMessage.send("Day Selected: {0}\nBranch Selected: {1}\n\nSchedule ID: {2}".format(roleAndDay["daySelected"], roleAndDay["roleSelected"], roleAndDay["scheduleId"]))
              
              break
          for dayKey in day_emoji_dict:
            if(day_emoji_dict[dayKey] == str(payload.emoji)): 
              sql = "SELECT person_day FROM schedules WHERE message_id = {0}".format(messageId[0])
              c.execute(sql,)
              allDaySelections = c.fetchone()
              allDaySelections = allDaySelections[0].split(",")
              count = 0
              for name in allDaySelections:
                if(str(payload.user_id) in name):
                  allDaySelections[count] = "{0} = {1}".format(payload.user_id, dayKey)
                  break
                count+=1
                if(count == len(allDaySelections)):
                  allDaySelections.append("{0} = {1}".format(payload.user_id, dayKey))
              allDaysUpdated = ",".join(allDaySelections[0:])
              sql = "UPDATE schedules SET person_day = ? WHERE message_id = ?"
              c.execute(sql,(allDaysUpdated, messageId[0]))
              conn.commit()
              roleAndDay = await self.returnRoleAndDay(str(payload.message_id), str(payload.user_id))
              await userToMessage.send("Day Selected: {0}\nBranch Selected: {1}\n\nSchedule ID: {2}".format(roleAndDay["daySelected"], roleAndDay["roleSelected"], roleAndDay["scheduleId"]))
              
              break
          if(str(payload.emoji) == "✅"):
            roleAndDay = await self.returnRoleAndDay(str(payload.message_id), str(payload.user_id))
            if(not roleAndDay["confirmReady"]):
              await userToMessage.send("You are not ready to confirm a schedule change. You must have a day and branch selected.\n\n\nDay Selected: {0}\nBranch Selected: {1}\n\nSchedule ID: {2}".format(roleAndDay["daySelected"], roleAndDay["roleSelected"], roleAndDay["scheduleId"]))
            else:
              dayInfo = await self.getDays(str(payload.message_id))
              for numInfo in dayInfo:
                if(numInfo == roleAndDay["daySelected"]):
                  numsSplit = dayInfo[numInfo].split('\n')
                  dayFull = True
                  for counter, numCheck in enumerate(numsSplit):
                    if("<@" not in numCheck):
                      newTxt = f'{numCheck} {roleAndDay["roleSelected"]} - <@{payload.user_id}>'
                      numsSplit[counter] = newTxt
                      dayInfo[numInfo] = "\n".join(numsSplit)
                      dayFull = False
                      break
                  if(dayFull):
                    await userToMessage.send("That day is full. Please choose another day.")
              
              newScheduleTxt = f"**__Schedule For:__ {roleAndDay['scheduleTitle']}**\n\n"
              for numInfo in dayInfo:
                newTxt = f"__{numInfo}__\n{dayInfo[numInfo]}\n\n"
                newScheduleTxt+=newTxt
              scheduleIdAppend = f"\n\nSchedule ID: {roleAndDay['scheduleId']}"
              newScheduleTxt+=scheduleIdAppend
              sql = "UPDATE schedules SET schedule_text = ? WHERE schedule_id = ?"
              c.execute(sql,(newScheduleTxt,roleAndDay["scheduleId"]))

              messageToUpdate = await channel.fetch_message(payload.message_id)
              await messageToUpdate.edit(content=newScheduleTxt)
          elif(str(payload.emoji) == "🗨️"):
            roleAndDay = await self.returnRoleAndDay(str(payload.message_id), str(payload.user_id))
            await userToMessage.send("Day Selected: {0}\nBranch Selected: {1}\n\nSchedule ID: {2}".format(roleAndDay["daySelected"], roleAndDay["roleSelected"], roleAndDay["scheduleId"]))
          elif(str(payload.emoji) == "❌"):
            roleAndDay = await self.returnRoleAndDay(str(payload.message_id), str(payload.user_id))
            if(roleAndDay["daySelected"] == "None"):
              await userToMessage.send("You do not have a day selected. Please choose a day to delete an event.")
            else:
              dayInfo = await self.getDays(str(payload.message_id))
              userFormatted = f"<@{payload.user_id}>"
              dayNums = dayInfo[roleAndDay["daySelected"]].split("\n")
              
              counter = 1
              for i,info in enumerate(dayNums):
                if(userFormatted in info):
                  dayNums[i] = f"{counter}."
                counter+=1
              dayInfo[roleAndDay["daySelected"]] = "\n".join(dayNums)
              newScheduleTxt = f"**__Schedule For:__ {roleAndDay['scheduleTitle']}**\n\n"
              for numInfo in dayInfo:
                newTxt = f"__{numInfo}__\n{dayInfo[numInfo]}\n\n"
                newScheduleTxt+=newTxt
              scheduleIdAppend = f"\n\nSchedule ID: {roleAndDay['scheduleId']}"
              newScheduleTxt+=scheduleIdAppend
              sql = "UPDATE schedules SET schedule_text = ? WHERE schedule_id = ?"
              c.execute(sql,(newScheduleTxt,roleAndDay["scheduleId"]))

              messageToUpdate = await channel.fetch_message(payload.message_id)
              await messageToUpdate.edit(content=newScheduleTxt)
          elif(str(payload.emoji) == "🚫"):
            if(payload.user_id in [294574889652715520, 546432782252113921, 356227435425169418, 384008963504603137, 567077990987726890]):
              try:
                await self.deleteSchedule(str(payload.message_id))
                await scheduleMessage.delete()
                return
              except Exception as e:
                print(e)
                await userToMessage.send("There was an error deleting the schedule.")
            else:
              await userToMessage.send("You lack the permissions to do that.")
          await scheduleMessage.remove_reaction(payload.emoji, payload.member)

      conn.commit()
      c.close()
      conn.close()



def setup(client):
  client.add_cog(ScheduleListener(client))