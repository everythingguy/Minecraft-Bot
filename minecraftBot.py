from discord.ext.commands import Bot
from discord.ext import commands
from mcstatus import MinecraftServer
from threading import Thread
from searchYT import search, getInfo, getPlaylist
import asyncio, time, discord, os, subprocess, socket, sys, youtube_dl, re, io, random, datetime

botID = ""

Client = discord.Client()
client = commands.Bot(command_prefix = "!")

serverUp = False
startingPC = False
lastChannel = None
playerWatcherCount = 0

triggers = []
blacklist = []
players = {}
voices = {}
musicQueue = {}
radioQueue = {}
musicChoices = {}
currentSong = {}
addingSong = False
leaving = False
downloading = False

#local IPs
botIP = ''
serverIP = ''

#global IPs
mcServerIP = ''
mcServerPort = ''

serverPlaylistURL = ''
yourDiscordID = ''

mcServerMacAddress = ''

@client.event
async def on_ready():
	print("Bot Started")
	await client.change_presence(game=discord.Game(name='Minecraft | !mc commands'))
	with io.open('mctriggers.txt', encoding='utf-8') as txtfile:
		for line in txtfile.readlines():
			trigger = line.split(', ')
			triggers.append(trigger)
	with io.open('mcblacklist.txt', encoding='utf-8') as listFile:
		for line in listFile.readlines():
			blacklist.append(line)
	checkServerPower()
	
@client.event
async def on_message(message):
	global serverUp, lastChannel, startingPC
	lastChannel = message.channel
	checkServerPower()
	if str(message.author)[-5:] in blacklist and message.content.startswith("!mc"):
		await client.delete_message(message)
	else:
		if message.content == "!mc start":
			if serverUp == False and startingPC == False and len(serverIP) > 0:
				await client.send_message(message.channel, "The Minecraft server is starting. This can take a minute. You can join at " + mcServerIP + ":" + mcServerPort)
				if pingPC(serverIP) == True:
					printSocket("Start Minecraft server")
					printSocket(str(message.author) + " started the Minecraft server")
					serverUp = True
				else:
					startPC(serverIP)
					startingPC = True
			elif len(serverIP > 0):
				await client.send_message(message.channel, "Error: The server is not setup")
			else:
				await client.send_message(message.channel, "The server is already running/starting")
		elif message.content == "!mc playlist":
			await client.send_message(message.channel, "Playlist for Minecraft Bot feel free to add to the playlist \n" + serverPlaylistURL)
		elif message.content == "!mc player count":
			if serverUp == True:
				players = checkPlayers()
				await client.send_message(message.channel, "There are " + str(players) + " player(s) on the server")
			else:
				await client.send_message(message.channel, "The server is not running")
		elif message.content == "!mc clear":
			await clearCommands(message)
		elif message.content == "!mc stop":
			players = checkPlayers()
			if serverUp == True and players <= 0:
				await client.send_message(message.channel, "Shutting down the server!")
				printSocket((str(message.author) + " stopped the Minecraft server"))
				shutdownServer()
			elif players > 0:
				await client.send_message(message.channel, "Can't shutdown the server players are on it!")
			else:
				await client.send_message(message.channel, "The server is not running")
		elif message.content.startswith('!mc ban'):
			banPlayer(message)
		elif message.content.startswith('!mc unban'):
			unbanPlayer(message)
		elif message.content == '!mc triggers':
			await triggerMenu(message)
		elif message.content.startswith('!mc trigger'):
			addTrigger(message)
		elif message.content.startswith("!mc radio"):
			checkMessage = message.content.replace("!mc radio", "")
			checkMessage = checkMessage.replace("-s", "")
			checkMessage = checkMessage.replace("-p", "")
			checkMessage = checkMessage.strip()
			turningOff = False
			if checkMessage.lower() == "off":
				radioQueue[message.server.id] = []
				turningOff = True
			elif checkMessage.lower() == "playlist":
				message.content = message.content.replace('playlist', serverPlaylistURL)
			shuffleSongs = False
			pickRan = False
			if '-s' in message.content:
				shuffleSongs = True
			if '-p' in message.content:
				pickRan = True
			if turningOff == False:
				await radio(message, Shuffle=shuffleSongs, ran=pickRan)
		elif message.content.startswith("!mc play -o"):
			playThread = Thread(target=playOptions, args=[message])
			playThread.start()
		elif message.content == "!mc play -cancel":
			pickCancel(message)
		elif message.content.startswith("!mc play"):
			await play(message)
		elif message.content.startswith("!mc pick"):
			await pickSong(message)
		elif message.content == "!mc queue":
			await postQue(message)
		elif message.content == "!mc leave":
			await leave(message)
		elif message.content == "!mc skip":
			skipSong(message)
		elif message.content == "!mc status":
			if serverUp == True:
				players = checkPlayers()
				await client.send_message(message.channel, "The server is currently running with " + str(players) + " player(s). You can join at " + mcServerIP + ":" + mcServerPort)
			else:
				await client.send_message(message.channel, 'The server is not running! Type "!mc start" to start the server')
		elif message.content == "!mc commands":
			await client.send_message(message.channel, "Commands: \n !mc start - start the minecraft server \n !mc stop - stop the Minecraft server \n !mc player count - get the amount of players on the Minecraft server \n !mc status - check to see if the Minecraft server is up \n !mc clear - clears commands from chat \n !mc radio [-s -p] <band name/Playlist URL> - to play a playlist of the bands songs, use the -s tag to shuffle the playlist and/or the -p tag to pick a random playlist instead of the first one on YT \n !mc radio playlist - play the server playlist \n !mc radio off - turn off radio \n !mc playlist - edit the server playlist \n !mc play [-o] <song name/link> - play a song from YouTube, add the -o tag to get options of songs to pick \n !mc leave - tells the bot to leave the voice channel \n !mc queue - Gets the current lineup of songs \n !mc skip - skips the current song \n !mc triggers - Show audio triggers and help on how to make one \n --------------------")
		else:
			if message.author != client.user:
				Triggered = False
				voiceChannel = message.server
				for trigger in triggers:
					if trigger[0] in message.content.lower() and Triggered == False:
						if voiceChannel.id in musicQueue:
							Queue = musicQueue[voiceChannel.id]
							inQueue = False
							if voiceChannel.id in currentSong and currentSong[voiceChannel.id] == trigger[1]:
								inQueue = True
							else:
								for x in range(len(Queue)):
									if trigger[1] == Queue[x][0]:
										inQueue = True
							if inQueue == False:
								message.content = "!mc play " + trigger[1]
								await play(message)
								Triggered = True
						else:
							message.content = "!mc play " + trigger[1]
							await play(message)
							Triggered = True

