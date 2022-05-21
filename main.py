import asyncio
import discord
from discord.ext import commands, tasks
from discord.voice_client import VoiceClient
import youtube_dl
from random import choice

youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume = 0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop = None, stream = False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download = not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data = data)

def is_connected(ctx):
    voice_client = ctx.message.guild.voice_client
    return voice_client and voice_client.is_connected()

client = commands.Bot(command_prefix = '!')

status = 'music!'
queue = []
loop = False

@client.event
async def on_ready():
    await client.change_presence(activity = discord.Game(status))
    print('Bot is online!')

@client.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.channels, name = 'general')
    await channel.send(f'{member.mention}, welcome to the server!')

@client.command(name = 'hello', help = 'Sends a random \"hello\" message')
async def hello(ctx):
    replies = ['yooo what\'s up', 'nice to see you back', 'how\'s the day goin\'', 'Hi!!!']
    await ctx.send(choice(replies))

@client.command(name = 'ping', help = 'Shows the latency.')
async def ping(ctx):
    await ctx.send(f'Ping: {round(client.latency * 1000)}ms.')

@client.command(name = 'join', help = 'Bot joins the voice channel.')
async def join(ctx):
    if not ctx.message.author.voice:
        await ctx.send('Connect to a voice channel and try using this command again!')
        return
    
    else:
        channel = ctx.message.author.voice.channel

    await channel.connect()

@client.command(name = 'leave', help = 'Bot leaves the voice channel.')
async def leave(ctx):
    voice_client = ctx.message.guild.voice_client
    await voice_client.disconnect()

@client.command(name = 'queue', help = 'Adds a song to the queue.')
async def queue_(ctx, *, url):
    global queue

    queue.append(url)
    await ctx.send(f'**{url}** added to the queue!')

@client.command(name = 'remove', help = 'Removes an index from the queue.')
async def remove(ctx, number):
    global queue

    try:
        del(queue[int(number)])
        if len(queue):
            await ctx.send(f'Queue is now **{queue}**!')
        else:
            await ctx.send(f'Queue is cleared!')
    
    except:
        await ctx.send('Empty queue or index not valid!')

@client.command(name = 'view', help = 'Shows the queue.')
async def view(ctx):
    await ctx.send(f'Your queue is now **{queue}**!')

@client.command(name = 'loop', help = 'Toggles loop mode.')
async def loop_(ctx):
    global loop

    if loop:
        await ctx.send('Loop mode is now **off**!')
        loop = False
    
    else: 
        await ctx.send('Loop mode is now **on**')
        loop = True

@client.command(name = 'play', help = 'Plays songs.')
async def play(ctx):
    global queue

    if not ctx.message.author.voice:
        await ctx.send('Connect to a voice channel and try using this command again!')
        return
    
    elif len(queue) == 0:
        await ctx.send('Queue is empty!')

    else:
        try:
            channel = ctx.message.author.voice.channel
            await channel.connect()
        except: 
            pass

    server = ctx.message.guild
    voice_channel = server.voice_client
    while queue:
        try:
            while voice_channel.is_playing() or voice_channel.is_paused():
                await asyncio.sleep(2)
                pass

        except AttributeError:
            pass
        
        try:
            async with ctx.typing():
                player = await YTDLSource.from_url(queue[0], loop = client.loop)
                voice_channel.play(player, after=lambda e: print('Player error: %s' % e) if e else None)
                
                if loop:
                    queue.append(queue[0])

                del(queue[0])
                
            await ctx.send('Now playing: **{}**'.format(player.title))

        except:
            break

client.run('OTY1NjE5MjgwMjE1NDA4NjYy.GejTd7.PwaxrdcnkjPn9vUNk7Tguimojc_09Dm3aUdQ9M')