# bot_commands.py
import discord
from discord import app_commands
from typing import Optional
from bot_config import bot_config
from staff_commands import staff_system

def setup_bot_commands(tree: app_commands.CommandTree, client: discord.Client):
    
    # --- NOVO COMANDO PARA STATUS PERSONALIZADO ---
    @tree.command(name="customstatus", description="👑 [Dono] Define um status personalizado para o bot.")
    @app_commands.describe(
        texto="A mensagem que aparecerá no status.",
        emoji="[Opcional] O emoji que aparecerá ao lado do texto."
    )
    async def custom_status(interaction: discord.Interaction, texto: str, emoji: Optional[str] = None):
        if not staff_system.is_staff(interaction.user):
            return await interaction.response.send_message("❌ Apenas membros da Staff podem usar este comando.", ephemeral=True)
            
        try:
            # Pega o status atual para não alterá-lo (Online, Ausente, etc)
            current_status_str = bot_config.get_presence().get('status', 'online')
            status_map = {"online": discord.Status.online, "idle": discord.Status.idle, "dnd": discord.Status.dnd, "invisible": discord.Status.invisible}
            current_status = status_map.get(current_status_str, discord.Status.online)
            
            # Cria a atividade personalizada
            activity = discord.CustomActivity(name=texto, emoji=emoji)
            
            await client.change_presence(status=current_status, activity=activity)
            
            # Salva a nova configuração
            bot_config.set_presence(current_status_str, "custom", texto, emoji=emoji)
            
            embed = discord.Embed(title="✅ Status Personalizado Definido!", description=f"O status foi alterado para: {emoji or ''} {texto}", color=0x00FF00)
            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            embed = discord.Embed(title="❌ Erro", description=f"Ocorreu um erro ao definir o status personalizado: {e}", color=0xFF0000)
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @tree.command(name="setstatus", description="👑 [Dono] Altera o status e a atividade do bot (Jogando, etc.).")
    @app_commands.describe(
        status="O status do bot (online, ausente, etc.)",
        activity_type="[Opcional] O tipo de atividade (jogando, ouvindo, etc.)",
        texto="[Opcional] O texto que aparecerá na atividade.",
        url_stream="[Opcional] URL da live (apenas para atividade 'Streaming')."
    )
    @app_commands.choices(
        status=[app_commands.Choice(name="Online", value="online"), app_commands.Choice(name="Ausente (Idle)", value="idle"), app_commands.Choice(name="Não Perturbar (DND)", value="dnd"), app_commands.Choice(name="Invisível", value="invisible")],
        activity_type=[app_commands.Choice(name="Jogando", value="playing"), app_commands.Choice(name="Ouvindo", value="listening"), app_commands.Choice(name="Assistindo", value="watching"), app_commands.Choice(name="Streaming", value="streaming")]
    )
    async def set_status(
        interaction: discord.Interaction, 
        status: app_commands.Choice[str], 
        activity_type: Optional[app_commands.Choice[str]] = None,
        texto: Optional[str] = None,
        url_stream: Optional[str] = None
    ):
        if not staff_system.is_staff(interaction.user):
            return await interaction.response.send_message("❌ Apenas membros da Staff podem usar este comando.", ephemeral=True)
        if activity_type and not texto:
            return await interaction.response.send_message("❌ Se você define um tipo de atividade, você também precisa fornecer um texto para ela.", ephemeral=True)
        if activity_type and activity_type.value == "streaming" and not url_stream:
            return await interaction.response.send_message("❌ Para a atividade 'Streaming', você precisa fornecer uma URL válida.", ephemeral=True)

        status_map = {"online": discord.Status.online, "idle": discord.Status.idle, "dnd": discord.Status.dnd, "invisible": discord.Status.invisible}
        activity = None
        if activity_type and texto:
            if activity_type.value == "playing": activity = discord.Game(name=texto)
            elif activity_type.value == "listening": activity = discord.Activity(type=discord.ActivityType.listening, name=texto)
            elif activity_type.value == "watching": activity = discord.Activity(type=discord.ActivityType.watching, name=texto)
            elif activity_type.value == "streaming": activity = discord.Streaming(name=texto, url=url_stream)

        try:
            await client.change_presence(status=status_map[status.value], activity=activity)
            bot_config.set_presence(status.value, activity_type.value if activity_type else None, texto, url_stream, emoji=None)
            embed = discord.Embed(title="✅ Status Atualizado", description="O status do bot foi alterado com sucesso!", color=0x00FF00)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(title="❌ Erro", description=f"Ocorreu um erro ao tentar alterar o status: {e}", color=0xFF0000)
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @tree.command(name="clearactivity", description="👑 [Dono] Remove a atividade ou status personalizado do bot.")
    async def clear_activity(interaction: discord.Interaction):
        if not staff_system.is_staff(interaction.user):
            return await interaction.response.send_message("❌ Apenas membros da Staff podem usar este comando.", ephemeral=True)
        try:
            current_status_str = bot_config.get_presence().get('status', 'online')
            status_map = {"online": discord.Status.online, "idle": discord.Status.idle, "dnd": discord.Status.dnd, "invisible": discord.Status.invisible}
            current_status = status_map.get(current_status_str, discord.Status.online)
            await client.change_presence(status=current_status, activity=None)
            bot_config.set_presence(current_status_str, None, None, None, None)
            embed = discord.Embed(title="✅ Atividade Removida", description="A atividade do bot foi removida com sucesso!", color=0x00FF00)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(title="❌ Erro", description=f"Ocorreu um erro ao limpar a atividade: {e}", color=0xFF0000)
            await interaction.response.send_message(embed=embed, ephemeral=True)