def banPlayer(message):
	playerID = message.content.replace("!mc ban ", "")
	if '#' in playerID and len(playerID) == 5 and str(message.author.id) == yourDiscordID:
		if playerID in blacklist:
			pass
		else:
			with io.open('mcblacklist.txt', 'a', encoding='utf-8') as banMenu:
				banMenu.write(playerID + '\n')
				blacklist.append(playerID)

def unbanPlayer(message):
	playerID = message.content.replace("!mc unban ", "")
	if '#' in playerID and len(playerID) == 5 and str(message.author.id) == yourDiscordID:
		memoryFile = io.open('mcblacklist.txt', 'r', encoding='utf-8').readlines()
		with io.open('mcblacklist.txt', 'w', encoding='utf-8') as banMenu:
			for line in memoryFile:
				if line != playerID + '\n':
					banMenu.write(line)
		blacklist.remove(playerID)

def addTrigger(message):
	trigger = message.content.replace('!mc trigger ', '')
	if getUrl(trigger) != 'Not a link' and ', ' in trigger:
		array = trigger.split(', ')
		if len(array) == 2:
			array = [array[0].lower(), array[1]]
			if array in triggers:
				pass
			else:
				triggers.append(array)
				with io.open('mctriggers.txt', 'a', encoding='utf-8') as triggerMenu:
					triggerMenu.write(trigger + '\n')

