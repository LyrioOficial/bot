# embed_builder_command.py
import discord
from discord import ui, app_commands
import json
from io import BytesIO
from typing import List, Optional
from staff_commands import staff_system
from ai_service import generate_embed_content

# --- MODALS (Formulários) ---
# Os modals agora chamam a função de atualização da view de forma mais direta.


class EditModal(ui.Modal):

    def __init__(self, view: 'EmbedBuilderView', title: str):
        super().__init__(title=title, timeout=300)
        self.view = view

    async def on_submit(self, interaction: discord.Interaction):
        # A lógica de atualização foi movida para cada modal específico
        pass


class EditTitleModal(EditModal):

    def __init__(self, view: 'EmbedBuilderView'):
        super().__init__(view, title="Editar Título")
        self.embed_title.default = view.get_current_embed().title

    embed_title = ui.TextInput(label="Título",
                               style=discord.TextStyle.short,
                               required=False,
                               max_length=256)

    async def on_submit(self, interaction: discord.Interaction):
        self.view.get_current_embed().title = self.embed_title.value
        await self.view.update_message(interaction)


class EditDescriptionModal(EditModal):

    def __init__(self, view: 'EmbedBuilderView'):
        super().__init__(view, title="Editar Descrição")
        self.description.default = view.get_current_embed().description

    description = ui.TextInput(label="Descrição",
                               style=discord.TextStyle.paragraph,
                               required=False,
                               max_length=4000)

    async def on_submit(self, interaction: discord.Interaction):
        self.view.get_current_embed().description = self.description.value
        await self.view.update_message(interaction)


class EditColorModal(EditModal):

    def __init__(self, view: 'EmbedBuilderView'):
        super().__init__(view, title="Editar Cor")
        if view.get_current_embed().color:
            self.color.default = f"#{view.get_current_embed().color.value:06x}"

    color = ui.TextInput(label="Cor Hexadecimal (ex: #FF5733)",
                         required=False,
                         max_length=7)

    async def on_submit(self, interaction: discord.Interaction):
        color_val = self.color.value
        if not color_val:
            self.view.get_current_embed().color = None
        else:
            try:
                self.view.get_current_embed().color = int(
                    color_val.lstrip('#'), 16)
            except ValueError:
                return await interaction.response.send_message("Cor inválida.",
                                                               ephemeral=True,
                                                               delete_after=5)
        await self.view.update_message(interaction)


class EditAuthorModal(EditModal):

    def __init__(self, view: 'EmbedBuilderView'):
        super().__init__(view, title="Editar Autor")
        author = view.get_current_embed().author
        self.author_name.default = author.name
        self.author_url.default = author.url
        self.author_icon_url.default = author.icon_url

    author_name = ui.TextInput(label="Nome do Autor",
                               required=False,
                               max_length=256)
    author_url = ui.TextInput(label="URL do Autor (Opcional)", required=False)
    author_icon_url = ui.TextInput(label="URL do Ícone do Autor (Opcional)",
                                   required=False)

    async def on_submit(self, interaction: discord.Interaction):
        name = self.author_name.value or ""
        self.view.get_current_embed().set_author(
            name=name,
            url=self.author_url.value or None,
            icon_url=self.author_icon_url.value or None)
        await self.view.update_message(interaction)


