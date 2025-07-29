# utility_commands.py
import discord
from discord import app_commands
import json
from io import BytesIO

def setup_utility_commands(tree: app_commands.CommandTree):
    
    @tree.context_menu(name="Extrair JSON do Embed")
    async def get_embed_json(interaction: discord.Interaction, message: discord.Message):
        """Extrai os dados de embeds e componentes de uma mensagem para um arquivo JSON."""
        
        # Verifica se a mensagem tem embeds OU componentes
        if not message.embeds and not message.components:
            await interaction.response.send_message("Esta mensagem não contém embeds ou componentes para extrair.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        try:
            # Cria um dicionário para armazenar o resultado final
            output_data = {}

            # 1. Processa os Embeds (se existirem)
            if message.embeds:
                embed_dicts = [embed.to_dict() for embed in message.embeds]
                # Se for só um embed, coloca ele direto. Se for mais de um, coloca numa lista.
                if len(embed_dicts) == 1:
                    output_data = embed_dicts[0]
                else:
                    output_data['embeds'] = embed_dicts

            # 2. Processa os Componentes (se existirem)
            if message.components:
                component_dicts = [component.to_dict() for component in message.components]
                # Adiciona a chave 'components' ao dicionário de saída
                # Se já havia um embed, ele adiciona a chave. Se não, ele cria o dicionário com a chave.
                output_data['components'] = component_dicts
            
            # Formata os dados em uma string JSON bonita
            json_string = json.dumps(output_data, indent=4, ensure_ascii=False)
            
            # Converte a string JSON em um arquivo em memória
            file_data = BytesIO(json_string.encode('utf-8'))
            file = discord.File(file_data, filename="message_data.json")
            
            await interaction.followup.send("Aqui está o código JSON da mensagem:", file=file, ephemeral=True)

        except Exception as e:
            await interaction.followup.send(f"❌ Ocorreu um erro ao extrair o JSON: {e}", ephemeral=True)