async def triggerMenu(message):
	menu = "............How to............... \n Use command !mc trigger <trigger word(s)>, <URL> \n ex: !mc trigger drift, TokyoDriftURL \n When using the command make sure you don't forget the ',' comma \n"
	menu = menu + "...........Triggers.............. \n "
	for trigger in triggers:
		print(trigger[0])
		menu = menu + trigger[0] + '\n'
	print(menu)
	await client.send_message(message.channel, menu)

async def radio(message, Shuffle=False, ran=False):
	global currentSong
	voiceChannel = message.server
	url = ''
	query = message.content.replace('!mc radio ', '')
	if Shuffle == True and ran == True:
		query = query.replace('-s -p', '')
		query = query.replace('-p -s', '')
	elif Shuffle == True:
		query = query.replace('-s', '')
	elif ran == True:
		query = query.replace('-p', '')
	if getUrl(query) == 'Not a link':
		query = query + ' playlist'
		results = search(query, True)
		playlist = []
		for result in results:
			if '&list=' in result[1] or '?list=' in result[1]:
				playlist.append(result[1])
		if ran == True:
			if(len(playlist) > 0):
				url = random.choice(playlist)
			else:
				url = "Not a link"
		else:
			if(len(playlist) > 0):
				url = playlist[0]
			else:
				url = "Not a link"
	else: 
		if '&list=' in query or '?list=' in query:
			url = query
		else:
			await client.send_message(message.channel, 'Error: That is not a playlist url')
	if(url != "Not a link"):
		videos = getPlaylist(url)
		if(len(videos) == 0):
			await client.send_message(message.channel, 'Error: that playlist has no videos, try using the -p tag or giving me a playlist url')
			return
		if Shuffle == True:
			random.shuffle(videos)
		radioQueue[voiceChannel.id] = videos
		if voiceChannel.id in currentSong:
			if currentSong[voiceChannel.id] == '' or currentSong[voiceChannel.id] == None or currentSong[voiceChannel.id] == "None":
				playNext(message)
		else:
			playNext(message)
	else:
		await client.send_message(message.channel, 'Error: Cannot find a playlist, try giving me a playlist url')


