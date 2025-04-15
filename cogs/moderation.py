from discord.ext import commands
from discord import Member, utils, TextChannel
from discord import app_commands, Interaction

class ModerationCog(commands.Cog):

    def __init__(self, bot):
        super().__init__()
        self.bot = bot
    
    @app_commands.command(name="clear", description="clear up `n_messages` messages in this channel")
    @app_commands.describe(n_messages="The number of previous messages to delete")
    async def clear(self, interaction: Interaction, n_messages: int):

        member = interaction.user if isinstance(interaction.user, Member) else interaction.guild.get_member(interaction.user.id)

        # Ensure the interaction's end user is a guild member
        if not member:
            await interaction.response.send_message("Could not fetch your member info.", ephemeral=True)
            return

        # Check if the user has permission to manage messages
        if not (member.guild_permissions.manage_messages or member.id == interaction.guild.owner_id):
            await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
            return

        # Ensure the command is being used in a text channel        
        if not isinstance(interaction.channel, TextChannel):
            await interaction.response.send_message("This command can only be used in text channels", ephemeral=True)
            return

        # Validate n_messages is in acceptable range
        if n_messages < 1 or n_messages > 100:
            await interaction.response.send_message("Please provide a number between 1 and 100.", ephemeral=True)
            return

        # After validating checks go ahead and delete 'em.
        try:
            await interaction.response.send_message(f"🧹 Deleting {n_messages} messages...", ephemeral=True)
            deleted = await interaction.channel.purge(limit=n_messages + 1)  # +1 to include the command itself if visible
        except Exception as e:
            await interaction.followup.send(f"⚠️ Failed to delete messages: {e}", ephemeral=True)

    