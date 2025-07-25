# embed_command.py
import discord
from discord import ui, app_commands
from typing import Optional
from staff_commands import staff_system

# Esta é a classe que define o formulário (pop-up) que o staff irá preencher.
class EmbedModal(ui.Modal, title='Criador de Embed Personalizado'):
    def __init__(self, target_channel: discord.TextChannel):
        super().__init__()
        self.target_channel = target_channel

    # Campo para o Título do Embed
    embed_title = ui.TextInput(
        label='Título do Embed',
        placeholder='O título principal do seu embed.',
        required=True,
        style=discord.TextStyle.short
    )

    # Campo para a Descrição do Embed
    description = ui.TextInput(
        label='Descrição',
        placeholder='O texto principal do embed. Você pode usar markdown aqui (ex: **negrito**).',
        required=True,
        style=discord.TextStyle.paragraph
    )

    # Campo para a Cor
    color = ui.TextInput(
        label='Cor em Hexadecimal (Opcional)',
        placeholder='Ex: #FF5733 ou apenas FF5733. Padrão é azul.',
        required=False,
        max_length=7
    )

    # Campo para a URL da imagem principal
    image_url = ui.TextInput(
        label='URL da Imagem Principal (Opcional)',
        placeholder='https.exemplo.com/imagem.png',
        required=False
    )

    # Campo para a URL da miniatura (thumbnail)
    thumbnail_url = ui.TextInput(
        label='URL da Miniatura (Thumbnail) (Opcional)',
        placeholder='https.exemplo.com/miniatura.png',
        required=False
    )

    # Esta função é executada quando o staff clica em "Enviar" no formulário.
    async def on_submit(self, interaction: discord.Interaction):
        # Pega os valores dos campos preenchidos
        title_text = self.embed_title.value
        desc_text = self.description.value
        color_hex = self.color.value
        img_url = self.image_url.value
        thumb_url = self.thumbnail_url.value

        # Tenta converter a cor hexadecimal para um inteiro. Se falhar, usa uma cor padrão.
        color_int = 0x5865F2 # Cor padrão (Azul Discord)
        if color_hex:
            try:
                color_int = int(color_hex.lstrip('#'), 16)
            except ValueError:
                await interaction.response.send_message("A cor hexadecimal fornecida é inválida. Usando a cor padrão.", ephemeral=True)
                return

        # Cria o objeto do Embed com os dados fornecidos
        embed = discord.Embed(
            title=title_text,
            description=desc_text,
            color=color_int
        )

        # Adiciona a imagem principal, se uma URL válida foi fornecida
        if img_url:
            embed.set_image(url=img_url)

        # Adiciona a miniatura, se uma URL válida foi fornecida
        if thumb_url:
            embed.set_thumbnail(url=thumb_url)

        try:
            # Envia o embed final no canal que foi escolhido
            await self.target_channel.send(embed=embed)
            await interaction.response.send_message(f"✅ Embed enviado com sucesso no canal {self.target_channel.mention}!", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ Erro de Permissão! Não tenho permissão para enviar mensagens nesse canal.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Ocorreu um erro inesperado: {e}", ephemeral=True)


def setup_embed_command(tree: app_commands.CommandTree):
    @tree.command(name="embed", description="📝 [STAFF] Cria e envia um embed personalizado em um canal.")
    @app_commands.describe(canal="O canal para onde o embed será enviado.")
    async def embed(interaction: discord.Interaction, canal: discord.TextChannel):
        if not staff_system.is_staff(interaction.user):
            await interaction.response.send_message("❌ Você não tem permissão para usar este comando.", ephemeral=True)
            return

        # Cria o modal e o envia para o usuário
        modal = EmbedModal(target_channel=canal)
        await interaction.response.send_modal(modal)