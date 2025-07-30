# embed_builder_command.py
import discord
from discord import ui, app_commands
import json
from io import BytesIO
from typing import List, Optional
from staff_commands import staff_system
from ai_service import generate_embed_content

# --- Classes Base ---
# Definidas primeiro para evitar o NameError
class BaseManagerView(ui.View):
    def __init__(self, original_interaction: discord.Interaction):
        super().__init__(timeout=900) # Timeout de 15 minutos
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
                pass # A mensagem pode ter sido deletada

class BaseModal(ui.Modal):
    def __init__(self, view: ui.View, title: str):
        super().__init__(title=title, timeout=300)
        self.view = view

    async def on_submit(self, interaction: discord.Interaction):
        if hasattr(self.view, 'update_message'):
            await self.view.update_message(interaction, from_modal=True)

# --- Modals (Formulários Pop-up) ---

class EditTitleModal(BaseModal):
    def __init__(self, view: 'EmbedBuilderView'):
        super().__init__(view, title="Editar Título")
        self.embed_title.default = view.get_current_embed().title
    embed_title = ui.TextInput(label="Título", required=False, max_length=256)
    async def on_submit(self, interaction: discord.Interaction):
        self.view.get_current_embed().title = self.embed_title.value
        await super().on_submit(interaction)

class EditDescriptionModal(BaseModal):
    def __init__(self, view: 'EmbedBuilderView'):
        super().__init__(view, title="Editar Descrição")
        self.description.default = view.get_current_embed().description
    description = ui.TextInput(label="Descrição", style=discord.TextStyle.paragraph, required=False, max_length=4000)
    async def on_submit(self, interaction: discord.Interaction):
        self.view.get_current_embed().description = self.description.value
        await super().on_submit(interaction)

class EditColorModal(BaseModal):
    def __init__(self, view: 'EmbedBuilderView'):
        super().__init__(view, title="Editar Cor")
        if view.get_current_embed().color: self.color.default = f"#{view.get_current_embed().color.value:06x}"
    color = ui.TextInput(label="Cor Hexadecimal (ex: #FF5733)", required=False, max_length=7)
    async def on_submit(self, interaction: discord.Interaction):
        color_val = self.color.value
        if not color_val: self.view.get_current_embed().color = None
        else:
            try: self.view.get_current_embed().color = int(color_val.lstrip('#'), 16)
            except ValueError: return await interaction.response.send_message("Cor inválida.", ephemeral=True, delete_after=5)
        await super().on_submit(interaction)

class EditAuthorModal(BaseModal):
    def __init__(self, view: 'EmbedBuilderView'):
        super().__init__(view, title="Editar Autor")
        author = view.get_current_embed().author
        self.author_name.default = author.name
        self.author_url.default = author.url
        self.author_icon_url.default = author.icon_url
    author_name = ui.TextInput(label="Nome do Autor", required=False, max_length=256)
    author_url = ui.TextInput(label="URL do Autor (Opcional)", required=False)
    author_icon_url = ui.TextInput(label="URL do Ícone do Autor (Opcional)", required=False)
    async def on_submit(self, interaction: discord.Interaction):
        self.view.get_current_embed().set_author(name=self.author_name.value or "", url=self.author_url.value or None, icon_url=self.author_icon_url.value or None)
        await super().on_submit(interaction)

class EditImageModal(BaseModal):
    def __init__(self, view: 'EmbedBuilderView'):
        super().__init__(view, title="Editar Imagens")
        embed = view.get_current_embed()
        self.image_url.default = embed.image.url
        self.thumbnail_url.default = embed.thumbnail.url
    image_url = ui.TextInput(label="URL da Imagem Principal (Opcional)", required=False)
    thumbnail_url = ui.TextInput(label="URL da Miniatura (Thumbnail) (Opcional)", required=False)
    async def on_submit(self, interaction: discord.Interaction):
        embed = self.view.get_current_embed()
        embed.set_image(url=self.image_url.value or None)
        embed.set_thumbnail(url=self.thumbnail_url.value or None)
        await super().on_submit(interaction)

