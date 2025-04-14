import discord
from discord.ext import commands
from discord import app_commands, ui, Interaction
import asyncio
import yt_dlp as youtube_dl
import datetime
from discord.voice_client import VoiceClient

class MusicControlsView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    def set_cog(self, music_cog):
        self.music_cog = music_cog
        return self
    
    @ui.button(label="Pause / Resume", style=discord.ButtonStyle.blurple)
    async def pause_resume(self, interaction: Interaction, button: ui.Button):
        
        vc_client = interaction.guild.voice_client
        
        if not vc_client:
            await interaction.response.send_message("Bot is not connected to a voice channel.")
            return
        
        if vc_client.is_paused():
            vc_client.resume()
            await interaction.response.send_message("▶️ Resumed playback", ephemeral=True)
        else:
            vc_client.pause()
            await interaction.response.send_message("⏸️ Paused playback", ephemeral=True)
    
    @ui.button(label="Skip", style=discord.ButtonStyle.primary, emoji="⏭️")
    async def skip(self, interaction: discord.Interaction, button: ui.Button):
        
        vc_client = interaction.guild.voice_client
        
        if not vc_client:
            await interaction.response.send_message("Bot is not connected to a voice channel.", ephemeral=True)
            return
            
        if vc_client.is_playing():
            vc_client.stop()
            await interaction.response.send_message("⏭️ Skipped track", ephemeral=True)
        else:
            await interaction.response.send_message("Nothing is playing right now.", ephemeral=True)

    @ui.button(label="Volume Down", style=discord.ButtonStyle.secondary, emoji="🔉")
    async def volume_down(self, interaction: discord.Interaction, button: ui.Button):
        
        guild_id = interaction.guild.id
        if not hasattr(self, 'music_cog') or not self.music_cog:
            await interaction.response.send_message("Controls not properly initialized.", ephemeral=True)
            return
            
        if guild_id in self.music_cog.players:
            current_volume = self.music_cog.players[guild_id]['volume']
            new_volume = max(0.0, current_volume - 0.1)
            self.music_cog.players[guild_id]['volume'] = new_volume
            
            voice_client = interaction.guild.voice_client
            if voice_client and voice_client.source:
                voice_client.source.volume = new_volume
                
            await interaction.response.send_message(f"🔉 Volume set to {int(new_volume * 100)}%", ephemeral=True)
        else:
            await interaction.response.send_message("No active player.", ephemeral=True)

    @ui.button(label="Volume Up", style=discord.ButtonStyle.secondary, emoji="🔊")
    async def volume_up(self, interaction: discord.Interaction, button: ui.Button):
        
        guild_id = interaction.guild.id
        if not hasattr(self, 'music_cog') or not self.music_cog:
            await interaction.response.send_message("Controls not properly initialized.", ephemeral=True)
            return
            
        if guild_id in self.music_cog.players:
            current_volume = self.music_cog.players[guild_id]['volume']
            new_volume = min(1.0, current_volume + 0.1)
            self.music_cog.players[guild_id]['volume'] = new_volume
            
            voice_client = interaction.guild.voice_client
            if voice_client and voice_client.source:
                voice_client.source.volume = new_volume
                
            await interaction.response.send_message(f"🔊 Volume set to {int(new_volume * 100)}%", ephemeral=True)
        else:
            await interaction.response.send_message("No active player.", ephemeral=True)

    @ui.button(label="Queue", style=discord.ButtonStyle.success, emoji="📋")
    async def show_queue(self, interaction: discord.Interaction, button: ui.Button):
        
        if not hasattr(self, 'music_cog') or not self.music_cog:
            await interaction.response.send_message("Controls not properly initialized.", ephemeral=True)
            return
            
        guild_id = interaction.guild.id
        if guild_id not in self.music_cog.queues or not self.music_cog.queues[guild_id]:
            await interaction.response.send_message("Queue is empty.", ephemeral=True)
            return
            
        queue = self.music_cog.queues[guild_id]
        
        embed = discord.Embed(title="Current Queue", color=discord.Color.blue())
        
        for i, track in enumerate(queue[:10]):  # Show first 10 items
            embed.add_field(
                name=f"{i+1}. {track['title']}",
                value=f"Duration: {track.get('duration', 'Unknown')} | Requested by: {track.get('requester', 'Unknown')}",
                inline=False
            )
            
        if len(queue) > 10:
            embed.set_footer(text=f"And {len(queue) - 10} more songs in queue")
            
        await interaction.response.send_message(embed=embed, ephemeral=True)