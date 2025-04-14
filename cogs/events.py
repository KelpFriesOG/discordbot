from discord.ext import commands
from discord import Member
from views.profile_view import ProfileView

class EventCog(commands.Cog):

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: Member):
        guild_name = member.guild.name  # 👈 get the server's name
        try:
            view = ProfileView()
            await member.send(
                f"👋 Welcome to **{guild_name}**, {member.name}!\n\n"
                "We're happy to have you here. Feel free to click the button below to tell us a bit about yourself — it's optional, but helps us get to know you better!",
                view=view
            )
        except Exception as e:
            print(f"⚠️ Failed to DM {member.name}: {e}")