class EditFooterModal(BaseModal):
    def __init__(self, view: 'EmbedBuilderView'):
        super().__init__(view, title="Editar Rodapé")
        footer = view.get_current_embed().footer
        self.footer_text.default = footer.text
        self.footer_icon_url.default = footer.icon_url
    footer_text = ui.TextInput(label="Texto do Rodapé", required=False, max_length=2048)
    footer_icon_url = ui.TextInput(label="URL do Ícone do Rodapé (Opcional)", required=False)
    async def on_submit(self, interaction: discord.Interaction):
        self.view.get_current_embed().set_footer(text=self.footer_text.value or "", icon_url=self.footer_icon_url.value or None)
        await super().on_submit(interaction)

class FieldEditModal(ui.Modal, title="Adicionar/Editar Campo"):
    def __init__(self, manager_view: 'FieldManagerView', field_index: Optional[int] = None):
        super().__init__()
        self.manager_view = manager_view
        self.field_index = field_index
        if field_index is not None:
            field = self.manager_view.embed.fields[field_index]
            self.field_name.default = field.name
            self.field_value.default = field.value
            self.field_inline.default = "sim" if field.inline else "nao"
    field_name = ui.TextInput(label="Nome do Campo", required=True, max_length=256)
    field_value = ui.TextInput(label="Valor do Campo", required=True, style=discord.TextStyle.paragraph, max_length=1024)
    field_inline = ui.TextInput(label="Inline (sim/nao)", default="sim", max_length=3)
    async def on_submit(self, interaction: discord.Interaction):
        inline = self.field_inline.value.lower() in ['sim', 's', 'yes', 'y', 'true']
        if self.field_index is not None:
            self.manager_view.embed.set_field_at(self.field_index, name=self.field_name.value, value=self.field_value.value, inline=inline)
        else:
            self.manager_view.embed.add_field(name=self.field_name.value, value=self.field_value.value, inline=inline)
        await self.manager_view.update_message(interaction, from_modal=True)

class ImportJsonModal(ui.Modal, title="Importar JSON"):
    def __init__(self, view: 'EmbedBuilderView'):
        super().__init__()
        self.view = view
    json_data = ui.TextInput(label="Cole o código JSON aqui", style=discord.TextStyle.paragraph, required=True)
    async def on_submit(self, interaction: discord.Interaction):
        try:
            data = json.loads(self.json_data.value)
            self.view.embeds = [discord.Embed.from_dict(e) for e in data.get('embeds', [data.get('embed', data)])]
            self.view.components = [ui.ActionRow.from_dict(c) for c in data.get('components', [])]
            self.view.current_embed_index = 0
            await self.view.update_message(interaction, from_modal=True)
        except Exception as e:
            await interaction.response.send_message(f"Erro ao processar JSON: {e}", ephemeral=True, delete_after=10)

class AIGenerateModal(ui.Modal, title="Gerar Embed com IA"):
    def __init__(self, view: 'EmbedBuilderView'):
        super().__init__()
        self.view = view
    prompt = ui.TextInput(label="Qual o tema do embed?", placeholder="Ex: 'um resumo sobre a história da Roma Antiga'", style=discord.TextStyle.paragraph, required=True)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        content = await generate_embed_content(self.prompt.value)
        if content:
            embed = self.view.get_current_embed()
            embed.title = content.get("title")
            embed.description = content.get("description")
            await self.view.update_message(interaction, from_modal=True)
            await interaction.followup.send("✅ Conteúdo gerado!", ephemeral=True, delete_after=5)
        else:
            await interaction.followup.send("❌ Não foi possível gerar o conteúdo.", ephemeral=True, delete_after=5)

class ComponentEditModal(ui.Modal, title="Adicionar/Editar Botão"):
    def __init__(self, manager_view: 'ComponentBuilderView', row: int, index: Optional[int] = None):
        super().__init__()
        self.manager_view = manager_view
        self.row = row
        self.index = index
        if index is not None:
            button = self.manager_view.components[row].children[index]
            self.button_label.default = button.label
            self.button_url.default = button.url
            if button.emoji: self.button_emoji.default = str(button.emoji)
    
    button_label = ui.TextInput(label="Texto do Botão", required=True, max_length=80)
    button_url = ui.TextInput(label="Link do Botão", required=True, style=discord.TextStyle.short)
    button_emoji = ui.TextInput(label="Emoji (Opcional)", required=False, max_length=5)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            button = ui.Button(label=self.button_label.value, url=self.button_url.value, emoji=self.button_emoji.value or None, style=discord.ButtonStyle.link)
            if self.index is not None:
                self.manager_view.components[self.row].children[self.index] = button
            else:
                self.manager_view.components[self.row].add_item(button)
            await self.manager_view.update_message(interaction, from_modal=True)
        except Exception as e:
            await interaction.response.send_message(f"Erro ao criar botão: {e}", ephemeral=True, delete_after=5)