async def play(message, next=False, Playlist=False):
	global addingSong, currentSong
	words = False
	url = 'Not a link'
	voiceChannel = message.server
	Queue = []
	if voiceChannel.id in musicQueue:
		Queue = musicQueue[voiceChannel.id]
	if next == False:
		url = getUrl(message.content)
		if url == 'Not a link':
			words = True
			print('Word search')
		print(url)
	elif len(Queue) > 0:
		url = Queue[0][0]
		message = Queue[0][1]
		Queue.pop(0)
		musicQueue[voiceChannel.id] = Queue
	if '&list=' in url or '?list=' in url:
		#checks if playlist, they aren't allowed here
		url = 'Not a link'
		print("Playlists aren't allowed here")
	if url is not 'Not a link' and words == False:
		print(url)
		voiceChannel = message.server
		player = None
		if voiceChannel.id in players:
			player = players[voiceChannel.id]
		if player == None and addingSong == False:
			addingSong = True
			state = await join(message)
			if state != 'Error':
				voice_client = client.voice_client_in(voiceChannel)
				members = voice_client.channel.voice_members
				if len(members) <= 1:
					await leave(message)
					return
				downloading = True
				try:
					if '&list=' in url or '?list=' in url:
						await client.send_message(message.channel, 'Error: that is a playlist url, playlist are only allowed on the radio')
						pass
					else:
						player = await voice_client.create_ytdl_player(url, after=lambda: playNext(message), ytdl_options="--ignore-errors", before_options=" -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5")
						player.volume = .5
						currentSong[voiceChannel.id] = player.title
						players[voiceChannel.id] = player
						player.start()
						if Playlist == False:
							await client.send_message(message.channel, 'Playing: ' + player.title)
				except Exception as e:
					print("Handled Error: " + str(e))
					state = await join(message, True)
					if state != "Error":
						if '&list=' in url or '?list=' in url:
							await client.send_message(message.channel, 'Error: that is a playlist url, playlist are only allowed on the radio')
							pass
						else:
							voice_client = client.voice_client_in(voiceChannel)
							player = await voice_client.create_ytdl_player(url, after=lambda: playNext(message), ytdl_options="--ignore-errors", before_options=" -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5")
							player.volume = .5
							currentSong[voiceChannel.id] = player.title
							players[voiceChannel.id] = player
							player.start()
							if Playlist == False:
								await client.send_message(message.channel, 'Playing: ' + player.title)
				if Playlist == True:
					botMessage = 'Playing ' + str(player.title) + ' ' + str(datetime.timedelta(seconds=player.duration)) + '\n' + str(player.url)
					await client.send_message(message.channel, botMessage)
				addingSong = False
				downloading = False
		elif addingSong == True or player.is_playing() and next == False:
			state = await join(message)
			song = [url, message]
			if voiceChannel.id in musicQueue:
				Queue = musicQueue[voiceChannel.id]
			else:
				Queue = []
			Queue.append(song)
			musicQueue[voiceChannel.id] = Queue
		elif next == True or Playlist == True:
			if player.is_playing():
				player.stop()
			addingSong = True
			state = await join(message)
			if state != 'Error':
				voice_client = client.voice_client_in(voiceChannel)
				members = voice_client.channel.voice_members
				if len(members) <= 1:
					await leave(message)
					return
				downloading = True
				try:
					if '&list=' in url or '?list=' in url:
						await client.send_message(message.channel, 'Error: that is a playlist url, playlist are only allowed on the radio')
						pass
					else:
						player = await voice_client.create_ytdl_player(url, after=lambda: playNext(message), ytdl_options="--ignore-errors", before_options=" -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5")
						player.volume = .5
						players[voiceChannel.id] = player
						player.start()
						if Playlist == False:
							await client.send_message(message.channel, 'Playing: ' + player.title)
				except Exception as e:
					print("Handled Error: " + str(e))
					state = await join(message, True)
					if state != "Error":
						if '&list=' in url or '?list=' in url:
							await client.send_message(message.channel, 'Error: that is a playlist url, playlist are only allowed on the radio')
							pass
						else:
							voice_client = client.voice_client_in(voiceChannel)
							members = voice_client.channel.voice_members
							if len(members) <= 1:
								await leave(message)
								return
							player = await voice_client.create_ytdl_player(url, after=lambda: playNext(message), ytdl_options="--ignore-errors", before_options=" -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5")
							player.volume = .5
							players[voiceChannel.id] = player
							player.start()
							if Playlist == False:
								await client.send_message(message.channel, 'Playing: ' + player.title)
				if Playlist == True:
					botMessage = 'Playing ' + str(player.title) + ' ' + str(datetime.timedelta(seconds=player.duration)) + '\n' + str(player.url)
					await client.send_message(message.channel, botMessage)
				currentSong[voiceChannel.id] = player.title
				addingSong = False
				downloading = False
	elif next == False:
		if '&list=' in url or '?list=' in url:
			await client.send_message(message.channel, 'Error: that is a playlist url, playlist are only allowed on the radio')
			pass
		else:
			#Searches for video with words
			query = message.content
			query = query.replace("!mc play ", "")
			print(query)
			results = search(query)
			print(results[0][1])
			message.content = str(results[0][1])
			await client.send_message(message.channel, "Adding " + message.content)
			await play(message)

async def botMessage(message, botmessage):
	await client.send_message(message.channel, botmessage)

def playOptions(message):
	if message.author.id in musicChoices:
		pass
	elif getUrl(message.content) == "Not a link":
		print(message.author.id)
		query = message.content
		query = query.replace("!mc play -o ", "")
		print(query)
		results = search(query)
		botmessage = ''
		for x in range(5):
			num = x + 1
			videoName = getInfo(results[x][1])
			botmessage = botmessage + str(num) + " " + videoName + "\n"
		musicChoices[message.author.id] = results
		botmessage = botmessage + "Use !mc pick <Number> \n"
		botmessage = botmessage + "Use !mc play -cancel, to cancel"
		asyncio.run_coroutine_threadsafe(client.send_message(message.channel, botmessage), client.loop)
	else:
		asyncio.run_coroutine_threadsafe(play(message), client.loop)

