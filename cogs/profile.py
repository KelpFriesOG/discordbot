from discord.ext import commands
from discord import app_commands, Interaction
from views.profile_view import ProfileModal
from utils.profile_utils import *

class ProfileCog(commands.Cog):

    # Constructor
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="modify_profile", description="Change your profile")
    async def modify_profile(self, interaction: Interaction):
        try:
            profiles = load_profiles()
            existing_profile = profiles.get(str(interaction.guild.id), {}).get(str(interaction.user.id), {})
            await interaction.response.send_modal(ProfileModal(profile_data=existing_profile))
        except Exception as e:
            print("Encountered an error", e)