class EditImageModal(EditModal):

    def __init__(self, view: 'EmbedBuilderView'):
        super().__init__(view, title="Editar Imagens")
        embed = view.get_current_embed()
        self.image_url.default = embed.image.url
        self.thumbnail_url.default = embed.thumbnail.url

    image_url = ui.TextInput(label="URL da Imagem Principal (Opcional)",
                             required=False)
    thumbnail_url = ui.TextInput(
        label="URL da Miniatura (Thumbnail) (Opcional)", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        embed = self.view.get_current_embed()
        embed.set_image(url=self.image_url.value or None)
        embed.set_thumbnail(url=self.thumbnail_url.value or None)
        await self.view.update_message(interaction)


class EditFooterModal(EditModal):

    def __init__(self, view: 'EmbedBuilderView'):
        super().__init__(view, title="Editar Rodapé")
        footer = view.get_current_embed().footer
        self.footer_text.default = footer.text
        self.footer_icon_url.default = footer.icon_url

    footer_text = ui.TextInput(label="Texto do Rodapé",
                               required=False,
                               max_length=2048)
    footer_icon_url = ui.TextInput(label="URL do Ícone do Rodapé (Opcional)",
                                   required=False)

    async def on_submit(self, interaction: discord.Interaction):
        self.view.get_current_embed().set_footer(
            text=self.footer_text.value or "",
            icon_url=self.footer_icon_url.value or None)
        await self.view.update_message(interaction)


class ImportJsonModal(ui.Modal, title="Importar Embed de JSON"):

    def __init__(self, view: 'EmbedBuilderView'):
        super().__init__()
        self.view = view

    json_data = ui.TextInput(label="Cole o código JSON aqui",
                             style=discord.TextStyle.paragraph,
                             required=True)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            data = json.loads(self.json_data.value)
            embed_dicts = data.get('embeds', [data])
            if not isinstance(embed_dicts, list) or not embed_dicts:
                raise ValueError("JSON deve conter uma lista de embeds.")
            self.view.embeds = [
                discord.Embed.from_dict(d) for d in embed_dicts
            ]
            self.view.current_embed_index = 0
            await self.view.update_message(interaction)
        except Exception as e:
            await interaction.response.send_message(
                f"Erro ao processar o JSON: {e}",
                ephemeral=True,
                delete_after=10)


class AIGenerateModal(ui.Modal, title="Gerar Embed com IA"):

    def __init__(self, view: 'EmbedBuilderView'):
        super().__init__()
        self.view = view

    prompt = ui.TextInput(
        label="Qual o tema do embed?",
        placeholder="Ex: 'um resumo sobre a história da Roma Antiga'",
        style=discord.TextStyle.paragraph,
        required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        content = await generate_embed_content(self.prompt.value)
        if content:
            embed = self.view.get_current_embed()
            embed.title = content.get("title")
            embed.description = content.get("description")
            # Precisamos chamar a atualização na view principal
            await self.view.update_message(interaction, from_modal=True)
            await interaction.followup.send(
                "✅ Conteúdo gerado e aplicado ao embed!", ephemeral=True)
        else:
            await interaction.followup.send(
                "❌ Desculpe, não foi possível gerar o conteúdo.",
                ephemeral=True)


# --- VIEW PRINCIPAL DO CONSTRUTOR DE EMBED ---


class EmbedBuilderView(ui.View):

    def __init__(self, original_interaction: discord.Interaction,
                 target_channel: discord.TextChannel):
        super().__init__(timeout=900)
        self.original_interaction = original_interaction
        self.target_channel = target_channel
        self.embeds: List[discord.Embed] = [
            discord.Embed(title="Novo Embed", description="Comece a editar!")
        ]
        self.current_embed_index = 0
        self.message: Optional[discord.Message] = None
        self._update_dynamic_components()

    def get_current_embed(self) -> discord.Embed:
        return self.embeds[self.current_embed_index]

    def create_panel_embed(self) -> discord.Embed:
        return discord.Embed(
            title="Painel de Criação de Embed",
            description=
            f"Editando **Embed #{self.current_embed_index + 1}** de **{len(self.embeds)}**.\n"
            f"Destino: {self.target_channel.mention}.",
            color=0x2B2D31)

    def _update_dynamic_components(self):
        """Atualiza os componentes que dependem do estado, como o menu e botões."""
        # Atualiza o menu de seleção
        select_menu: ui.Select = self.children[0]
        select_options = [
            discord.SelectOption(label=f"Embed #{i+1}", value=str(i))
            for i in range(len(self.embeds))
        ]
        select_menu.options = select_options or [
            discord.SelectOption(label="N/A", value="0")
        ]
        select_menu.placeholder = f"Editando Embed #{self.current_embed_index + 1}"

        # Atualiza o estado do botão de apagar
        remove_button: ui.Button = self.children[2]
        remove_button.disabled = len(self.embeds) <= 1

    async def update_message(self,
                             interaction: discord.Interaction,
                             from_modal: bool = False):
        self._update_dynamic_components()
        panel_embed = self.create_panel_embed()
        embeds_to_show = [panel_embed, self.get_current_embed()]

        if from_modal:
            # Se a interação veio de um modal, ela já foi respondida (defer).
            # Usamos o followup para editar a mensagem original do painel.
            if self.message:
                await self.message.edit(embeds=embeds_to_show, view=self)
        else:
            # Se veio de um botão/select, a interação é nova e pode ser editada diretamente.
            await interaction.response.edit_message(embeds=embeds_to_show,
                                                    view=self)

    # --- Componentes e Callbacks (Método Decorado e Estável) ---

    @ui.select(placeholder="Selecione um Embed", row=0)
    async def select_embed(self, interaction: discord.Interaction,
                           select: ui.Select):
        self.current_embed_index = int(select.values[0])
        await self.update_message(interaction)

    @ui.button(label="Adicionar Embed",
               emoji="➕",
               style=discord.ButtonStyle.success,
               row=1)
    async def add_embed(self, interaction: discord.Interaction,
                        button: ui.Button):
        if len(self.embeds) >= 10:
            return await interaction.response.send_message(
                "Limite de 10 embeds atingido.",
                ephemeral=True,
                delete_after=5)
        self.embeds.append(
            discord.Embed(description=f"Novo Embed #{len(self.embeds) + 1}"))
        self.current_embed_index = len(self.embeds) - 1
        await self.update_message(interaction)

    @ui.button(label="Apagar Embed",
               emoji="🗑️",
               style=discord.ButtonStyle.danger,
               row=1)
    async def remove_embed(self, interaction: discord.Interaction,
                           button: ui.Button):
        self.embeds.pop(self.current_embed_index)
        self.current_embed_index = min(self.current_embed_index,
                                       len(self.embeds) - 1)
        await self.update_message(interaction)

    @ui.button(label="Gerar com IA",
               emoji="✨",
               style=discord.ButtonStyle.primary,
               row=1)
    async def generate_with_ai(self, interaction: discord.Interaction,
                               button: ui.Button):
        await interaction.response.send_modal(AIGenerateModal(self))

    @ui.button(label="Título",
               emoji="✏️",
               style=discord.ButtonStyle.secondary,
               row=2)
    async def edit_title(self, interaction: discord.Interaction,
                         button: ui.Button):
        await interaction.response.send_modal(EditTitleModal(self))

    @ui.button(label="Descrição",
               emoji="📄",
               style=discord.ButtonStyle.secondary,
               row=2)
    async def edit_description(self, interaction: discord.Interaction,
                               button: ui.Button):
        await interaction.response.send_modal(EditDescriptionModal(self))

    @ui.button(label="Cor",
               emoji="🎨",
               style=discord.ButtonStyle.secondary,
               row=2)
    async def edit_color(self, interaction: discord.Interaction,
                         button: ui.Button):
        await interaction.response.send_modal(EditColorModal(self))

    @ui.button(label="Autor",
               emoji="👤",
               style=discord.ButtonStyle.secondary,
               row=3)
    async def edit_author(self, interaction: discord.Interaction,
                          button: ui.Button):
        await interaction.response.send_modal(EditAuthorModal(self))

    @ui.button(label="Imagem/Thumb",
               emoji="🖼️",
               style=discord.ButtonStyle.secondary,
               row=3)
    async def edit_image(self, interaction: discord.Interaction,
                         button: ui.Button):
        await interaction.response.send_modal(EditImageModal(self))

    @ui.button(label="Rodapé",
               emoji="🦶",
               style=discord.ButtonStyle.secondary,
               row=3)
    async def edit_footer(self, interaction: discord.Interaction,
                          button: ui.Button):
        await interaction.response.send_modal(EditFooterModal(self))

    @ui.button(label="Campos",
               emoji="➕",
               style=discord.ButtonStyle.secondary,
               row=3)
    async def edit_fields(self, interaction: discord.Interaction,
                          button: ui.Button):
        await interaction.response.send_message(
            "<:1156062066411589652:1391438221589610627> Funcionalidade de editar campos ainda em desenvolvimento.",
            ephemeral=True,
            delete_after=5)

    @ui.button(label="Importar JSON",
               emoji="📥",
               style=discord.ButtonStyle.grey,
               row=4)
    async def import_json(self, interaction: discord.Interaction,
                          button: ui.Button):
        await interaction.response.send_modal(ImportJsonModal(self))

    @ui.button(label="Exportar JSON",
               emoji="📤",
               style=discord.ButtonStyle.grey,
               row=4)
    async def export_json(self, interaction: discord.Interaction,
                          button: ui.Button):
        json_string = json.dumps(
            {"embeds": [e.to_dict() for e in self.embeds]},
            indent=4,
            ensure_ascii=False)
        file_data = BytesIO(json_string.encode('utf-8'))
        file = discord.File(file_data, filename="embeds.json")
        await interaction.response.send_message(
            "Aqui está o JSON dos seus embed(s):", file=file, ephemeral=True)

    @ui.button(label="Enviar Embeds",
               emoji="🚀",
               style=discord.ButtonStyle.primary,
               row=4)
    async def send_embeds(self, interaction: discord.Interaction,
                          button: ui.Button):
        await interaction.response.defer(ephemeral=True)
        try:
            await self.target_channel.send(embeds=self.embeds)
            await interaction.followup.send(
                f"✅ Embeds enviados com sucesso para {self.target_channel.mention}!",
                ephemeral=True)
            self.stop()
        except Exception as e:
            await interaction.followup.send(f"❌ Ocorreu um erro: {e}",
                                            ephemeral=True)


def setup_embed_builder_command(tree: app_commands.CommandTree):

    @tree.command(
        name="embed",
        description="📝 [STAFF] Abre o painel interativo para criar embeds.")
    @app_commands.describe(
        canal="O canal para onde o(s) embed(s) será(ão) enviado(s).")
    async def embed(interaction: discord.Interaction,
                    canal: discord.TextChannel):
        if not (isinstance(interaction.user, discord.Member)
                and staff_system.is_staff(interaction.user)):
            return await interaction.response.send_message(
                "❌ Você não tem permissão para usar este comando.",
                ephemeral=True)

        view = EmbedBuilderView(interaction, canal)
        await interaction.response.send_message(
            embeds=[view.create_panel_embed(),
                    view.get_current_embed()],
            view=view,
            ephemeral=True)
        view.message = await interaction.original_response()
