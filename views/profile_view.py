from utils.profile_utils import save_profiles, load_profiles
import discord
from discord.ui import Button, View, TextInput, Modal


class ProfileView(discord.ui.View):
    def __init__(self, button_text: str = "Modify Profile"):
        super().__init__(timeout=None)

        button = Button(
            label = button_text,
            style = discord.ButtonStyle.blurple
        )

        # Callback button to launch modal with it
        button.callback = self.launch_modal
        self.add_item(button)

    async def launch_modal(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ProfileModal())

class ProfileModal(Modal, title="Hello :smile:"):

    def __init__(self, profile_data = None, title = "Modify Profile"):

        super().__init__()

        # Fallback to empty dict if not provided
        profile_data = profile_data or {}

        self.name = TextInput(
            label='Name',
            default=profile_data.get("name", "")
        )
        self.age = TextInput(
            label='Age',
            placeholder='Enter a number',
            default=str(profile_data.get("age", "")) if profile_data.get("age") else ""
        )
        self.hobbies = TextInput(
            label='Hobbies (include games / coding languages)',
            style=discord.TextStyle.paragraph,
            default=profile_data.get("hobbies", "")
        )
        self.answer = TextInput(
            label='Bio',
            style=discord.TextStyle.paragraph,
            default=profile_data.get("bio", "")
        )

        self.title = title
        self.add_item(self.name)
        self.add_item(self.age)
        self.add_item(self.hobbies)
        self.add_item(self.answer)

    async def on_submit(self, interaction: discord.Interaction):
        print("🔥 on_submit triggered")
        await interaction.response.defer(ephemeral=True)

        member = interaction.guild.get_member(interaction.user.id)
        if not member:
            await interaction.followup.send("Couldn't find your member info.", ephemeral=True)
            return

        guild_id = str(interaction.guild_id)
        user_id = str(interaction.user.id)
        profiles = load_profiles()

        # Create new guild entry if not present
        if guild_id not in profiles:
            profiles[guild_id] = {}

        # Validate age
        age_num = None
        warnings = []
        if self.age.value:
            try:
                age_num = int(self.age.value)
            except ValueError:
                warnings.append("⚠️ Age was invalid and not registered.")
                age_num = None  # Just to be explicit

        # Save profile
        profiles[guild_id][user_id] = {
            "name": self.name.value,
            "age": age_num,
            "hobbies": self.hobbies.value,
            "bio": self.answer.value
        }

        nickname_updated = False
        nickname_failed = False

        # Try nickname change (skip for owner)
        if interaction.user.id == interaction.guild.owner_id:
            warnings.append("ℹ️ You're the server owner, so I can't change your nickname.")
        else:
            try:
                await member.edit(nick=self.name.value, reason="Profile update")
                nickname_updated = True
            except discord.Forbidden:
                nickname_failed = True
                warnings.append("⚠️ I don't have permission to change your nickname.")

        save_profiles(profiles)

        # Role auto-assignment
        roles_to_check = {
            "Valorant": ["valorant", "valo"],
            "League of Legends": ["league", "league of legends"],
            "Python": ["python"],
            "JavaScript": ["javascript", "js"],
            "Artist": ["draw", "art", "sketch"],
            "Gamer": ["game", "gamer"],
            "Coder": ["code", "developer", "program"]
        }

        matched_roles = set()
        profile_data = profiles.get(str(interaction.guild.id), {}).get(str(interaction.user.id), {})
        text = (profile_data.get("hobbies", "") + " " + profile_data.get("bio", "")).lower()

        for role_name, keywords in roles_to_check.items():
            if any(keyword in text for keyword in keywords):
                matched_roles.add(role_name)

        assigned = []
        for role_name in matched_roles:
            role = discord.utils.get(interaction.guild.roles, name=role_name)
            if role:
                try:
                    await member.add_roles(role)
                    assigned.append(role.name)
                except discord.Forbidden:
                    warnings.append(f"⚠️ Couldn't assign role: {role.name}")

        # Build the final message
        lines = ["✅ Your profile is saved!"]

        if nickname_updated:
            lines.append(f"📝 Nickname updated to `{self.name.value}`")

        lines.append(f"🎭 Roles assigned: {', '.join(assigned) if assigned else 'None'}")

        if warnings:
            lines.append("\n❗ Notes:")
            lines.extend(warnings)

        await interaction.followup.send("\n".join(lines), ephemeral=True)


    async def on_cancel(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"That's fine, you can continue setting up your profile at any time using /profile! :smile:")