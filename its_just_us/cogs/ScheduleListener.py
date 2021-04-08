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

  async def get_days(self, msg_id):
    conn = sqlite3.connect('dbs/schedules.db')
    c = conn.cursor() 
    
    sql = "SELECT schedule_text FROM schedules WHERE message_id = ?"
    c.execute(sql,(msg_id,))
    all_days = c.fetchone()[0]
    days_split = all_days.split("\n\n")
    days_split.pop(0)
    del days_split[-1]
    del days_split[-1]
    
    day_dict = {}

    for day_info in days_split:
      format_info = day_info.replace('__','').split('\n')
      day_nums = "\n".join(format_info[1:])
      day_dict[format_info[0]] = f'{day_nums}'

    c.close()
    conn.close()
    return day_dict

  async def check_for_day(self, msg_id, user_id):
    conn = sqlite3.connect('dbs/schedules.db')
    c = conn.cursor() 

    sql = "SELECT person_day FROM schedules WHERE message_id = ?"
    c.execute(sql,(msg_id,))
    all_day_selections = c.fetchone()[0].split(',')
    
    string_to_del = "{0} = ".format(user_id)
    day_selected = "None"
    for name in all_day_selections:
      if(user_id in name):
        day_selected = name.replace(string_to_del, '')
        break

    c.close()
    conn.close()
    return day_selected

  async def check_for_role(self, msg_id, user_id):
    conn = sqlite3.connect('dbs/schedules.db')
    c = conn.cursor() 

    sql = "SELECT person_role FROM schedules WHERE message_id = ?"
    c.execute(sql,(msg_id,))
    all_role_selections = c.fetchone()[0].split(',')
    
    string_to_del = "{0} = ".format(user_id)
    role_selected = "None"
    for name in all_role_selections:
      if(user_id in name):
        role_selected = name.replace(string_to_del, '')
        break

    c.close()
    conn.close()
    return role_selected

  async def return_role_and_day(self, msg_id, user_id):
    day_selected = await self.check_for_day(msg_id, user_id)
    role_selected = await self.check_for_role(msg_id, user_id)

    confirm_ready = False
    if(day_selected != "None") and (role_selected != "None"):
      confirm_ready = True

    conn = sqlite3.connect('dbs/schedules.db')
    c = conn.cursor() 

    sql = "SELECT schedule_id,schedule_title FROM schedules WHERE message_id = ?"
    c.execute(sql,(msg_id,))
    schedule_tuple = c.fetchone()
    schedule_id = schedule_tuple[0]
    schedule_title = schedule_tuple[1]

    c.close()
    conn.close()

    return {"day_selected":day_selected, "role_selected":role_selected, "confirm_ready":confirm_ready, "schedule_id":schedule_id, "schedule_title":schedule_title}

  async def delete_schedule(self, msg_id):
    conn = sqlite3.connect('dbs/schedules.db')
    c = conn.cursor() 

    sql = "DELETE FROM schedules WHERE message_id = ?"
    c.execute(sql,(msg_id,))
    conn.commit()
    c.close()
    conn.close()

  @commands.Cog.listener()
  async def on_raw_reaction_add(self, payload):
    with open('tokens.json') as f:
        tokens = json.load(f)
    user_ids = tokens["user_ids"]
    if(payload.user_id != user_ids["bot"]): 
      role_emoji_dict = {"Artisans Wing": "🎨", "World Travels":"🗺️", "Assassins League":"🗡️", "Questers Mark":"☠️", "Rogue Runners":"🏃‍♂️", "The More The Merrier":"👥"}
      day_emoji_dict = {"Sunday":"☀️", "Monday":"🇲", "Tuesday":"🇹","Wednesday":"🇼","Thursday":"🔨","Friday":"🇫","Saturday":"🇸"}

      conn = sqlite3.connect('dbs/schedules.db')
      c = conn.cursor()

      sql = "SELECT message_id FROM schedules"
      c.execute(sql)
      id_results = c.fetchall()
      for message_id in id_results:
        if(str(payload.message_id) == message_id[0]):
          channel = self.client.get_channel(payload.channel_id)
          schedule_message = await channel.fetch_message(payload.message_id)
          user_to_message = await schedule_message.guild.fetch_member(payload.user_id)
          for role_key in role_emoji_dict:
            if(role_emoji_dict[role_key] == str(payload.emoji)):
              sql = "SELECT person_role FROM schedules WHERE message_id = {0}".format(message_id[0])
              c.execute(sql,)
              all_role_selections = c.fetchone()
              all_role_selections = all_role_selections[0].split(",")
              count = 0
              for name in all_role_selections:
                if(str(payload.user_id) in name):
                  all_role_selections[count] = "{0} = {1}".format(payload.user_id, role_key)
                  break
                count+=1
                if(count == len(all_role_selections)):
                  all_role_selections.append("{0} = {1}".format(payload.user_id, role_key))
              all_roles_updated = ",".join(all_role_selections[0:])
              sql = "UPDATE schedules SET person_role = ? WHERE message_id = ?"
              c.execute(sql,(all_roles_updated, message_id[0]))
              conn.commit()
              role_and_day = await self.return_role_and_day(str(payload.message_id), str(payload.user_id))
              await user_to_message.send("Day Selected: {0}\nBranch Selected: {1}\n\nSchedule ID: {2}".format(role_and_day["day_selected"], role_and_day["role_selected"], role_and_day["schedule_id"]))
              
              break
          for day_key in day_emoji_dict:
            if(day_emoji_dict[day_key] == str(payload.emoji)): 
              sql = "SELECT person_day FROM schedules WHERE message_id = {0}".format(message_id[0])
              c.execute(sql,)
              all_day_selections = c.fetchone()
              all_day_selections = all_day_selections[0].split(",")
              count = 0
              for name in all_day_selections:
                if(str(payload.user_id) in name):
                  all_day_selections[count] = "{0} = {1}".format(payload.user_id, day_key)
                  break
                count+=1
                if(count == len(all_day_selections)):
                  all_day_selections.append("{0} = {1}".format(payload.user_id, day_key))
              all_days_updated = ",".join(all_day_selections[0:])
              sql = "UPDATE schedules SET person_day = ? WHERE message_id = ?"
              c.execute(sql,(all_days_updated, message_id[0]))
              conn.commit()
              role_and_day = await self.return_role_and_day(str(payload.message_id), str(payload.user_id))
              await user_to_message.send("Day Selected: {0}\nBranch Selected: {1}\n\nSchedule ID: {2}".format(role_and_day["day_selected"], role_and_day["role_selected"], role_and_day["schedule_id"]))
              
              break
          if(str(payload.emoji) == "✅"):
            role_and_day = await self.return_role_and_day(str(payload.message_id), str(payload.user_id))
            if(not role_and_day["confirm_ready"]):
              await user_to_message.send("You are not ready to confirm a schedule change. You must have a day and branch selected.\n\n\nDay Selected: {0}\nBranch Selected: {1}\n\nSchedule ID: {2}".format(role_and_day["day_selected"], role_and_day["role_selected"], role_and_day["schedule_id"]))
            else:
              day_info = await self.get_days(str(payload.message_id))
              for num_info in day_info:
                if(num_info == role_and_day["day_selected"]):
                  nums_split = day_info[num_info].split('\n')
                  day_full = True
                  for counter, numCheck in enumerate(nums_split):
                    if("<@" not in numCheck):
                      new_txt = f'{numCheck} {role_and_day["role_selected"]} - <@{payload.user_id}>'
                      nums_split[counter] = new_txt
                      day_info[num_info] = "\n".join(nums_split)
                      day_full = False
                      break
                  if(day_full):
                    await user_to_message.send("That day is full. Please choose another day.")
              
              new_schedule_txt = f"**__Schedule For:__ {role_and_day['schedule_title']}**\n\n"
              for num_info in day_info:
                new_txt = f"__{num_info}__\n{day_info[num_info]}\n\n"
                new_schedule_txt+=new_txt
              schedule_id_append = f"\n\nSchedule ID: {role_and_day['schedule_id']}"
              new_schedule_txt+=schedule_id_append
              sql = "UPDATE schedules SET schedule_text = ? WHERE schedule_id = ?"
              c.execute(sql,(new_schedule_txt,role_and_day["schedule_id"]))

              message_to_update = await channel.fetch_message(payload.message_id)
              await message_to_update.edit(content=new_schedule_txt)
          elif(str(payload.emoji) == "🗨️"):
            role_and_day = await self.return_role_and_day(str(payload.message_id), str(payload.user_id))
            await user_to_message.send("Day Selected: {0}\nBranch Selected: {1}\n\nSchedule ID: {2}".format(role_and_day["day_selected"], role_and_day["role_selected"], role_and_day["schedule_id"]))
          elif(str(payload.emoji) == "❌"):
            role_and_day = await self.return_role_and_day(str(payload.message_id), str(payload.user_id))
            if(role_and_day["day_selected"] == "None"):
              await user_to_message.send("You do not have a day selected. Please choose a day to delete an event.")
            else:
              day_info = await self.get_days(str(payload.message_id))
              user_formatted = f"<@{payload.user_id}>"
              day_nums = day_info[role_and_day["day_selected"]].split("\n")
              
              counter = 1
              for i,info in enumerate(day_nums):
                if(user_formatted in info):
                  day_nums[i] = f"{counter}."
                counter+=1
              day_info[role_and_day["day_selected"]] = "\n".join(day_nums)
              new_schedule_txt = f"**__Schedule For:__ {role_and_day['schedule_title']}**\n\n"
              for num_info in day_info:
                new_txt = f"__{num_info}__\n{day_info[num_info]}\n\n"
                new_schedule_txt+=new_txt
              schedule_id_append = f"\n\nSchedule ID: {role_and_day['schedule_id']}"
              new_schedule_txt+=schedule_id_append
              sql = "UPDATE schedules SET schedule_text = ? WHERE schedule_id = ?"
              c.execute(sql,(new_schedule_txt,role_and_day["schedule_id"]))

              message_to_update = await channel.fetch_message(payload.message_id)
              await message_to_update.edit(content=new_schedule_txt)
          elif(str(payload.emoji) == "🚫"):
            if(payload.user_id in [int(user_ids["sarge"]), int(user_ids["wasp"]), int(user_ids["angel"]), int(user_ids["opera"]), int(user_ids["mal"])]):
              try:
                await self.delete_schedule(str(payload.message_id))
                await schedule_message.delete()
                return
              except Exception as e:
                print(e)
                await user_to_message.send("There was an error deleting the schedule.")
            else:
              await user_to_message.send("You lack the permissions to do that.")
          await schedule_message.remove_reaction(payload.emoji, payload.member)

      conn.commit()
      c.close()
      conn.close()



def setup(client):
  client.add_cog(ScheduleListener(client))