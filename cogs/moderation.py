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

        if not member:
            await interaction.response.send_message("Could not fetch your member info.", ephemeral=True)
            return
        
        has_role = utils.get(member.roles, name="moderator")
        is_owner = member.id == interaction.guild.owner_id

        if not (has_role or is_owner):
            await interaction.reponse.send_message("You don't have permission to use this command")
            return

        if not isinstance(interaction.channel, TextChannel):
            await interaction.response.send_message("This command can only be used in text channels")
            return

        # Delete some messages
        await interaction.response.send_message(f"🧹 Deleting {n_messages} messages.", ephemeral=True)
        deleted_messages = await interaction.channel.purge(limit=n_messages+1)