async def pickSong(message):
	if message.author.id in musicChoices:
		choice = message.content
		choice = choice.replace("!mc pick ", "")
		choice = int(choice)
		choice = choice - 1
		options = musicChoices[message.author.id]
		message.content = str(options[choice][1])
		musicChoices[message.author.id] = None
		musicChoices.pop(message.author.id, None)
		await play(message)

def pickCancel(message):
	if message.author.id in musicChoices:
		musicChoices[message.author.id] = None
		musicChoices.pop(message.author.id, None)
		
def playNext(message):
	print('NEXT')
	voiceChannel = message.server
	Queue = []
	radio = []
	if voiceChannel.id in musicQueue:
		Queue = musicQueue[voiceChannel.id]

	if voiceChannel.id in radioQueue:
		radio = radioQueue[voiceChannel.id]
	if len(Queue) == 0 and len(radio) == 0:
		asyncio.run_coroutine_threadsafe(leave(message), client.loop)
	elif len(radio) > 0 and len(Queue) == 0:
		message.content = '!mc play ' + radio[0][1]
		radio.pop(0)
		radioQueue[message.server.id] = radio
		print('NEXT: ' + message.content)
		asyncio.run_coroutine_threadsafe(play(message, Playlist=True), client.loop)
	elif leaving == False:
		asyncio.run_coroutine_threadsafe(play(message, next=True), client.loop)
	
def skipSong(message):
	voiceChannel = message.server
	if voiceChannel.id in players:
		players[voiceChannel.id].stop()

async def postQue(message):
	global currentSong
	voiceChannel = message.server
	send = ''
	if voiceChannel.id in currentSong and currentSong[voiceChannel.id] != '':
		send = 'Current Song: ' + currentSong[voiceChannel.id] + '\n'
	else:
		send = 'Current Song: None \n'
	send = send + '..................Queue..................... \n'
	if voiceChannel.id in musicQueue:
		Queue = musicQueue[voiceChannel.id]
		if len(Queue) > 0:
			for song in Queue:
				send = send + getInfo(song[0]) + '\n'
		else:
			send = send + 'None \n'
	else:
		send = send + 'None \n'
	send = send + '.....................Radio.......................... \n'
	if voiceChannel.id in radioQueue:
		Queue = radioQueue[voiceChannel.id]
		if len(Queue) > 0:
			limit = 0
			for song in Queue:
				if limit <= 8:
					send = send + song[0] + '\n'
					limit = limit + 1
		else:
			send = send + 'None \n'
	else:
		send = send + 'None \n'
	send = send + '....................................................'
	print(send)
	await client.send_message(message.channel, send)

async def leave(message):
	global currentSong
	while downloading == True:
		await asyncio.sleep(10)
	leaving = True
	channel = message.server
	voice_client = client.voice_client_in(channel)
	if channel.id in players:
		if players[channel.id].is_playing():
			players[channel.id].stop()
		players[channel.id] = None
		players.pop(channel.id, None)
	if message.server in voices:
		voices[message.server] = None
		voices.pop(message.server, None)
	if channel.id in musicQueue:
		musicQueue[channel.id] = None
		musicQueue.pop(channel.id, None)
	if channel.id in radioQueue:
		radioQueue[channel.id] = None
		radioQueue.pop(channel.id, None)
	if channel.id in currentSong:
		currentSong[channel.id] = None
		currentSong.pop(channel.id, None)
	if voice_client:
		await voice_client.disconnect()
	leaving = False
	
async def join(message, overide=False):
	try:
		channel = message.author.voice.voice_channel
		if message.server in voices and overide == False:
			print('Already here')
			return 'Already here'
		else:
			voice = await client.join_voice_channel(channel)
			voices[message.server] = voice
			print('Success')
			return 'Successful'
	except Exception as e:
		print(e)
		print('Error joining voice channel')
		printSocket('Error joining voice channel')
		return 'Error'

def getUrl(url):
	match = re.search("(?P<url>https?://[^\s]+)", url)
	if match is not None:
		return match.group("url")
	else:
		return 'Not a link'
		
