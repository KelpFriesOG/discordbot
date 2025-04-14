# cogs/music.py
import asyncio
import datetime
import discord
from discord.ext import commands
from discord import app_commands
from utils.playlist_utils import save_playlists, load_playlists
from views.music_controls_view import MusicControlsView
import yt_dlp as youtube_dl

# YouTube DL options
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': True,  # Allow skipping bad entries if needed
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'force-ipv4': True,  # Helps with YouTube DNS issues sometimes
    'external_downloader_args': [
        '-reconnect', '1',
        '-reconnect_streamed', '1',
        '-reconnect_delay_max', '5'
    ]
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.duration = self._format_duration(data.get('duration', 0))
        self.thumbnail = data.get('thumbnail')
        self.requester = None

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=True):
        ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    
    @classmethod
    async def from_url(cls, url, loop=None, stream=True):
        data = await loop.run_in_executor(
            None, lambda: ytdl.extract_info(url, download=not stream)
        )

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(
            discord.FFmpegPCMAudio(filename, **ffmpeg_options),
            volume=0.5,
        )

    
    def _format_duration(self, duration):
        if not duration:
            return "Unknown"
        return str(datetime.timedelta(seconds=duration))

class MusicCog(commands.Cog):
    
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.queues = {}  # Guild ID -> list of tracks
        self.players = {}  # Guild ID -> player info (volume, etc.)
        self.current_sources = {}
        # Create the controls view and link it to this cog
        self.controls = MusicControlsView().set_cog(self)

    # Core commands

    @app_commands.command(name="join_channel", description="Make the bot join your current voice channel")
    async def join(self, interaction: discord.Interaction):
        voice_state = interaction.user.voice
        if not voice_state or not voice_state.channel:
            await interaction.response.send_message("❌ You need to be in a voice channel first.", ephemeral=True)
            return

        channel = voice_state.channel
        
        # If bot is already in a voice channel, move it
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.move_to(channel)
        else:
            await channel.connect()
        
        # Initialize player data for this guild if it doesn't exist
        guild_id = interaction.guild.id
        if guild_id not in self.players:
            self.players[guild_id] = {
                'volume': 0.5,  # Default volume: 50%
            }
        
        await interaction.response.send_message(f"✅ Joined {channel.name}!")

    @app_commands.command(name="leave_channel", description="Make the bot leave the voice channel")
    async def leave(self, interaction: discord.Interaction):
        if interaction.guild.voice_client:
            guild_id = interaction.guild.id
            
            # Clear the queue if it exists
            if guild_id in self.queues:
                self.queues[guild_id].clear()
                
            await interaction.guild.voice_client.disconnect()
            await interaction.response.send_message("👋 Disconnected from the voice channel.")
        else:
            await interaction.response.send_message("❌ I'm not in a voice channel.")

    @app_commands.command(name="play_url", description="Play a song from URL or search term")
    @app_commands.describe(query="YouTube URL or search term")
    async def play(self, interaction: discord.Interaction, query: str):
        voice_state = interaction.user.voice
        
        if not voice_state or not voice_state.channel:
            await interaction.response.send_message("❌ You need to be in a voice channel first.", ephemeral=True)
            return
            
        voice_client = interaction.guild.voice_client
        
        # Join the user's voice channel if not already connected
        if not voice_client:
            voice_client = await voice_state.channel.connect()
            
        guild_id = interaction.guild.id
        
        # Initialize guild data if it doesn't exist
        if guild_id not in self.queues:
            self.queues[guild_id] = []
            
        if guild_id not in self.players:
            self.players[guild_id] = {
                'volume': 0.5,  # Default volume: 50%
            }
            
        # Defer response since downloading metadata might take time
        await interaction.response.defer(ephemeral=False, thinking=True)
        
        try:
            # Extract info without downloading to get metadata
            loop = asyncio.get_event_loop()
            
            # Use run_in_executor to avoid blocking the bot
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(query, download=False))
            
            if 'entries' in data:
                # Take first item from a playlist
                data = data['entries'][0]
                
            # Add track to queue with additional info
            track_info = {
                'url': data['webpage_url'],
                'title': data['title'],
                'duration': str(datetime.timedelta(seconds=data.get('duration', 0))),
                'thumbnail': data.get('thumbnail', None),
                'requester': interaction.user.display_name
            }
            
            self.queues[guild_id].append(track_info)
            
            embed = discord.Embed(
                title="Added to Queue",
                description=f"[{track_info['title']}]({track_info['url']})",
                color=discord.Color.green()
            )
            
            embed.add_field(name="Duration", value=track_info['duration'], inline=True)
            embed.add_field(name="Requested by", value=track_info['requester'], inline=True)
            
            if track_info['thumbnail']:
                embed.set_thumbnail(url=track_info['thumbnail'])
                
            # If this is the only song in queue and nothing is playing, start playback
            if len(self.queues[guild_id]) == 1 and not voice_client.is_playing():
                await self._play_next(guild_id, interaction)
                embed.set_author(name="Now Playing")
            else:
                position = len(self.queues[guild_id])
                embed.set_footer(text=f"Position in queue: {position}")
                
            await interaction.followup.send(embed=embed, view=self.controls)
            print(f"Queue: {self.queues[guild_id]}")

        except Exception as e:
            await interaction.followup.send(f"❌ Error processing your request: {str(e)}")

    @app_commands.command(name="save_queue_as_playlist", description="Save current queue as a playlist")
    @app_commands.describe(name="name for the saved playlist")
    async def save_playlist(self, interaction: discord.Interaction, name: str):
        guild_id = interaction.guild.id
        str_guild_id = str(guild_id)

        queue = self.queues.get(guild_id)
        if not isinstance(queue, list) or not any('url' in track for track in queue):
            await interaction.response.send_message("Queue is empty or invalid - nothing to save.", ephemeral=True)
            return

        playlists = load_playlists()

        if str_guild_id not in playlists:
            playlists[str_guild_id] = {}

        # Save full metadata for each track
        playlists[str_guild_id][name] = queue

        save_playlists(playlists)
        await interaction.response.send_message(f"✅ Saved current queue as playlist: `{name}`", ephemeral=True)


    @app_commands.command(name="load_playlist", description="Load a saved playlist")
    @app_commands.describe(name="name of the playlist to load")
    async def load_playlist(self, interaction: discord.Interaction, name: str):
        guild_id = interaction.guild.id
        str_guild_id = str(guild_id)

        playlists = load_playlists()

        if str_guild_id not in playlists or name not in playlists[str_guild_id]:
            await interaction.response.send_message(f"❌ No playlist found with name: `{name}`", ephemeral=True)
            return

        if guild_id not in self.queues:
            self.queues[guild_id] = []

        was_empty = len(self.queues[guild_id]) == 0

        # Append full track metadata
        self.queues[guild_id].extend(playlists[str_guild_id][name])

        await interaction.response.send_message(f"✅ Loaded playlist: `{name}` ({len(playlists[str_guild_id][name])} tracks)")

        voice_client = interaction.guild.voice_client
        if was_empty and voice_client and not voice_client.is_playing():
            await self._play_next(guild_id, interaction)


    
    # Additional commands...
    @app_commands.command(name="show_music_controls", description="Show music player controls")
    async def controls_command(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        voice_client = interaction.guild.voice_client
        
        if not voice_client or not voice_client.is_connected():
            await interaction.response.send_message("I'm not currently in a voice channel.", ephemeral=True)
            return
            
        embed = discord.Embed(
            title="Music Player Controls",
            description="Use the buttons below to control playback",
            color=discord.Color.blue()
        )
        
        # Add info about current song if playing
        if guild_id in self.queues and self.queues[guild_id] and voice_client.is_playing():
            current_track = self.queues[guild_id][0]
            embed.add_field(
                name="Now Playing",
                value=f"[{current_track['title']}]({current_track['url']})",
                inline=False
            )
            
            if current_track.get('thumbnail'):
                embed.set_thumbnail(url=current_track['thumbnail'])
        
        # Add volume information
        if guild_id in self.players:
            volume = self.players[guild_id]['volume']
            embed.add_field(name="Current Volume", value=f"{int(volume * 100)}%", inline=True)
        
        await interaction.response.send_message(embed=embed, view=self.controls)

    async def _play_next(self, guild_id, interaction: discord.Interaction):
        """Internal method to play the next song in queue"""
        if guild_id not in self.queues or not self.queues[guild_id]:
            return  # Queue is empty

        voice_client = self.bot.get_guild(guild_id).voice_client
        if not voice_client:
            member = self.bot.get_guild(guild_id).get_member(interaction.user.id)
            if not member or not member.voice or not member.voice.channel:
                print("❌ Cannot find a valid voice channel to join.")
                return
            voice_client = await member.voice.channel.connect()
        elif voice_client.is_playing() or voice_client.is_paused():
            voice_client.stop()

        # Get the next track info
        track_info = self.queues[guild_id][0]

        try:
            source = await YTDLSource.from_url(track_info['url'], loop=self.bot.loop)
            source.requester = track_info['requester']

            volume = self.players[guild_id]['volume']
            source.volume = volume

            def after_playing(error):
                if error:
                    print(f"Player error: {error}")
                if guild_id in self.queues and self.queues[guild_id]:
                    self.queues[guild_id].pop(0)
                asyncio.run_coroutine_threadsafe(
                    self._play_next(guild_id, interaction),
                    self.bot.loop
                )

            voice_client.play(source, after=after_playing)
            self.current_sources[guild_id] = source


        except Exception as e:
            print(f"Error playing song: {e}")
            if guild_id in self.queues and self.queues[guild_id]:
                self.queues[guild_id].pop(0)
            await self._play_next(guild_id, interaction)




