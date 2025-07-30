# embed_builder_command.py
import discord
from discord import ui, app_commands
import json
from io import BytesIO
from typing import List, Optional
from staff_commands import staff_system
from ai_service import generate_embed_content

# --- Classes Base ---
class BaseManagerView(ui.View):
    def __init__(self, original_interaction: discord.Interaction, timeout: float = 900):
        super().__init__(timeout=timeout)
        self.original_interaction = original_interaction
        self.message: Optional[discord.Message] = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.original_interaction.user.id:
            await interaction.response.send_message("Você não pode controlar este painel.", ephemeral=True, delete_after=5)
            return False
        return True

    async def on_timeout(self):
        if self.message:
            for item in self.children:
                item.disabled = True
            try:
                await self.message.edit(content="*Este painel de criação expirou.*", view=self)
            except discord.NotFound:
                pass

class BaseModal(ui.Modal):
    def __init__(self, view: 'EmbedBuilderView', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.view = view

# --- Modals ---
class EditTitleModal(BaseModal, title="Editar Título"):
    def __init__(self, view: 'EmbedBuilderView'):
        super().__init__(view)
        self.embed_title.default = view.get_current_embed().title
    embed_title = ui.TextInput(label="Título", required=False, max_length=256)
    async def on_submit(self, interaction: discord.Interaction):
        self.view.get_current_embed().title = self.embed_title.value
        await self.view.update_message(interaction)

class EditDescriptionModal(BaseModal, title="Editar Descrição"):
    def __init__(self, view: 'EmbedBuilderView'):
        super().__init__(view)
        self.description.default = view.get_current_embed().description
    description = ui.TextInput(label="Descrição", style=discord.TextStyle.paragraph, required=False, max_length=4000)
    async def on_submit(self, interaction: discord.Interaction):
        self.view.get_current_embed().description = self.description.value
        await self.view.update_message(interaction)

class EditColorModal(BaseModal, title="Editar Cor"):
    def __init__(self, view: 'EmbedBuilderView'):
        super().__init__(view)
        if view.get_current_embed().color: self.color.default = f"#{view.get_current_embed().color.value:06x}"
    color = ui.TextInput(label="Cor Hexadecimal (ex: #FF5733)", required=False, max_length=7)
    async def on_submit(self, interaction: discord.Interaction):
        color_val = self.color.value
        if not color_val: self.view.get_current_embed().color = None
        else:
            try: self.view.get_current_embed().color = int(color_val.lstrip('#'), 16)
            except ValueError: return await interaction.response.send_message("Cor inválida.", ephemeral=True, delete_after=5)
        await self.view.update_message(interaction)

class EditAuthorModal(BaseModal, title="Editar Autor"):
    def __init__(self, view: 'EmbedBuilderView'):
        super().__init__(view)
        author = view.get_current_embed().author
        self.author_name.default = author.name
        self.author_url.default = author.url
        self.author_icon_url.default = author.icon_url
    author_name = ui.TextInput(label="Nome do Autor", required=False, max_length=256)
    author_url = ui.TextInput(label="URL do Autor (Opcional)", required=False)
    author_icon_url = ui.TextInput(label="URL do Ícone do Autor (Opcional)", required=False)
    async def on_submit(self, interaction: discord.Interaction):
        self.view.get_current_embed().set_author(name=self.author_name.value or "", url=self.author_url.value or None, icon_url=self.author_icon_url.value or None)
        await self.view.update_message(interaction)

class EditImageModal(BaseModal, title="Editar Imagens"):
    def __init__(self, view: 'EmbedBuilderView'):
        super().__init__(view)
        embed = view.get_current_embed()
        self.image_url.default = embed.image.url
        self.thumbnail_url.default = embed.thumbnail.url
    image_url = ui.TextInput(label="URL da Imagem Principal (Opcional)", required=False)
    thumbnail_url = ui.TextInput(label="URL da Miniatura (Opcional)", required=False)
    async def on_submit(self, interaction: discord.Interaction):
        embed = self.view.get_current_embed()
        embed.set_image(url=self.image_url.value or None)
        embed.set_thumbnail(url=self.thumbnail_url.value or None)
        await self.view.update_message(interaction)

class EditFooterModal(BaseModal, title="Editar Rodapé"):
    def __init__(self, view: 'EmbedBuilderView'):
        super().__init__(view)
        footer = view.get_current_embed().footer
        self.footer_text.default = footer.text
        self.footer_icon_url.default = footer.icon_url
    footer_text = ui.TextInput(label="Texto do Rodapé", required=False, max_length=2048)
    footer_icon_url = ui.TextInput(label="URL do Ícone do Rodapé (Opcional)", required=False)
    async def on_submit(self, interaction: discord.Interaction):
        self.view.get_current_embed().set_footer(text=self.footer_text.value or "", icon_url=self.footer_icon_url.value or None)
        await self.view.update_message(interaction)

class ImportJsonModal(ui.Modal, title="Importar JSON"):
    def __init__(self, view: 'EmbedBuilderView'):
        super().__init__()
        self.view = view
    json_data = ui.TextInput(label="Cole o código JSON aqui", style=discord.TextStyle.paragraph, required=True)
    async def on_submit(self, interaction: discord.Interaction):
        try:
            data = json.loads(self.json_data.value)
            embed_dicts = data.get('embeds', [data])
            self.view.embeds = [discord.Embed.from_dict(d) for d in embed_dicts]
            self.view.components = [] # Reset components on import
            self.view.current_embed_index = 0
            await self.view.update_message(interaction)
        except Exception as e:
            await interaction.response.send_message(f"Erro ao processar JSON: {e}", ephemeral=True, delete_after=10)

class AIGenerateModal(ui.Modal, title="Gerar Embed com IA"):
    def __init__(self, view: 'EmbedBuilderView'):
        super().__init__()
        self.view = view
    prompt = ui.TextInput(label="Qual o tema do embed?", placeholder="Ex: 'um resumo sobre a história da Roma Antiga'", style=discord.TextStyle.paragraph)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        content = await generate_embed_content(self.prompt.value)
        if content:
            embed = self.view.get_current_embed()
            embed.title = content.get("title")
            embed.description = content.get("description")
            await self.view.update_message(interaction.message)
            await interaction.followup.send("✅ Conteúdo gerado!", ephemeral=True, delete_after=5)
        else:
            await interaction.followup.send("❌ Não foi possível gerar o conteúdo.", ephemeral=True, delete_after=5)

# --- VIEW PRINCIPAL DO CONSTRUTOR DE EMBED ---
class EmbedBuilderView(BaseManagerView):
    def __init__(self, original_interaction: discord.Interaction, target_channel: discord.TextChannel):
        super().__init__(original_interaction)
        self.target_channel = target_channel
        self.embeds: List[discord.Embed] = [discord.Embed(title="Novo Embed", description="Comece a editar!")]
        self.components: List[ui.ActionRow] = []
        self.current_embed_index = 0
        self._add_components()

    def get_current_embed(self) -> discord.Embed:
        return self.embeds[self.current_embed_index]

    def create_panel_embed(self) -> discord.Embed:
        return discord.Embed(
            title="Painel de Criação de Mensagens",
            description=f"Editando **Embed #{self.current_embed_index + 1}** de **{len(self.embeds)}**.\n"
                        f"Destino: {self.target_channel.mention}.",
            color=0x2B2D31
        )
    
    def _add_components(self):
        self.clear_items()
        options = [discord.SelectOption(label=f"Embed #{i+1}", value=str(i)) for i in range(len(self.embeds))]
        self.add_item(ui.Select(placeholder=f"Editando Embed #{self.current_embed_index + 1}", options=options, row=0))
        self.add_item(ui.Button(label="Adicionar Embed", emoji="➕", style=discord.ButtonStyle.success, row=1))
        self.add_item(ui.Button(label="Apagar Embed", emoji="🗑️", style=discord.ButtonStyle.danger, row=1, disabled=len(self.embeds) <= 1))
        self.add_item(ui.Button(label="Gerar com IA", emoji="✨", style=discord.ButtonStyle.primary, row=1))
        self.add_item(ui.Button(label="Título", emoji="✏️", style=discord.ButtonStyle.secondary, row=2))
        self.add_item(ui.Button(label="Descrição", emoji="📄", style=discord.ButtonStyle.secondary, row=2))
        self.add_item(ui.Button(label="Cor", emoji="🎨", style=discord.ButtonStyle.secondary, row=2))
        self.add_item(ui.Button(label="Autor", emoji="👤", style=discord.ButtonStyle.secondary, row=3))
        self.add_item(ui.Button(label="Imagem/Thumb", emoji="🖼️", style=discord.ButtonStyle.secondary, row=3))
        self.add_item(ui.Button(label="Rodapé", emoji="🦶", style=discord.ButtonStyle.secondary, row=3))
        self.add_item(ui.Button(label="Campos", emoji="➕", style=discord.ButtonStyle.secondary, row=3))
        self.add_item(ui.Button(label="Importar JSON", emoji="📥", style=discord.ButtonStyle.grey, row=4))
        self.add_item(ui.Button(label="Exportar JSON", emoji="📤", style=discord.ButtonStyle.grey, row=4))
        self.add_item(ui.Button(label="Enviar Mensagem", emoji="🚀", style=discord.ButtonStyle.primary, row=4))

    async def update_message(self, interaction: discord.Interaction):
        self._add_components() # Recria os botões com o estado atualizado (ex: botão de apagar)
        await interaction.response.edit_message(
            embeds=[self.create_panel_embed(), self.get_current_embed()], 
            view=self
        )

    async def callback(self, interaction: discord.Interaction):
        # Este callback agora lida com todos os botões e selects
        custom_id = interaction.data.get('custom_id') # Para componentes com ID
        
        # Lógica para o Menu de Seleção
        if interaction.data.get('component_type') == 3:
             self.current_embed_index = int(interaction.data['values'][0])
             await self.update_message(interaction)
             return

        # Lógica para os Botões (usa o label como identificador)
        label = interaction.data.get('label')
        if label == "Adicionar Embed":
            if len(self.embeds) >= 10: return await interaction.response.send_message("Limite de 10 embeds.", ephemeral=True, delete_after=5)
            self.embeds.append(discord.Embed(description=f"Novo Embed #{len(self.embeds) + 1}"))
            self.current_embed_index = len(self.embeds) - 1
            await self.update_message(interaction)
        elif label == "Apagar Embed":
            self.embeds.pop(self.current_embed_index)
            self.current_embed_index = min(self.current_embed_index, len(self.embeds) - 1)
            await self.update_message(interaction)
        elif label == "Gerar com IA": await interaction.response.send_modal(AIGenerateModal(self))
        elif label == "Título": await interaction.response.send_modal(EditTitleModal(self))
        elif label == "Descrição": await interaction.response.send_modal(EditDescriptionModal(self))
        elif label == "Cor": await interaction.response.send_modal(EditColorModal(self))
        elif label == "Autor": await interaction.response.send_modal(EditAuthorModal(self))
        elif label == "Imagem/Thumb": await interaction.response.send_modal(EditImageModal(self))
        elif label == "Rodapé": await interaction.response.send_modal(EditFooterModal(self))
        elif label == "Campos": await interaction.response.send_message("Funcionalidade de Campos em desenvolvimento.", ephemeral=True, delete_after=5)
        elif label == "Importar JSON": await interaction.response.send_modal(ImportJsonModal(self))
        elif label == "Exportar JSON":
            output = {"embeds": [e.to_dict() for e in self.embeds]}
            if self.components: output["components"] = [c.to_dict() for c in self.components]
            json_string = json.dumps(output, indent=4, ensure_ascii=False)
            file = discord.File(BytesIO(json_string.encode('utf-8')), filename="message.json")
            await interaction.response.send_message("JSON da sua mensagem:", file=file, ephemeral=True)
        elif label == "Enviar Mensagem":
            await interaction.response.defer(ephemeral=True)
            try:
                await self.target_channel.send(embeds=self.embeds)
                await interaction.followup.send(f"✅ Mensagem enviada para {self.target_channel.mention}!", ephemeral=True)
                self.stop()
            except Exception as e:
                await interaction.followup.send(f"❌ Ocorreu um erro: {e}", ephemeral=True)

def setup_embed_builder_command(tree: app_commands.CommandTree):
    @tree.command(name="embed", description="📝 [STAFF] Abre o painel interativo para criar mensagens.")
    @app_commands.describe(canal="O canal para onde a mensagem será enviada.")
    async def embed(interaction: discord.Interaction, canal: discord.TextChannel):
        if not (isinstance(interaction.user, discord.Member) and staff_system.is_staff(interaction.user)):
            return await interaction.response.send_message("❌ Você não tem permissão para usar este comando.", ephemeral=True)
        
        view = EmbedBuilderView(interaction, canal)
        await interaction.response.send_message(
            embeds=[view.create_panel_embed(), view.get_current_embed()], 
            view=view, 
            ephemeral=True
        )
        view.message = await interaction.original_response()