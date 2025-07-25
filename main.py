# main.py
import discord
from discord import app_commands
from typing import Optional

# Importa as funções de setup
from goodmorning import setup_goodmorning_command
from staff_commands import setup_staff_commands
from bot_commands import setup_bot_commands
from help_command import setup_help_command
from embed_builder_command import setup_embed_builder_command
from bot_config import bot_config
from automod_system import automod # <-- MUDANÇA AQUI: Importa a instância global

# Substitua 'SEU_TOKEN_AQUI' pelo token do seu bot
TOKEN = 'token'

intents = discord.Intents.default()
intents.message_content = True 
intents.guilds = True 
intents.members = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# REMOVIDO: A instância agora é global no automod_system.py
# automod = AutoModSystem(client)

@client.event
async def on_ready():
    print(f'Bot logado como {client.user}')

    # --- MUDANÇA: Atribui o client à instância global do automod ---
    automod.client = client
    
    try:
        presence_data = bot_config.get_presence()
        if presence_data:
            status_map = {"online": discord.Status.online, "idle": discord.Status.idle, "dnd": discord.Status.dnd, "invisible": discord.Status.invisible}
            activity = None
            act_type = presence_data.get("activity_type")
            act_name = presence_data.get("name")
            act_url = presence_data.get("url")
            act_emoji = presence_data.get("emoji")
            if act_type and act_name:
                if act_type == "playing": activity = discord.Game(name=act_name)
                elif act_type == "listening": activity = discord.Activity(type=discord.ActivityType.listening, name=act_name)
                elif act_type == "watching": activity = discord.Activity(type=discord.ActivityType.watching, name=act_name)
                elif act_type == "streaming" and act_url: activity = discord.Streaming(name=act_name, url=act_url)
                elif act_type == "custom": activity = discord.CustomActivity(name=act_name, emoji=act_emoji)
            saved_status = presence_data.get("status")
            if saved_status and saved_status in status_map:
                await client.change_presence(status=status_map[saved_status], activity=activity)
                print("Status e atividade anteriores carregados.")
    except Exception as e:
        print(f"Não foi possível carregar o status salvo: {e}")
    
    # Configura todos os grupos de comandos
    setup_goodmorning_command(tree)
    setup_staff_commands(tree, client)
    setup_bot_commands(tree, client)
    setup_help_command(tree)
    setup_embed_builder_command(tree)
    
    print("Bot pronto para receber comandos.")

@client.event
async def on_message(message: discord.Message):
    await automod.check_message(message)

class HelloView(discord.ui.View):
    def __init__(self, user_mention: str):
        super().__init__(timeout=300)
        self.user_mention = user_mention
        self.is_english = False
        link_button = discord.ui.Button(label="🔗 Active Developer", style=discord.ButtonStyle.link, url="https://discord.com/developers/active-developer")
        self.add_item(link_button)
    
    def create_embed(self):
        if self.is_english:
            embed = discord.Embed(title="<:pepeflor:1387159299700035646> Hello!", description=f"Hello, {self.user_mention}! I'm Canary, **your assistant**.", color=0x2F3136)
            embed.add_field(name="<:pepefeliz:1387160182634713199> Congratulations!", value="Now that you've used a command, you'll keep your Active Developer badge!", inline=False)
            embed.set_footer(text="Thank you. I'm here for any questions.")
        else:
            embed = discord.Embed(title="<:pepeflor:1387159299700035646> Olá!", description=f"Olá, {self.user_mention}! Eu sou o Canary, **seu ajudante**.", color=0x2F3136)
            embed.add_field(name="<:pepefeliz:1387160182634713199> Parabéns!", value="Agora que você deu um comando, você vai manter sua badge de Active Developer!", inline=False)
            embed.set_footer(text="Obrigado. Estou aqui para qualquer dúvida.")
        return embed
    
    @discord.ui.button(label="🌐 English", style=discord.ButtonStyle.secondary, emoji="🔄")
    async def translate_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.is_english = not self.is_english
        if self.is_english: button.label = "🌐 Português"
        else: button.label = "🌐 English"
        embed = self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

@tree.command(name="hello", description="Ative sua badge de graça! 🎉")
async def hello_command(interaction: discord.Interaction):
    view = HelloView(interaction.user.mention)
    embed = view.create_embed()
    if client.user.avatar: embed.set_thumbnail(url=client.user.avatar.url)
    if interaction.user.avatar: embed.set_footer(text=embed.footer.text, icon_url=interaction.user.avatar.url)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

client.run(TOKEN)