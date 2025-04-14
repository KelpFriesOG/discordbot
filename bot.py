import discord
from discord.ext import commands
import configparser
import requests
from cogs.events import EventCog
from cogs.moderation import ModerationCog
from cogs.profile import ProfileCog
from cogs.music import MusicCog
from views.profile_view import ProfileModal

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

config = configparser.ConfigParser()
config.read('config.ini')

class MyBot(commands.Bot):
    async def setup_hook(self):
        # Load cogs
        await self.add_cog(ProfileCog(self))
        await self.add_cog(EventCog(self))
        await self.add_cog(ModerationCog(self))
        await self.add_cog(MusicCog(self))
        print("🧠 Cogs loaded in setup_hook")
        print(f"🚀 Total commands: {len(bot.tree.get_commands())}")

        # Sync commands to each guild
        servers = config['discord']['servers'].split(', ')
        for guild_id in servers:
            guild = discord.Object(id=int(guild_id))
            await self.tree.sync(guild=guild)
            print(f"🔁 {len(bot.tree.get_commands(guild=guild))} guild-specific commands synced to guild: {guild_id}")

        # Sync the global commands
        await self.tree.sync()
        print(f"🌎 Global commands synced!")

bot = MyBot(command_prefix='/', intents=intents)

@bot.tree.command(name="query", description="Ask a question and get an answer!")
async def query(interaction: discord.Interaction, question: str):
    await interaction.response.defer()

    headers = {'Content-Type': 'application/json'}
    json_data = {
        'model': 'qwen2.5-coder-3b-instruct',
        'messages': [
            {'role': 'system', 'content': 'Give a short answer to the question.'},
            {'role': 'user', 'content': question},
        ],
        'temperature': 0.7,
        'max_tokens': 256,
        'stream': False,
    }

    try:
        response = requests.post('http://localhost:1234/v1/chat/completions', headers=headers, json=json_data)
        data = response.json()
        answer = data.get('choices', [{}])[0].get('message', {}).get('content', 'No answer found.')
        await interaction.followup.send(f'Answer: {answer}')
    except requests.RequestException as e:
        await interaction.followup.send(f"Error querying the API: {e}")

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}.")

if __name__ == '__main__':
    try:
        secret_key = config['discord']['api_key']
        bot.run(secret_key)
    except KeyError:
        print("Missing 'api_key' in config.ini.")
    except FileNotFoundError:
        print("Missing config.ini file.")
