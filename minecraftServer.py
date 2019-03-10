from threading import Thread
import asyncio, time, os, subprocess, socket, sys

serverUp = False
server = None

botLocalIP = ''
serverLocalIP = ''

def messageSetup():
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	address = (serverLocalIP, 5968)
	sock.bind(address)
	sock.listen(5)
	print('Message server started')
	messageServer(sock)
		
def messageServer(sock):
	connection, clientIP = sock.accept()
	while 1:
		data = connection.recv(1024)
		if not data: break
		message = data.decode('utf-8')
		print('Message Recieved: ' + message)
	connection.close()
	if message == "Length: 22 message: Start Minecraft server":
		startupServer()
	elif message == "Length: 29 message: Shutdown the Minecraft server":
		shutdownServer()
	elif message == "Length: 31 message: Is the Minecraft server running":
		checkServerPower()
		if serverUp == True:
			printSocket("The Minecraft server is running")
		else:
			printSocket("The Minecraft server is down")
	else:
		print('Unknown message: ' + message)
	messageServer(sock)
		
def printSocket(message):
	print(message)
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((botLocalIP, 5968))
		message = str(message)
		charCount = len(message)
		FinalMessage = "Length: " + str(charCount) + " message: " + message
		s.send(FinalMessage.encode(encoding='ascii'))
		s.close()
	except socket.error as err:
		print("Error sending socket message: " + str(err))
		
def startupServer():
	global server, serverUp
	#MAKE SURE THIS COMMAND IS CORRECT FOR YOUR SITUATION
	server = subprocess.Popen('java -Xms1024M -Xmx2048M -jar server.jar', stdin=subprocess.PIPE, cwd="D:/Servers/Minecraft/Vanilla")
	serverUp = True
	printSocket('The Minecraft server is running')
		
def checkServerPower():
	global server, serverUp
	if server is not None:
		if server.poll() is None:
			serverUp = True
		else:
			serverUp = False
	else:
		serverUp = False
		
def shutdownServer():
	global server, serverUp
	checkServerPower()
	if serverUp == True:
		server.stdin.write(bytes("stop\r\n", "ascii"))
		server.stdin.flush()
		serverUp = False
		print('Server Shutting Down')

messageSetup()