def pingPC(ip):
	if(len(ip) > 0):
		response = os.system("ping -c 1 " + ip + " >/dev/null 2>&1")
		if response == 0:
			return True
		else:
			return False
	else:
		return False
		
def startPC(ip):
	os.system("wakeonlan " + mcServerMacAddress)
		
def printSocket(message):
	print(message)
	if(len(serverIP) > 0):
		try:
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.connect((serverIP, 5968))
			message = str(message)
			charCount = len(message)
			FinalMessage = "Length: " + str(charCount) + " message: " + message
			s.send(FinalMessage.encode(encoding='ascii'))
			s.close()
		except socket.error as err:
			print("Error sending socket message: " + str(err))

async def clearCommands(message):
	mgs = []
	Num = 1000
	async for x in client.logs_from(message.channel, limit = Num):
		if x.content.startswith("!mc") or x.author == client.user:
			if len(mgs) <= 99:
				mgs.append(x)
				#print(str(x.author) + " " + str(x.content))
			else:
				try:
					await client.delete_messages(mgs)
				except:
					for mg in mgs:
						try:
							await client.delete_message(mg)
						except:
							print('Error Mg to old: ' + mg)
				mgs = []
				mgs.append(x)
				#print(str(x.author) + " " + str(x.content))
	if len(mgs) > 0:
		try:
			await client.delete_messages(mgs)
		except:
			for mg in mgs:
				try:
					await client.delete_message(mg)
				except:
					print('Error Mg to old: ' + mg)
		await client.send_message(message.channel, "MC commands cleared from chat")

def checkPlayers():
	try:
		serverchecker = MinecraftServer(serverIP, mcServerPort)
		status = serverchecker.status()
		return status.players.online
	except:
		return 0
	
def checkServerPower():
	global serverUp
	if pingPC(serverIP) == False:
		serverUp = False

def serverWatcher():
	global serverUp, lastChannel, startingPC, playerCountWatcher, playerWatcherCount
	checkServerPower()
	if startingPC == True:
		if pingPC(serverIP) == True and serverUp == False:
			printSocket("Start Minecraft server")
		elif serverUp == True:
			startingPC = False
	if serverUp == True:
		playerCount = checkPlayers()
		if playerCount <= 0:
			playerShutdown()
		elif playerWatcherCount > 0:
			playerWatcherCount = 0
			print('Some players joined, no longer shutting down!')
	elif serverUp == False and playerWatcherCount > 0:
		playerWatcherCount = 0
	time.sleep(60)
	serverWatcher()
		
def playerShutdown():
	global playerWatcherCount
	if playerWatcherCount == 1:
		print('No players, shutting down in 20 minutes')
	time.sleep(1)
	playerCount = checkPlayers()
	if playerCount <= 0 and playerWatcherCount >= 1200:
		shutdownServer()
		playerWatcherCount = 0
		if(lastChannel is not None):
			client.send_message(lastChannel, "No players shutting down the server")
	else:
		playerWatcherCount = playerWatcherCount + 1
		
def shutdownServer():
	global serverUp
	checkServerPower()
	if serverUp == True:
		printSocket("Shutdown the Minecraft server")
		serverUp = False
		
def messageSetup():
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	address = (botIP, 5968)
	sock.bind(address)
	sock.listen(5)
	messageServer(sock)
	print("Message server started")
		
def messageServer(sock):
	global serverUp
	SockTimeout = False
	connection, clientIP = sock.accept()
	while 1 and SockTimeout == False:
		try:
			data = connection.recv(1024)
			if not data: break
			message = data.decode('utf-8')
			print('Message Recieved: ' + message)
		except socket.timeout:
			SockTimeout = True
	connection.close()
	if SockTimeout == False:
		if message == "Length: 31 message: The Minecraft server is running":
			serverUp = True
			print('Yes the server is running')
		elif message == "Length: 28 message: The Minecraft server is down":
			serverUp = False
			print('No the server is off')
		else:
			print('Unknown message: ' + message)
	messageServer(sock)

messageRecv = Thread(target=messageSetup, args=[])
#messageRecv.start()

time.sleep(10)

checkServer = Thread(target=serverWatcher, args=[])
#checkServer.start()

time.sleep(10)

client.run(botID)
