# automod_system.py
import discord
import json
import os
import re
from datetime import datetime
from typing import Optional

class AutoModSystem:
    # O __init__ agora aceita o client como opcional para ser definido depois
    def __init__(self, client: Optional[discord.Client] = None):
        self.client = client
        self.settings_file = "settings.json"
        self.settings = self.load_settings()
        
        # Variáveis para controle de spam
        self.spam_threshold = 5
        self.user_messages = {}

    def load_settings(self):
        """Carrega as configurações do automod a partir de um arquivo JSON."""
        if os.path.exists(self.settings_file):
            with open(self.settings_file, "r", encoding='utf-8') as f:
                return json.load(f)
        else:
            default_settings = {
                "nsfw_keywords": ["porn", "xxx", "hentai", "nsfw", "lewd", "gore"],
                "phishing_patterns": [
                    r"discorcl.gift", r"dlscord.gift", r"discord-app.com",
                    r"discord-gifts.com", r"steamcommunily.com"
                ]
            }
            with open(self.settings_file, "w", encoding='utf-8') as f:
                json.dump(default_settings, f, indent=4)
            return default_settings

    def save_settings(self):
        """Salva as configurações atuais no arquivo JSON."""
        with open(self.settings_file, "w", encoding='utf-8') as f:
            json.dump(self.settings, f, indent=4)

    def reload_settings(self):
        """Recarrega as configurações do arquivo."""
        self.settings = self.load_settings()

    async def check_message(self, message: discord.Message):
        """Função principal que verifica cada mensagem."""
        if message.author.bot or not isinstance(message.author, discord.Member) or not message.guild:
            return

        if message.author.guild_permissions.administrator:
            return

        for keyword in self.settings.get("nsfw_keywords", []):
            if keyword.lower() in message.content.lower():
                await self.punish_and_log(
                    message, 
                    "Conteúdo Inapropriado Detectado", 
                    f"A mensagem continha a palavra-chave proibida: `{keyword}`."
                )
                return

        for pattern in self.settings.get("phishing_patterns", []):
            if re.search(pattern, message.content, re.IGNORECASE):
                await self.punish_and_log(
                    message, 
                    "Link Malicioso Detectado",
                    f"A mensagem continha um link suspeito que corresponde ao padrão: `{pattern}`."
                )
                return

        user_id = str(message.author.id)
        current_time = datetime.now().timestamp()
        
        if user_id not in self.user_messages:
            self.user_messages[user_id] = []

        self.user_messages[user_id].append(current_time)
        self.user_messages[user_id] = [t for t in self.user_messages[user_id] if (current_time - t) <= 10]

        if len(self.user_messages[user_id]) > self.spam_threshold:
            await message.channel.send(f"{message.author.mention}, por favor, evite enviar mensagens em excesso!", delete_after=10)
            self.user_messages[user_id] = []
            return

    async def punish_and_log(self, message: discord.Message, reason_title: str, reason_desc: str):
        try:
            await message.delete()
        except (discord.NotFound, discord.Forbidden):
            pass
            
        from config_system import config_system
        log_channel_id = config_system.get_log_channel(str(message.guild.id))
        if log_channel_id and self.client:
            log_channel = self.client.get_channel(log_channel_id)
            if log_channel:
                embed = discord.Embed(
                    title=f"🛡️ AutoMod: {reason_title}",
                    description=reason_desc,
                    color=discord.Color.red()
                )
                embed.add_field(name="Usuário", value=message.author.mention, inline=True)
                embed.add_field(name="Canal", value=message.channel.mention, inline=True)
                embed.add_field(name="Conteúdo Original", value=f"```\n{message.content[:1000]}\n```", inline=False)
                embed.set_footer(text=f"ID do Usuário: {message.author.id}")
                embed.timestamp = datetime.now()
                try:
                    await log_channel.send(embed=embed)
                except discord.Forbidden:
                    pass

        try:
            dm_embed = discord.Embed(
                title="Sua mensagem foi removida",
                description=f"Sua mensagem no servidor **{message.guild.name}** foi removida automaticamente pelo seguinte motivo: **{reason_title}**.",
                color=discord.Color.orange()
            )
            await message.author.send(embed=dm_embed)
        except discord.Forbidden:
            pass

# --- MUDANÇA: CRIA UMA INSTÂNCIA GLOBAL DO SISTEMA ---
automod = AutoModSystem()