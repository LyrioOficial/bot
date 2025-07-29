# staff_commands.py
import discord
from discord import app_commands
# --- IMPORTAÇÕES DO AUTOMOD COMENTADAS PARA EVITAR O ERRO ---
# from discord import AutoModRule, AutoModTrigger, AutoModAction, AutoModRuleEventType, AutoModTriggerType, AutoModActionType
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Union
from goodmorning import coin_system
from config_system import config_system
from automod_system import automod

class StaffCommands:
    def __init__(self):
        self.staff_roles = ["Staff", "Moderador", "Admin", "Owner", "Administrador"]
        self.log_file = "staff_logs.json"
        self.warns_file = "user_warns.json"
        self.mutes_file = "user_mutes.json"
        self.ensure_files()

    def ensure_files(self):
        files = [self.log_file, self.warns_file, self.mutes_file]
        for file in files:
            if not os.path.exists(file):
                with open(file, 'w', encoding='utf-8') as f:
                    json.dump({} if file != self.log_file else [], f)

    def log_action(self, staff_id: str, staff_name: str, action: str, target_id: str, target_name: str, amount: int = 0, reason: str = "", extra_data: str = ""):
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except:
            logs = []
        log_entry = {
            "timestamp": datetime.now().isoformat(), "staff_id": staff_id, "staff_name": staff_name, "action": action,
            "target_id": target_id, "target_name": target_name, "amount": amount, "reason": reason, "extra_data": extra_data
        }
        logs.append(log_entry)
        if len(logs) > 1000:
            logs = logs[-1000:]
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)

    def is_staff(self, member: Union[discord.Member, discord.User]) -> bool:
        if isinstance(member, discord.User):
            return False
        if member.guild_permissions.administrator:
            return True
        for role in member.roles:
            if role.name in self.staff_roles:
                return True
        return False

    def get_logs(self, limit: int = 50):
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
            return logs[-limit:][::-1]
        except:
            return []

    def add_warn(self, user_id: str, staff_id: str, reason: str):
        try:
            with open(self.warns_file, 'r', encoding='utf-8') as f:
                warns = json.load(f)
        except:
            warns = {}
        if user_id not in warns:
            warns[user_id] = []
        warn_data = {
            "id": len(warns[user_id]) + 1, "timestamp": datetime.now().isoformat(), "staff_id": staff_id,
            "reason": reason, "active": True
        }
        warns[user_id].append(warn_data)
        with open(self.warns_file, 'w', encoding='utf-8') as f:
            json.dump(warns, f, indent=2, ensure_ascii=False)
        return len(warns[user_id])

    def get_warns(self, user_id: str):
        try:
            with open(self.warns_file, 'r', encoding='utf-8') as f:
                warns = json.load(f)
            return warns.get(user_id, [])
        except:
            return []

    def remove_warn(self, user_id: str, warn_id: int):
        try:
            with open(self.warns_file, 'r', encoding='utf-8') as f:
                warns = json.load(f)
        except:
            return False
        if user_id not in warns:
            return False
        for warn in warns[user_id]:
            if warn["id"] == warn_id and warn["active"]:
                warn["active"] = False
                with open(self.warns_file, 'w', encoding='utf-8') as f:
                    json.dump(warns, f, indent=2, ensure_ascii=False)
                return True
        return False

    def add_mute(self, user_id: str, staff_id: str, duration: int, reason: str):
        try:
            with open(self.mutes_file, 'r', encoding='utf-8') as f:
                mutes = json.load(f)
        except:
            mutes = {}
        mute_until = datetime.now() + timedelta(minutes=duration)
        mutes[user_id] = {
            "timestamp": datetime.now().isoformat(), "staff_id": staff_id, "reason": reason,
            "duration": duration, "mute_until": mute_until.isoformat(), "active": True
        }
        with open(self.mutes_file, 'w', encoding='utf-8') as f:
            json.dump(mutes, f, indent=2, ensure_ascii=False)

    def is_muted(self, user_id: str):
        try:
            with open(self.mutes_file, 'r', encoding='utf-8') as f:
                mutes = json.load(f)
        except:
            return False
        if user_id not in mutes: return False
        mute_data = mutes[user_id]
        if not mute_data.get("active", False): return False
        mute_until = datetime.fromisoformat(mute_data["mute_until"])
        if datetime.now() >= mute_until:
            mute_data["active"] = False
            with open(self.mutes_file, 'w', encoding='utf-8') as f:
                json.dump(mutes, f, indent=2, ensure_ascii=False)
            return False
        return True

    def unmute(self, user_id: str):
        try:
            with open(self.mutes_file, 'r', encoding='utf-8') as f:
                mutes = json.load(f)
        except:
            return False
        if user_id not in mutes: return False
        mutes[user_id]["active"] = False
        with open(self.mutes_file, 'w', encoding='utf-8') as f:
            json.dump(mutes, f, indent=2, ensure_ascii=False)
        return True