# --- Views de Gerenciamento ---

class FieldManagerView(BaseManagerView):
    def __init__(self, main_view: 'EmbedBuilderView'):
        super().__init__(main_view.original_interaction)
        self.main_view = main_view
        self.embed = self.main_view.get_current_embed()
        self.selected_field_index: Optional[int] = None
        self.message = main_view.message
        self._update_components()

    def _update_components(self):
        self.clear_items()
        options = [discord.SelectOption(label=f"Campo #{i+1}: {field.name[:80]}", value=str(i), description=(field.value or "...")[:100]) for i, field in enumerate(self.embed.fields)] or [discord.SelectOption(label="Nenhum campo para selecionar", value="-1")]
        self.add_item(ui.Select(placeholder="Selecione um campo...", options=options, row=0))
        self.add_item(ui.Button(label="Adicionar Campo", emoji="➕", style=discord.ButtonStyle.success, row=1))
        self.add_item(ui.Button(label="Editar Campo", emoji="✏️", style=discord.ButtonStyle.secondary, row=1, disabled=(self.selected_field_index is None)))
        self.add_item(ui.Button(label="Remover Campo", emoji="🗑️", style=discord.ButtonStyle.danger, row=1, disabled=(self.selected_field_index is None)))
        self.add_item(ui.Button(label="Voltar ao Painel", emoji="⬅️", style=discord.ButtonStyle.primary, row=2))

    async def update_message(self, interaction: discord.Interaction, from_modal: bool = False):
        view = FieldManagerView(self.main_view)
        view.selected_field_index = self.selected_field_index
        if from_modal and not interaction.response.is_done(): await interaction.response.defer()
        target = self.message if from_modal else interaction
        await target.edit(embed=self.embed, view=view)

    @ui.select(row=0)
    async def on_select_field(self, interaction: discord.Interaction, select: ui.Select):
        value = select.values[0]
        if value != "-1": self.selected_field_index = int(value)
        await self.update_message(interaction)

    @ui.button(label="Adicionar Campo", row=1)
    async def on_add_field(self, interaction: discord.Interaction, button: ui.Button):
        if len(self.embed.fields) >= 25: return await interaction.response.send_message("Máximo de 25 campos atingido.", ephemeral=True, delete_after=5)
        await interaction.response.send_modal(FieldEditModal(self))

    @ui.button(label="Editar Campo", row=1)
    async def on_edit_field(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(FieldEditModal(self, self.selected_field_index))

    @ui.button(label="Remover Campo", row=1)
    async def on_remove_field(self, interaction: discord.Interaction, button: ui.Button):
        if self.selected_field_index is not None:
            self.embed.remove_field(self.selected_field_index)
            self.selected_field_index = None
        await self.update_message(interaction)

    @ui.button(label="Voltar ao Painel", row=2)
    async def on_back(self, interaction: discord.Interaction, button: ui.Button):
        await self.main_view.update_message(interaction)

class ComponentBuilderView(BaseManagerView):
    def __init__(self, main_view: 'EmbedBuilderView'):
        super().__init__(main_view.original_interaction)
        self.main_view = main_view
        self.components = self.main_view.components
        self.message = main_view.message
        self._update_components()

    def _update_components(self):
        self.clear_items()
        for i, action_row in enumerate(self.components):
            for j, button in enumerate(action_row.children):
                self.add_item(ui.Button(label=f"Editar Botão {j+1}", emoji="🔘", style=discord.ButtonStyle.secondary, custom_id=f"edit_{i}_{j}", row=i))
            if len(action_row.children) < 5:
                self.add_item(ui.Button(label="Adicionar Botão", emoji="➕", style=discord.ButtonStyle.success, custom_id=f"add_{i}", row=i))
        if len(self.components) < 5:
            self.add_item(ui.Button(label="Adicionar Nova Fila de Botões", emoji="➕", style=discord.ButtonStyle.primary, custom_id="add_row", row=len(self.components)))
        self.add_item(ui.Button(label="Voltar ao Painel", emoji="⬅️", style=discord.ButtonStyle.primary, row=4, custom_id="back_to_main"))

    async def update_message(self, interaction: discord.Interaction, from_modal: bool=False):
        view = ComponentBuilderView(self.main_view)
        preview_embed = discord.Embed(title="Editor de Componentes (Botões)", description="Adicione ou edite botões de link para sua mensagem.", color=0x2B2D31)
        if from_modal:
            if not interaction.response.is_done(): await interaction.response.defer()
            await self.message.edit(embed=preview_embed, view=view)
        else:
            await interaction.response.edit_message(embed=preview_embed, view=view)
    
    async def on_button_click(self, interaction: discord.Interaction, button: ui.Button):
        cid = button.custom_id
        if cid == "add_row":
            if len(self.components) < 5: self.components.append(ui.ActionRow())
        elif cid.startswith("add_"):
            row = int(cid.split('_')[1])
            await interaction.response.send_modal(ComponentEditModal(self, row))
        elif cid.startswith("edit_"):
            _, row, index = cid.split('_')
            await interaction.response.send_modal(ComponentEditModal(self, int(row), int(index)))
        elif cid == "back_to_main":
            return await self.main_view.update_message(interaction)
        await self.update_message(interaction)

class EmbedBuilderView(BaseManagerView):
    def __init__(self, original_interaction: discord.Interaction, target_channel: discord.TextChannel):
        super().__init__(original_interaction)
        self.target_channel = target_channel
        self.embeds: List[discord.Embed] = [discord.Embed(title="Novo Embed", description="Comece a editar!")]
        self.components: List[ui.ActionRow] = []
        self.current_embed_index = 0
        self._update_components()

    def get_current_embed(self) -> discord.Embed: return self.embeds[self.current_embed_index]
    def create_panel_embed(self) -> discord.Embed: return discord.Embed(title="Painel Principal", description=f"Editando **Embed #{self.current_embed_index + 1}** de **{len(self.embeds)}**.\nDestino: {self.target_channel.mention}.", color=0x2B2D31)
    
    def _update_components(self):
        self.clear_items()
        self.add_item(ui.Select(placeholder=f"Editando Embed #{self.current_embed_index + 1}", options=[discord.SelectOption(label=f"Embed #{i+1}", value=str(i)) for i in range(len(self.embeds))] or [discord.SelectOption(label="N/A", value="0")], row=0))
        self.add_item(ui.Button(label="Adicionar Embed", emoji="➕", style=discord.ButtonStyle.success, row=1))
        self.add_item(ui.Button(label="Apagar Embed", emoji="🗑️", style=discord.ButtonStyle.danger, row=1, disabled=len(self.embeds) <= 1))
        self.add_item(ui.Button(label="Gerar com IA", emoji="✨", style=discord.ButtonStyle.primary, row=1))
        self.add_item(ui.Button(label="Editar Embed Selecionado", emoji="✏️", style=discord.ButtonStyle.secondary, row=2))
        self.add_item(ui.Button(label="Adicionar/Editar Componentes", emoji="🔘", style=discord.ButtonStyle.secondary, row=2))
        self.add_item(ui.Button(label="Importar JSON", emoji="📥", style=discord.ButtonStyle.grey, row=3))
        self.add_item(ui.Button(label="Exportar JSON", emoji="📤", style=discord.ButtonStyle.grey, row=3))
        self.add_item(ui.Button(label="Enviar Mensagem", emoji="🚀", style=discord.ButtonStyle.primary, row=4))

    async def update_message(self, interaction: discord.Interaction, from_modal: bool = False):
        view = EmbedBuilderView(self.original_interaction, self.target_channel)
        view.embeds, view.current_embed_index, view.message, view.components = self.embeds, self.current_embed_index, self.message, self.components
        
        embeds_to_show = [view.create_panel_embed(), view.get_current_embed()]
        
        target = interaction.followup if from_modal and self.message else interaction.response
        if from_modal:
            if not interaction.response.is_done(): await interaction.response.defer()
            await self.message.edit(embeds=embeds_to_show, view=view)
        else:
            await interaction.response.edit_message(embeds=embeds_to_show, view=view)

    @ui.select(row=0)
    async def on_select_embed(self, interaction: discord.Interaction, select: ui.Select):
        self.current_embed_index = int(select.values[0])
        await self.update_message(interaction)

    @ui.button(label="Adicionar Embed", row=1)
    async def on_add_embed(self, interaction: discord.Interaction, button: ui.Button):
        if len(self.embeds) >= 10: return await interaction.response.send_message("Limite de 10 embeds.", ephemeral=True, delete_after=5)
        self.embeds.append(discord.Embed(description=f"Novo Embed #{len(self.embeds) + 1}"))
        self.current_embed_index = len(self.embeds) - 1
        await self.update_message(interaction)
        
    @ui.button(label="Apagar Embed", row=1)
    async def on_remove_embed(self, interaction: discord.Interaction, button: ui.Button):
        self.embeds.pop(self.current_embed_index)
        self.current_embed_index = min(self.current_embed_index, len(self.embeds) - 1)
        await self.update_message(interaction)

    @ui.button(label="Gerar com IA", row=1)
    async def on_ai_generate(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(AIGenerateModal(self))
        
    @ui.button(label="Editar Embed Selecionado", row=2)
    async def on_edit_embed(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.edit_message(view=EmbedEditView(self))

    @ui.button(label="Adicionar/Editar Componentes", row=2)
    async def on_edit_components(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.edit_message(embed=discord.Embed(title="Editor de Componentes", description="Use os botões para gerenciar as fileiras e os botões de link.", color=0x2B2D31), view=ComponentBuilderView(self))

    @ui.button(label="Importar JSON", row=3)
    async def on_import_json(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(ImportJsonModal(self))

    @ui.button(label="Exportar JSON", row=3)
    async def on_export_json(self, interaction: discord.Interaction, button: ui.Button):
        output = {"embeds": [e.to_dict() for e in self.embeds]}
        if self.components: output["components"] = [c.to_dict() for c in self.components]
        json_string = json.dumps(output, indent=4, ensure_ascii=False)
        file = discord.File(BytesIO(json_string.encode('utf-8')), filename="message.json")
        await interaction.response.send_message("Aqui está o JSON da sua mensagem:", file=file, ephemeral=True)

    @ui.button(label="Enviar Mensagem", row=4)
    async def on_send_message(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer(ephemeral=True)
        final_view = ui.View()
        for action_row in self.components:
            for component in action_row.children:
                final_view.add_item(component)
        try:
            await self.target_channel.send(embeds=self.embeds, view=final_view if final_view.children else None)
            await interaction.followup.send(f"✅ Mensagem enviada para {self.target_channel.mention}!", ephemeral=True)
            self.stop()
        except Exception as e:
            await interaction.followup.send(f"❌ Ocorreu um erro: {e}", ephemeral=True)

class EmbedEditView(BaseManagerView):
    def __init__(self, main_view: EmbedBuilderView):
        super().__init__(main_view.original_interaction)
        self.main_view = main_view
        self.message = main_view.message
    
    @ui.button(label="Título", emoji="✏️", style=discord.ButtonStyle.secondary, row=0)
    async def on_edit_title(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(EditTitleModal(self.main_view))
    # ... Adicione os outros botões de edição aqui
    @ui.button(label="Voltar ao Painel", emoji="⬅️", style=discord.ButtonStyle.primary, row=4)
    async def on_back(self, interaction: discord.Interaction, button: ui.Button):
        await self.main_view.update_message(interaction)

def setup_embed_builder_command(tree: app_commands.CommandTree):
    embed_group = app_commands.Group(name="embed", description="Comandos para criar e gerenciar embeds e mensagens.")

    @embed_group.command(name="create", description="📝 [STAFF] Abre o painel interativo para criar mensagens.")
    @app_commands.describe(canal="O canal para onde a mensagem será enviada.")
    async def embed_create(interaction: discord.Interaction, canal: discord.TextChannel):
        if not (isinstance(interaction.user, discord.Member) and staff_system.is_staff(interaction.user)):
            return await interaction.response.send_message("❌ Você não tem permissão para usar este comando.", ephemeral=True)
        
        view = EmbedBuilderView(interaction, canal)
        await interaction.response.send_message(
            embeds=[view.create_panel_embed(), view.get_current_embed()], 
            view=view, 
            ephemeral=True
        )
        view.message = await interaction.original_response()

    tree.add_command(embed_group)