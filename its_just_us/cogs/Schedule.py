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

  async def get_days(self, msg_id):
    conn = sqlite3.connect('dbs/schedules.db')
    c = conn.cursor() 
    
    sql = "SELECT schedule_text FROM schedules WHERE schedule_id = ?"
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
  
  async def get_message_text(self, msg_id):
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

  async def update_posted_schedules(self, msg_id, schedule_id):
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

  async def get_posted_schedule_message(self, schedule_id):
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

  async def check_if_schedule_exists(self, schedule_id):
    conn = sqlite3.connect('dbs/schedules.db')
    c = conn.cursor()

    sql = "SELECT * FROM schedules WHERE schedule_id = ?"
    c.execute(sql,(schedule_id,))
    check_if_exists = c.fetchone()

    c.close()
    conn.close()
    if(check_if_exists == None):
      return False
    else:
      return True

  async def update_day_info(self, schedule_id, schedule_txt):
    conn = sqlite3.connect('dbs/schedules.db')
    c = conn.cursor()

    sql = "SELECT schedule_text,schedule_title,message_id FROM schedules WHERE schedule_id = ?"
    c.execute(sql,(schedule_id,))
    old_txt_full = c.fetchone()
    old_schedule_text = old_txt_full[0]
    schedule_title = old_txt_full[1]
    old_txt_split = old_schedule_text.split('\n\n\n\n')

    new_schedule_txt = f"**__Schedule For:__ {schedule_title}**\n\n"
    for day_name in schedule_txt:
      new_schedule_txt += f"__{day_name}__\n{schedule_txt[day_name]}\n\n"
    new_schedule_txt += f"\n\n{old_txt_split[1]}"

    sql = "UPDATE schedules SET schedule_text = ? WHERE schedule_id = ?"
    c.execute(sql,(new_schedule_txt,schedule_id))
    conn.commit()

    c.close()
    conn.close()
    return [old_txt_full[2], new_schedule_txt]


  @commands.command()
  @commands.check(is_author_bot)

  async def schedule(self, ctx):
    color = 0x43c91f
    args = ctx.message.content.split(' ')
    role_day_emoji_dict = {"artisans": "🎨", "world_travels":"🗺️", "assassins_league":"🗡️", "questers_mark":"☠️", "rogue_runners":"🏃‍♂️", "more_merrier":"👥", "sunday":"☀️", "monday":"🇲", "tuesday":"🇹","wednesday":"🇼","thursday":"🔨","friday":"🇫","saturday":"🇸", "confirm":"✅", "message":"🗨️", "delete":"❌", "remove_schedule":"🚫"}
    with open('tokens.json') as f:
      tokens = json.load(f)
    user_ids = tokens["user_ids"]
    channel_ids = tokens["channel_ids"]
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
      if(ctx.author.id in [int(user_ids["sarge"]), int(user_ids["wasp"]), int(user_ids["angel"]), int(user_ids["opera"]), int(user_ids["mal"])]):
        channel_id = channel_ids["weekly_schedule"] 
        schedule_id = ctx.message.content.replace("!schedule -post ","")
        msg_txt = await self.get_message_text(schedule_id)
        if(msg_txt != None):
          msg_txt = msg_txt.split('\n\n\n\n')
          del msg_txt[-1]
          channel_to_send_to = self.client.get_channel(channel_id)
          try:
            old_msg_id = await self.get_posted_schedule_message(schedule_id)
            old_msg = await channel_to_send_to.fetch_message(int(old_msg_id))
            await old_msg.delete()
          except Exception as e:
            print(e)
            await ctx.send("There was an error deleting the old schedule.")
          try:
            new_msg = await channel_to_send_to.send(f"New Schedule! @everyone\n\n{msg_txt[0]}")
            await self.update_posted_schedules(str(new_msg.id), schedule_id)
          except Exception as e:
            print(e)
            await ctx.send("There was an error posting the new schedule.")
        else:
          await ctx.author.send("Not a valid ID")
      return
    
    elif('-edit' in args):
      if(ctx.author.id in [int(user_ids["sarge"]), int(user_ids["wasp"]), int(user_ids["angel"]), int(user_ids["opera"]), int(user_ids["mal"])]):
        edit_args = ctx.message.content.split(",")
        edit_args[0] = edit_args[0][-6:]
        schedule_id = edit_args[0]
        del edit_args[0]
        schedule_exists = await self.check_if_schedule_exists(schedule_id)

        if(schedule_exists):
          # pre-set vars
          day_to_edit = False
          num_to_edit = False
          time_to_edit = ""
          leader_to_edit = ""
          details_to_edit = ""
          del_day_info = False

          #reassign vars new values if given
          for options in edit_args:
            options = options.strip()
            if("-day" in options):
              options = options.replace("-day","").strip()
              day_list = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
              if(options in day_list):
                day_to_edit = options
            elif("-num" in options):
              options = options.replace("-num","").strip()
              if(options.isnumeric()):
                if(int(options) in [1,2,3]):
                  num_to_edit = options
            elif("-leader" in options):
              options = options.replace("-leader","").strip()
              options_split = options.split(' ')
              for leader_option in options_split:
                if("&" in leader_option):
                  discord_char = "&"
                else:
                  discord_char = ""
                leader_id = leader_option.replace("<","").replace("@","").replace("&","").replace("!","").replace(">","").strip()
                if(leader_id.isnumeric()):
                  leader_to_edit = f"<@{discord_char}{leader_id}>"
            elif("-time" in options):
              options = options.replace("-time","").strip()
              time_to_edit = options
            elif("-details" in options):
              options = options.replace("-details","").strip()
              details_to_edit = options
            elif("-delete" in options):
              del_day_info = True
          if(day_to_edit == False) or (num_to_edit == False):
            await ctx.author.send("Either no day or time was given or the ones given are wrong. Both are required to edit an event.")
          elif(del_day_info == True):
            old_msg_txt = await self.get_days(schedule_id)
            old_msg_txt_split = old_msg_txt[day_to_edit].split("\n")
            for msg_index, day_info in enumerate(old_msg_txt_split):
              if(f"{num_to_edit}." in day_info):
                old_msg_txt_split[msg_index] = f"{num_to_edit}."
                break
            txt_to_update = "\n".join(old_msg_txt_split)
            old_msg_txt[day_to_edit] = txt_to_update
            new_msg_info = await self.update_day_info(schedule_id, old_msg_txt)

            msg_to_update = await ctx.fetch_message(new_msg_info[0])
            await msg_to_update.edit(content=new_msg_info[1]) 
          else:
            #new message text
            branches = ["Artisans Wing", "World Travels", "Assassins League", "Questers Mark", "Rogue Runners", "The More The Merrier"]
            old_msg_txt = await self.get_days(schedule_id)
            old_msg_txt_split = old_msg_txt[day_to_edit].split("\n")
            for msg_index, day_info in enumerate(old_msg_txt_split):
              if(f"{num_to_edit}." in day_info):
                if(details_to_edit == ""):
                  branch_in_details = False
                  for potential_branches in branches:
                    if(f"{potential_branches} - " in day_info):
                      details_to_edit = potential_branches
                      branch_in_details = True
                      break
                  if(branch_in_details == False) and (day_info.strip() == f"{num_to_edit}."):
                    details_to_edit = "Default Event (1GP/1BP)"
                  elif(branch_in_details == False):
                    formatted_day_info = day_info.split(' at ')
                    details_to_edit = formatted_day_info[0].replace(f"{num_to_edit}. ", "").strip() 
                    formatted_day_info = formatted_day_info[1].strip().split(' - ')
                    if(time_to_edit == ""):
                      time_to_edit = formatted_day_info[0].strip()
                    if(leader_to_edit == ""):
                      leader_to_edit = formatted_day_info[1].strip()

                if(time_to_edit == ""):
                  time_to_edit = "12AM CST"
                if(leader_to_edit == ""):
                  leader_to_edit = f"<@{ctx.author.id}>"
                new_msg_txt = f"{num_to_edit}. {details_to_edit} at {time_to_edit} - {leader_to_edit}"
                old_msg_txt_split[msg_index] = new_msg_txt
                break
            txt_to_update = "\n".join(old_msg_txt_split)
            old_msg_txt[day_to_edit] = txt_to_update
            new_msg_info = await self.update_day_info(schedule_id, old_msg_txt)

            msg_to_update = await ctx.fetch_message(new_msg_info[0])
            await msg_to_update.edit(content=new_msg_info[1]) 
        else:
          await ctx.author.send(f"No schedule with that ID\n\nID Given: {schedule_id}")        
      await ctx.message.delete(delay=5)
      return
    
    schedule_id = str(uuid.uuid4().int)[:6]
    schedule_title = " ".join(args[1:]) + " ALL events based upon Central Time zone (CST/CDT)"
    msg_base_content = "**__Schedule For:__ {0}**\n\n__Sunday__\n1.\n2.\n3.\n\n__Monday__\n1.\n2.\n3.\n\n__Tuesday__\n1.\n2.\n3.\n\n__Wednesday__\n1.\n2.\n3.\n\n__Thursday__\n1.\n2.\n3.\n\n__Friday__\n1.\n2.\n3.\n\n__Saturday__\n1.\n2.\n3.\n\n\n\nSchedule ID: {1}".format(schedule_title, schedule_id)
    base_msg = await ctx.send(msg_base_content)
    for emoji in role_day_emoji_dict:
      await base_msg.add_reaction(role_day_emoji_dict[emoji])

    conn = sqlite3.connect('dbs/schedules.db')
    c = conn.cursor()
    sql = "INSERT INTO schedules VALUES(?,?,?,?,?,?)"
    c.execute(sql,(str(base_msg.id), str(schedule_id), schedule_title, "", "", msg_base_content))
    conn.commit() 
    c.close()
    conn.close()

def setup(client):
  client.add_cog(Schedule(client))