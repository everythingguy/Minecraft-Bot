This is a discord bot that can play music and start a minecraft server off of a computer. The minecraft server must be setup like normal and then change the command in minecraftServer.py to work.

Install dependences with the following command
python -m pip install -r requirements.txt

minecraftServer.py runs on the computer that has the mc server on it (in my case my desktop)
minecraftBot.py runs on the computer you want to run the bot (I used a raspberry pi)

commands
..............
!mc start - start the minecraft server 
!mc stop - stop the Minecraft server 
!mc player count - get the amount of players on the Minecraft server 
!mc status - check to see if the Minecraft server is up 
!mc clear - clears commands from chat 
!mc radio [-s -p] <band name/Playlist URL> - to play a playlist of the bands songs, use the -s tag to shuffle the playlist and/or the -p tag to pick a random playlist instead of the first one on YT 
!mc radio playlist - play the server playlist 
!mc radio off - turn off radio 
!mc playlist - edit the server playlist 
!mc play [-o] <song name/link> - play a song from YouTube, add the -o tag to get options of songs to pick 
!mc leave - tells the bot to leave the voice channel 
!mc queue - Gets the current lineup of songs 
!mc skip - skips the current song 
!mc triggers - Show audio triggers and help on how to make one 