staff_system = StaffCommands()

async def send_log_message(interaction: discord.Interaction, embed: discord.Embed):
    log_channel_id = config_system.get_log_channel(str(interaction.guild.id))
    if log_channel_id:
        try:
            log_channel = interaction.guild.get_channel(log_channel_id)
            if log_channel and isinstance(log_channel, discord.TextChannel):
                await log_channel.send(embed=embed)
        except (discord.Forbidden, discord.NotFound):
            pass
        except Exception as e:
            print(f"Erro ao enviar log: {e}")

def setup_staff_commands(tree: app_commands.CommandTree):
    
    automod_group = app_commands.Group(name="automod", description="Comandos para configurar o sistema de moderação automática.")

    @automod_group.command(name="reload", description="🛡️ [Admin] Recarrega as configurações do AutoMod do arquivo settings.json.")
    async def reload_automod(interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Apenas administradores podem usar este comando.", ephemeral=True)
        
        automod.reload_settings()
        await interaction.response.send_message("✅ Configurações do AutoMod recarregadas com sucesso.", ephemeral=True)

    @automod_group.command(name="add-keyword", description="🛡️ [Admin] Adiciona uma palavra-chave à lista de filtros.")
    @app_commands.describe(palavra="A palavra a ser bloqueada.")
    async def add_keyword(interaction: discord.Interaction, palavra: str):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Apenas administradores podem usar este comando.", ephemeral=True)
        
        keyword = palavra.lower().strip()
        if keyword not in automod.settings['nsfw_keywords']:
            automod.settings['nsfw_keywords'].append(keyword)
            automod.save_settings()
            await interaction.response.send_message(f"✅ Palavra-chave `{keyword}` adicionada ao filtro.", ephemeral=True)
        else:
            await interaction.response.send_message(f"⚠️ A palavra-chave `{keyword}` já está no filtro.", ephemeral=True)

    @automod_group.command(name="remove-keyword", description="🛡️ [Admin] Remove uma palavra-chave da lista de filtros.")
    @app_commands.describe(palavra="A palavra a ser removida.")
    async def remove_keyword(interaction: discord.Interaction, palavra: str):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Apenas administradores podem usar este comando.", ephemeral=True)
        
        keyword = palavra.lower().strip()
        if keyword in automod.settings['nsfw_keywords']:
            automod.settings['nsfw_keywords'].remove(keyword)
            automod.save_settings()
            await interaction.response.send_message(f"✅ Palavra-chave `{keyword}` removida do filtro.", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ A palavra-chave `{keyword}` não foi encontrada.", ephemeral=True)
    
    tree.add_command(automod_group)

    # O COMANDO DO AUTOMOD FOI COMENTADO PARA EVITAR O ERRO
    # @tree.command(name="automod-rule-create", description="🛡️ [Admin] Cria uma regra do AutoMod para obter a badge.")
    # @app_commands.describe(
    #     nome="O nome da regra (ex: Filtro de Palavras)",
    #     palavras="Palavras a serem bloqueadas, separadas por vírgula (ex: palavra1,palavra2)",
    #     canal_log="[Opcional] Canal para enviar os alertas do AutoMod."
    # )
    # async def automod_rule_create(interaction: discord.Interaction, nome: str, palavras: str, canal_log: Optional[discord.TextChannel] = None):
        # ... (código do comando removido) ...

    @tree.command(name="setlogchannel", description="🔧 [STAFF] Define o canal para receber os logs de moderação.")
    @app_commands.describe(channel="O canal de texto para onde os logs serão enviados.")
    async def set_log_channel(interaction: discord.Interaction, channel: discord.TextChannel):
        if not staff_system.is_staff(interaction.user):
            await interaction.response.send_message("❌ Você não tem permissão para usar este comando.", ephemeral=True)
            return
        config_system.set_log_channel(str(interaction.guild.id), channel.id)
        embed = discord.Embed(title="✅ Canal de Logs Definido", description=f"O canal de logs foi configurado para {channel.mention}.", color=0x00FF00)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    @tree.command(name="removelogchannel", description="🔧 [STAFF] Desativa o envio de logs de moderação.")
    async def remove_log_channel(interaction: discord.Interaction):
        if not staff_system.is_staff(interaction.user):
            await interaction.response.send_message("❌ Você não tem permissão para usar este comando.", ephemeral=True)
            return
        if config_system.remove_log_channel(str(interaction.guild.id)):
            embed = discord.Embed(title="✅ Logs Desativados", description="O canal de logs foi removido.", color=0x00FF00)
        else:
            embed = discord.Embed(title="⚠️ Nenhum Canal de Log", description="Não havia um canal de logs configurado.", color=0xFF9500)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @tree.command(name="addcoins", description="🪙 [STAFF] Adicionar Orbs a um usuário")
    @app_commands.describe(user="Usuário que receberá os Orbs", amount="Quantidade de Orbs para adicionar", reason="Motivo da adição (opcional)")
    async def add_coins(interaction: discord.Interaction, user: discord.Member, amount: int, reason: Optional[str] = "Não especificado"):
        if not staff_system.is_staff(interaction.user):
            embed = discord.Embed(title="❌ Acesso Negado", description="Você não tem permissão para usar este comando!", color=0xFF0000)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        if amount <= 0:
            embed = discord.Embed(title="❌ Valor Inválido", description="A quantidade deve ser positiva!", color=0xFF0000)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        new_balance = coin_system.add_coins(str(user.id), amount)
        staff_system.log_action(str(interaction.user.id), str(interaction.user), "ADD_COINS", str(user.id), str(user), amount, reason)
        embed = discord.Embed(title="💰 Orbs Adicionados", description=f"**{amount:,}** Orbs foram adicionados com sucesso!", color=0x00FF00)
        embed.add_field(name="👤 Usuário", value=user.mention, inline=True)
        embed.add_field(name="🪙 Novo Saldo", value=f"**{new_balance:,}** Orbs", inline=True)
        embed.add_field(name="👮 Staff", value=interaction.user.mention, inline=True)
        embed.add_field(name="📝 Motivo", value=f"```{reason}```", inline=False)
        embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
        embed.set_footer(text=f"ID: {user.id}")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await send_log_message(interaction, embed.copy())
        try:
            dm_embed = discord.Embed(title="<:pepeflor:1387159299700035646> Você Recebeu Orbs!", description=f"Um membro da staff te beneficiou com **{amount:,}** Orbs à sua conta!", color=0x000000)
            dm_embed.add_field(name="💰 Seu Novo Saldo", value=f"**{new_balance:,}** Orbs", inline=True)
            dm_embed.add_field(name="📝 Motivo", value=reason, inline=False)
            dm_embed.set_footer(text=f"Servidor: {interaction.guild.name}")
            await user.send(embed=dm_embed)
        except:
            pass

    @tree.command(name="warn", description="⚠️ [STAFF] Dar advertência a um usuário")
    @app_commands.describe(user="Usuário que receberá a advertência", reason="Motivo da advertência")
    async def warn_user(interaction: discord.Interaction, user: discord.Member, reason: str):
        if not staff_system.is_staff(interaction.user):
            embed = discord.Embed(title="❌ Acesso Negado", description="Você não tem permissão para usar este comando!", color=0xFF0000)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        if user.id == interaction.user.id:
            embed = discord.Embed(title="❌ Ação Inválida", description="Você não pode dar advertência para si mesmo!", color=0xFF0000)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        warn_count = staff_system.add_warn(str(user.id), str(interaction.user.id), reason)
        staff_system.log_action(str(interaction.user.id), str(interaction.user), "WARN", str(user.id), str(user), warn_count, reason)
        embed = discord.Embed(title="⚠️ Advertência Aplicada", description=f"**{user.display_name}** recebeu uma advertência!", color=0xFF9500)
        embed.add_field(name="👤 Usuário Advertido", value=user.mention, inline=True)
        embed.add_field(name="📊 Total de Warns", value=f"**{warn_count}** advertências", inline=True)
        embed.add_field(name="👮 Staff Responsável", value=interaction.user.mention, inline=True)
        embed.add_field(name="📝 Motivo", value=f"```{reason}```", inline=False)
        if warn_count >= 3:
            embed.add_field(name="🚨 Aviso Importante", value="Este usuário atingiu **3 ou mais advertências**! Considere ações adicionais.", inline=False)
        embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
        embed.set_footer(text=f"ID: {user.id}")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await send_log_message(interaction, embed.copy())
        try:
            dm_embed = discord.Embed(title="⚠️ Você Recebeu uma Advertência", description=f"Você recebeu uma advertência no servidor **{interaction.guild.name}**", color=0xFF9500)
            dm_embed.add_field(name="📝 Motivo", value=reason, inline=False)
            dm_embed.set_footer(text="Por favor, leia as regras do servidor para evitar futuras advertências.")
            await user.send(embed=dm_embed)
        except:
            pass

    @tree.command(name="ban", description="🔨 [STAFF] Banir um usuário do servidor")
    @app_commands.describe(user="Usuário que será banido", reason="Motivo do banimento", delete_messages="Deletar mensagens dos últimos X dias (0-7)")
    async def ban_user(interaction: discord.Interaction, user: discord.Member, reason: str, delete_messages: Optional[int] = 0):
        if not staff_system.is_staff(interaction.user):
            embed = discord.Embed(title="❌ Acesso Negado", description="Você não tem permissão para usar este comando!", color=0xFF0000)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        if user.id == interaction.user.id:
            embed = discord.Embed(title="❌ Ação Inválida", description="Você não pode banir a si mesmo!", color=0xFF0000)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        if user.top_role >= interaction.user.top_role and not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(title="❌ Hierarquia Insuficiente", description="Você não pode banir este usuário devido à hierarquia de cargos!", color=0xFF0000)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        if delete_messages < 0 or delete_messages > 7:
            delete_messages = 0
        embed = discord.Embed(title="🔨 Usuário Banido", description=f"**{user.display_name}** foi banido permanentemente do servidor!", color=0x8B0000)
        embed.add_field(name="👤 Usuário Banido", value=f"{user.mention}\n`{user.display_name}`", inline=True)
        embed.add_field(name="👮 Staff Responsável", value=interaction.user.mention, inline=True)
        embed.add_field(name="🗑️ Mensagens Deletadas", value=f"Últimos **{delete_messages}** dias" if delete_messages > 0 else "Nenhuma", inline=True)
        embed.add_field(name="📝 Motivo", value=f"```{reason}```", inline=False)
        embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
        embed.set_footer(text=f"ID: {user.id}")
        try:
            dm_embed = discord.Embed(title="🔨 Você Foi Banido", description=f"Você foi banido do servidor **{interaction.guild.name}**", color=0x8B0000)
            dm_embed.add_field(name="📝 Motivo", value=reason, inline=False)
            dm_embed.set_footer(text="Se você acredita que este banimento foi injusto, entre em contato com a administração.")
            await user.send(embed=dm_embed)
        except:
            pass
        await user.ban(reason=f"[{interaction.user}] {reason}", delete_message_days=delete_messages)
        staff_system.log_action(str(interaction.user.id), str(interaction.user), "BAN", str(user.id), str(user), delete_messages, reason)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await send_log_message(interaction, embed.copy())

    @tree.command(name="kick", description="👢 [STAFF] Expulsar um usuário do servidor")
    @app_commands.describe(user="Usuário que será expulso", reason="Motivo da expulsão")
    async def kick_user(interaction: discord.Interaction, user: discord.Member, reason: str):
        if not staff_system.is_staff(interaction.user):
            embed = discord.Embed(title="❌ Acesso Negado", description="Você não tem permissão para usar este comando!", color=0xFF0000)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        if user.id == interaction.user.id:
            embed = discord.Embed(title="❌ Ação Inválida", description="Você não pode expulsar a si mesmo!", color=0xFF0000)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        if user.top_role >= interaction.user.top_role and not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(title="❌ Hierarquia Insuficiente", description="Você não pode expulsar este usuário devido à hierarquia de cargos!", color=0xFF0000)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        embed = discord.Embed(title="👢 Usuário Expulso", description=f"**{user.display_name}** foi expulso do servidor!", color=0xFF4500)
        embed.add_field(name="👤 Usuário Expulso", value=f"{user.mention}\n`{user.display_name}`", inline=True)
        embed.add_field(name="👮 Staff Responsável", value=interaction.user.mention, inline=True)
        embed.add_field(name="🔄 Pode Retornar", value="✅ Sim, com novo convite", inline=True)
        embed.add_field(name="📝 Motivo", value=f"```{reason}```", inline=False)
        embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
        embed.set_footer(text=f"ID: {user.id}")
        try:
            dm_embed = discord.Embed(title="👢 Você Foi Expulso", description=f"Você foi expulso do servidor **{interaction.guild.name}**", color=0xFF4500)
            dm_embed.add_field(name="📝 Motivo", value=reason, inline=False)
            dm_embed.set_footer(text="Você pode retornar ao servidor através de um novo convite.")
            await user.send(embed=dm_embed)
        except:
            pass
        await user.kick(reason=f"[{interaction.user}] {reason}")
        staff_system.log_action(str(interaction.user.id), str(interaction.user), "KICK", str(user.id), str(user), 0, reason)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await send_log_message(interaction, embed.copy())

    @tree.command(name="mute", description="🔇 [STAFF] Silenciar um usuário temporariamente")
    @app_commands.describe(user="Usuário que será silenciado", duration="Duração em minutos", reason="Motivo do silenciamento")
    async def mute_user(interaction: discord.Interaction, user: discord.Member, duration: int, reason: str):
        if not staff_system.is_staff(interaction.user):
            embed = discord.Embed(title="❌ Acesso Negado", description="Você não tem permissão para usar este comando!", color=0xFF0000)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        if user.id == interaction.user.id:
            embed = discord.Embed(title="❌ Ação Inválida", description="Você não pode silenciar a si mesmo!", color=0xFF0000)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        if duration <= 0 or duration > 10080:
            embed = discord.Embed(title="❌ Duração Inválida", description="A duração deve ser entre 1 e 10080 minutos (7 dias)!", color=0xFF0000)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        mute_until = discord.utils.utcnow() + timedelta(minutes=duration)
        try:
            await user.timeout(mute_until, reason=f"[{interaction.user}] {reason}")
        except discord.Forbidden:
            embed = discord.Embed(title="❌ Erro de Permissão", description="Não foi possível silenciar este usuário. Verifique as permissões!", color=0xFF0000)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        staff_system.add_mute(str(user.id), str(interaction.user.id), duration, reason)
        staff_system.log_action(str(interaction.user.id), str(interaction.user), "MUTE", str(user.id), str(user), duration, reason)
        if duration < 60:
            time_text = f"{duration} minutos"
        elif duration < 1440:
            hours = duration // 60
            minutes = duration % 60
            time_text = f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"
        else:
            days = duration // 1440
            hours = (duration % 1440) // 60
            time_text = f"{days}d {hours}h" if hours > 0 else f"{days}d"
        embed = discord.Embed(title="🔇 Usuário Silenciado", description=f"**{user.display_name}** foi silenciado temporariamente!", color=0x808080)
        embed.add_field(name="👤 Usuário Silenciado", value=user.mention, inline=True)
        embed.add_field(name="⏰ Duração", value=f"**{time_text}**", inline=True)
        embed.add_field(name="👮 Staff Responsável", value=interaction.user.mention, inline=True)
        embed.add_field(name="🕐 Liberado em", value=f"<t:{int(mute_until.timestamp())}:F>", inline=True)
        embed.add_field(name="📝 Motivo", value=f"```{reason}```", inline=False)
        embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
        embed.set_footer(text=f"ID: {user.id}")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await send_log_message(interaction, embed.copy())
        try:
            dm_embed = discord.Embed(title="🔇 Você Foi Silenciado", description=f"Você foi silenciado no servidor **{interaction.guild.name}**", color=0x808080)
            dm_embed.add_field(name="⏰ Duração", value=time_text, inline=True)
            dm_embed.add_field(name="📝 Motivo", value=reason, inline=False)
            dm_embed.add_field(name="🕐 Será liberado em", value=f"<t:{int(mute_until.timestamp())}:F>", inline=False)
            dm_embed.set_footer(text="Aguarde o tempo do silenciamento passar ou entre em contato com a staff.")
            await user.send(embed=dm_embed)
        except:
            pass

    @tree.command(name="warns", description="📋 [STAFF] Ver advertências de um usuário")
    @app_commands.describe(user="Usuário para verificar advertências")
    async def view_warns(interaction: discord.Interaction, user: discord.Member):
        if not staff_system.is_staff(interaction.user):
            embed = discord.Embed(title="❌ Acesso Negado", description="Você não tem permissão para usar este comando!", color=0xFF0000)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        warns = staff_system.get_warns(str(user.id))
        active_warns = [w for w in warns if w.get("active", True)]
        embed = discord.Embed(title=f"📋 Advertências de {user.display_name}", color=0xFF9500 if active_warns else 0x00FF00)
        embed.add_field(name="📊 Resumo", value=f"**{len(active_warns)}** advertências ativas\n**{len(warns)}** advertências totais", inline=True)
        if not active_warns:
            embed.add_field(name="✅ Status", value="Usuário sem advertências ativas", inline=True)
        else:
            warns_text = ""
            for warn in active_warns[-5:]:
                timestamp = datetime.fromisoformat(warn["timestamp"]).strftime("%d/%m/%Y")
                warns_text += f"**#{warn['id']}** - {timestamp}\n```{warn['reason'][:50]}{'...' if len(warn['reason']) > 50 else ''}```\n"
            embed.add_field(name="⚠️ Advertências Recentes", value=warns_text, inline=False)
        embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
        embed.set_footer(text=f"ID: {user.id}")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @tree.command(name="stafflogs", description="📋 [STAFF] Ver logs das ações da staff")
    @app_commands.describe(limit="Número de logs para mostrar (máximo 10)")
    async def staff_logs(interaction: discord.Interaction, limit: Optional[int] = 5):
        if not staff_system.is_staff(interaction.user):
            embed = discord.Embed(title="❌ Acesso Negado", description="Você não tem permissão para usar este comando!", color=0xFF0000)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        if limit > 10:
            limit = 10
        logs = staff_system.get_logs(limit)
        if not logs:
            embed = discord.Embed(title="📋 Logs da Staff", description="Nenhum log encontrado.", color=0x36393F)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        embed = discord.Embed(title="📋 Logs da Staff", description=f"📊 Exibindo as últimas **{len(logs)}** ações:", color=0xFF6B35)
        action_emojis = {"ADD_COINS": "💰", "REMOVE_COINS": "💸", "SET_COINS": "⚙️", "WARN": "⚠️", "BAN": "🔨", "KICK": "👢", "MUTE": "🔇", "UNMUTE": "🔊", "RESET_DAILY": "🔄"}
        for i, log in enumerate(logs, 1):
            timestamp = datetime.fromisoformat(log["timestamp"]).strftime("%d/%m às %H:%M")
            emoji = action_emojis.get(log["action"], "📝")
            action = log["action"].replace("_", " ").title()
            if log["action"] in ["ADD_COINS", "REMOVE_COINS", "SET_COINS"]:
                value = f"{emoji} **{action}**\n👤 **{log['target_name']}**\n💰 **{log['amount']}** Orbs\n👮 {log['staff_name']}\n📝 {log['reason'][:30]}{'...' if len(log['reason']) > 30 else ''}"
            else:
                value = f"{emoji} **{action}**\n👤 **{log['target_name']}**\n👮 {log['staff_name']}\n📝 {log['reason'][:30]}{'...' if len(log['reason']) > 30 else ''}"
            embed.add_field(name=f"#{i} • {timestamp}", value=value, inline=True)
        embed.set_footer(text=f"📋 Consultado por {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @tree.command(name="serverinfo", description="📊 [STAFF] Ver informações detalhadas do servidor")
    async def server_info(interaction: discord.Interaction):
        if not staff_system.is_staff(interaction.user):
            embed = discord.Embed(title="❌ Acesso Negado", description="Você não tem permissão para usar este comando!", color=0xFF0000)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        guild = interaction.guild
        bots = sum(1 for member in guild.members if member.bot)
        humans = guild.member_count - bots
        online = sum(1 for member in guild.members if member.status != discord.Status.offline and not member.bot)
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        created = guild.created_at.strftime("%d/%m/%Y às %H:%M")
        days_old = (datetime.now() - guild.created_at.replace(tzinfo=None)).days
        embed = discord.Embed(title=f"📊 Informações de {guild.name}", color=0x5865F2)
        embed.add_field(name="👥 Membros", value=f"**Total:** {guild.member_count:,}\n**Humanos:** {humans:,}\n**Bots:** {bots:,}\n**Online:** {online:,}", inline=True)
        embed.add_field(name="📺 Canais", value=f"**Texto:** {text_channels}\n**Voz:** {voice_channels}\n**Categorias:** {categories}\n**Total:** {text_channels + voice_channels}", inline=True)
        embed.add_field(name="🎭 Cargos", value=f"**{len(guild.roles)}** cargos", inline=True)
        embed.add_field(name="📅 Criado em", value=f"{created}\n(**{days_old}** dias atrás)", inline=True)
        embed.add_field(name="👑 Dono", value=guild.owner.mention if guild.owner else "Desconhecido", inline=True)
        embed.add_field(name="🌐 Região", value="Automática", inline=True)
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        embed.set_footer(text=f"ID: {guild.id}")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @tree.command(name="clear", description="🧹 [STAFF] Limpar mensagens de um canal")
    @app_commands.describe(amount="Número de mensagens para deletar (1-100)", user="Deletar apenas mensagens de um usuário específico (opcional)")
    async def clear_messages(interaction: discord.Interaction, amount: int, user: Optional[discord.Member] = None):
        if not staff_system.is_staff(interaction.user):
            embed = discord.Embed(title="❌ Acesso Negado", description="Você não tem permissão para usar este comando!", color=0xFF0000)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        if amount < 1 or amount > 100:
            embed = discord.Embed(title="❌ Quantidade Inválida", description="Você deve especificar entre 1 e 100 mensagens!", color=0xFF0000)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        def check(message):
            if user:
                return message.author == user
            return True
        try:
            deleted = await interaction.channel.purge(limit=amount, check=check)
            staff_system.log_action(str(interaction.user.id), str(interaction.user), "CLEAR", str(user.id) if user else "ALL", str(user) if user else "Todas as mensagens", len(deleted), f"Limpeza no canal {interaction.channel.name}")
            embed = discord.Embed(title="🧹 Mensagens Limpas", description=f"**{len(deleted)}** mensagens foram deletadas com sucesso!", color=0x00FF00)
            embed.add_field(name="📺 Canal", value=interaction.channel.mention, inline=True)
            embed.add_field(name="👤 Usuário Específico", value=user.mention if user else "Todos os usuários", inline=True)
            embed.add_field(name="👮 Staff Responsável", value=interaction.user.mention, inline=True)
            embed.set_footer(text="Sistema de Moderação")
            await interaction.followup.send(embed=embed, ephemeral=True)
            await send_log_message(interaction, embed.copy())
        except discord.Forbidden:
            await interaction.followup.send(embed=discord.Embed(title="❌ Erro de Permissão", description="Não tenho permissão para deletar mensagens neste canal!", color=0xFF0000), ephemeral=True)
        except Exception as e:
            await interaction.followup.send(embed=discord.Embed(title="❌ Erro", description=f"Ocorreu um erro ao deletar as mensagens: {str(e)[:100]}", color=0xFF0000), ephemeral=True)