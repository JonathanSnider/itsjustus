import discord
from discord.ext import commands
from discord.ext.commands import Bot
import asyncio
from pathlib import Path
import requests
import json
import random

class Santa (commands.Cog):
  def __init__(self, client):
    self.client = client

  async def checkIfInFile(self, name, userId):
    with open("people.json", 'r') as inFile:
      people = json.load(inFile)

    for userName, Id in people.items():
      if(userName == name):
        return True
      elif(userId == Id): # user updated name
        removedPerson = await self.deleteUserFromFile(userName) 
        return False
    return False

  async def putUserInFile(self, name, userId):
    newValue = {name: userId}
    with open("people.json", 'r') as inFile:
      people = json.load(inFile)

    people.update(newValue)

    with open("people.json", 'w') as outFile:
      json.dump(people, outFile)

  async def deleteUserFromFile(self, name):
    with open("people.json", 'r') as inFile:
      people = json.load(inFile)
    removedPerson = people.pop(name, None)
    with open("people.json", 'w') as outFile:
      json.dump(people, outFile)    
    return removedPerson

  async def pruneUsers(self):
    with open("people.json", 'r') as inFile:
      people = json.load(inFile)

    nameList = []
    idList = []

    for userName, userId in people.items():
      if(userName in nameList):
        removedPerson = await self.deleteUserFromFile(userName)
      elif(userId in idList):
        removedPerson = await self.deleteUserFromFile(userName)
      else:
        nameList.append(userName)
        idList.append(userId)

  # async def getListOfPeople(self):
  #   with open("people.json", 'r') as inFile:
  #     people = json.load(inFile)
  #   nameDict = {}
  #   for name in people:
  #     nameDict[name] = people[name]
  #   return nameDict

  async def getRandomPerson(self, nameList):
    return random.choice(nameList)

  async def getRandomPairs(self):
    with open("people.json", 'r') as inFile:
      people = json.load(inFile)
    nameList = []
    for name in people:
      nameList.append(name)

    randomPairs = []
    alreadyPicked = []
    alreadyPickedIds = []
    for name in nameList:
      validPick = False
      while not validPick:
        pick = await self.getRandomPerson(nameList)
        if(pick in alreadyPicked):
          pass # not valid pick
        elif(name == pick):
          if(len(nameList) == (len(alreadyPicked) + 1)):
            # Last person to be picked is also the person picking, causing an infinite loop
            # To counter this, redraw until a valid list is produced
            #validPick = True # Function will recursively redraw until a valid list is done, so this is True
            #return await self.getRandomPairs() # run function until picks are valid
            return False
          else:
            pass # not a valid pick
        else:
          alreadyPicked.append(pick)
          alreadyPickedIds.append(people[pick])
          validPick = True # valid pick
      pair = name, pick
      randomPairs.append(pair)
    return randomPairs
  
  async def messagePairs(self, ctx, namePairs):
    with open("people.json", 'r') as inFile:
      people = json.load(inFile)
    for names in namePairs:
      userToMessage = await ctx.guild.fetch_member(people[names[0]])
      await userToMessage.send(f"Hello there {names[0]}! Your Secret Santa pick is **{names[1]}**. Have a good day and Merry Christmas!")

  @commands.command()
  # Random Dog Gifs
  async def enter(self, ctx):
    name = ctx.author.name
    userId = ctx.author.id
    userInFile = await self.checkIfInFile(name, userId)
    
    if(userInFile == True):
      await ctx.send("Already entered!")
      return
    else:
      try:
        await self.putUserInFile(name, userId)
        await ctx.send("Entered!")
      except Exception as e:
        await ctx.send("Sorry! There was an error.")
        await ctx.send(f"<@294574889652715520> {e}")
  
  @commands.command()
  async def withdraw(self, ctx):
    name = ctx.author.name
    try:
      removedPerson = await self.deleteUserFromFile(name)
      if(removedPerson == None):
        await ctx.send("Not entered! Please use **!enter** to enter yourself!")
      else:
        await ctx.send("Withdrawn!")
    except Exception as e:
      await ctx.send("Sorry! There was an error.")
      await ctx.send(f"<@294574889652715520> {e}")

  @commands.command()
  async def draw(self, ctx):
    userId = ctx.author.id
    if(userId in [294574889652715520, 546432782252113921]):
      try:
        await self.pruneUsers()
        validPicks = False
        while not validPicks:
          pairs = await self.getRandomPairs()
          if(pairs != False):
            validPicks = True
        await self.messagePairs(ctx, pairs)
      except Exception as e:
        await ctx.send("Sorry! There was an error.")
        await ctx.send(f"<@294574889652715520> {e}")
    else:
      await ctx.send("https://tenor.com/R0yA.gif")

  @commands.command()
  async def listpeople(self, ctx):
    userId = ctx.author.id
    if(userId in [294574889652715520, 546432782252113921]):
      with open("people.json", 'r') as inFile:
        people = json.load(inFile)
      pplStr = ""
      for names in people:
        pplStr+=f"{names}\n"
      if(pplStr == ""):
        pplStr = "None"
      await ctx.send(pplStr)
    else:
      await ctx.send("https://tenor.com/R0yA.gif")
def setup(client):
  n = Santa(client)
  client.add_cog(n)    