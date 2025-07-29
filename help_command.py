# help_command.py
import discord
from discord import ui, app_commands
from typing import Union

# Central de registro para categorizar os comandos automaticamente
COMMAND_CATEGORIES = {
    "misc": ["daily", "perfil", "ranking", "hello"],
    "interactions": ["interagir"],
    "marriage": ["casar", "divorciar"],
    "staff": [
        "addcoins", "warn", "warns", "ban", "kick", "mute", 
        "clear", "serverinfo", "setlogchannel", "removelogchannel",
        "embed"
    ],
    "bot_config": ["setstatus", "clearactivity", "sync", "customstatus"]
}

# Detalhes para a formatação de cada categoria no embed
CATEGORY_DETAILS = {
    "misc": {"emoji": "🎲", "title": "Comandos de Miscelânea"},
    "interactions": {"emoji": "💖", "title": "Comandos de Interação"},
    "marriage": {"emoji": "💍", "title": "Comandos de Casamento"},
    "staff": {"emoji": "🛡️", "title": "Comandos de Staff"},
    "bot_config": {"emoji": "🤖", "title": "Comandos de Configuração do Bot"}
}

class HelpView(ui.View):
    def __init__(self, tree: app_commands.CommandTree, original_interaction: discord.Interaction):
        super().__init__(timeout=180)
        self.tree = tree
        self.original_interaction = original_interaction
        self.all_commands = {cmd.name: cmd for cmd in tree.get_commands()}

        self.add_item(self.create_home_button())
        
        for category_id, details in CATEGORY_DETAILS.items():
            if category_id in ["staff", "bot_config"] and not self.is_staff(original_interaction.user):
                continue
            self.add_item(self.create_category_button(
                label=details["title"].replace("Comandos de ", ""),
                emoji=details["emoji"],
                custom_id=category_id
            ))

    def is_staff(self, member: Union[discord.Member, discord.User]) -> bool:
        if isinstance(member, discord.User): return False
        return member.guild_permissions.manage_guild

    def create_category_button(self, label: str, emoji: str, custom_id: str):
        button = ui.Button(label=label, emoji=emoji, style=discord.ButtonStyle.secondary, custom_id=custom_id)
        button.callback = self.show_category
        return button

    def create_home_button(self):
        button = ui.Button(label="Início", emoji="🏠", style=discord.ButtonStyle.primary, custom_id="home")
        button.callback = self.show_home
        return button

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.original_interaction.user.id:
            await interaction.response.send_message("Você não pode controlar este painel de ajuda.", ephemeral=True)
            return False
        return True

    def get_home_embed(self):
        embed = discord.Embed(
            title="👋 Central de Ajuda do Bot",
            description="Olá! Sou seu bot assistente, pronto para ajudar.\n\n"
                        "Use os botões abaixo para navegar pelas categorias e descobrir todos os comandos disponíveis.",
            color=0x5865F2
        )
        embed.set_footer(text="Selecione uma categoria para ver os comandos.")
        return embed

    async def show_home(self, interaction: discord.Interaction):
        embed = self.get_home_embed()
        await interaction.response.edit_message(embed=embed)

    def format_command(self, cmd: app_commands.Command | app_commands.Group) -> str:
        def format_params(parameters):
            if not parameters: return ""
            param_parts = [f"<{p.display_name}>" if p.required else f"[{p.display_name}]" for p in parameters]
            return " " + " ".join(param_parts)

        if isinstance(cmd, app_commands.Group):
            group_desc = f"`/{cmd.name}` - {cmd.description}"
            subcommands_desc = [f"**└** `/{cmd.name} {sub_cmd.name}{format_params(sub_cmd.parameters)}`\n   *↳ {sub_cmd.description}*" for sub_cmd in cmd.commands]
            return group_desc + "\n" + "\n".join(subcommands_desc)

        return f"`/{cmd.name}{format_params(cmd.parameters)}` - {cmd.description}"

    async def show_category(self, interaction: discord.Interaction):
        category_id = interaction.data['custom_id']
        details = CATEGORY_DETAILS.get(category_id)
        
        embed = discord.Embed(title=details['title'], color=0x5865F2)
        
        command_names_in_category = COMMAND_CATEGORIES.get(category_id, [])
        description_lines = [self.format_command(command) for cmd_name in command_names_in_category if (command := self.all_commands.get(cmd_name))]
        
        embed.description = "\n\n".join(description_lines) if description_lines else "Nenhum comando encontrado."
            
        embed.set_footer(text="Use os botões para navegar ou volte para o início.")
        await interaction.response.edit_message(embed=embed)

def setup_help_command(tree: app_commands.CommandTree):
    @tree.command(name="help", description="Mostra a lista de todos os comandos disponíveis.")
    async def help_command(interaction: discord.Interaction):
        view = HelpView(tree, interaction)
        embed = view.get_home_embed()
        if interaction.client.user.avatar:
            embed.set_thumbnail(url=interaction.client.user.avatar.url)
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)