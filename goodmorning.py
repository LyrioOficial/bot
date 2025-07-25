# goodmorning.py
import discord
from discord import app_commands
import random
import json
import os
from datetime import datetime, timedelta
from typing import Optional

# Importa os sistemas
from marriage_system import marriage_system

class CoinSystem:
    def __init__(self, filename="user_coins.json"):
        self.filename = filename
        self.data = self.load_data()

    def load_data(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_data(self):
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

    def add_coins(self, user_id: str, amount: int):
        if user_id not in self.data:
            self.data[user_id] = {"coins": 0, "last_daily": None, "total_earned": 0, "roleplay_counts": {}}
        
        if "coins" not in self.data[user_id]:
            self.data[user_id]["coins"] = 0
        if "total_earned" not in self.data[user_id]:
            self.data[user_id]["total_earned"] = 0

        self.data[user_id]["coins"] += amount
        self.data[user_id]["total_earned"] += amount
        self.save_data()
        return self.data[user_id]["coins"]

    def remove_coins(self, user_id: str, amount: int):
        if user_id not in self.data or self.data[user_id].get("coins", 0) < amount:
            return False
        self.data[user_id]["coins"] -= amount
        self.save_data()
        return True

    def get_coins(self, user_id: str):
        if user_id not in self.data:
            return 0
        return self.data[user_id].get("coins", 0)

    def increment_roleplay_count(self, user_id: str, action_type: str):
        if user_id not in self.data:
            self.data[user_id] = {"coins": 0, "last_daily": None, "total_earned": 0, "roleplay_counts": {}}
        if "roleplay_counts" not in self.data[user_id]:
            self.data[user_id]["roleplay_counts"] = {}
        if action_type not in self.data[user_id]["roleplay_counts"]:
            self.data[user_id]["roleplay_counts"][action_type] = 0
        self.data[user_id]["roleplay_counts"][action_type] += 1
        self.save_data()

    def get_roleplay_counts(self, user_id: str):
        if user_id not in self.data:
            return {}
        return self.data[user_id].get("roleplay_counts", {})

    def can_claim_daily(self, user_id: str):
        if user_id not in self.data: return True
        last_daily = self.data[user_id].get("last_daily")
        if not last_daily: return True
        last_date = datetime.fromisoformat(last_daily).date()
        return last_date < datetime.now().date()

    def claim_daily(self, user_id: str):
        if not self.can_claim_daily(user_id): return False, 0
        amount = random.randint(50, 150)
        self.add_coins(user_id, amount)
        if user_id not in self.data:
            self.data[user_id] = {"coins": 0, "last_daily": None, "total_earned": 0}
        self.data[user_id]["last_daily"] = datetime.now().isoformat()
        self.save_data()
        return True, amount

    def can_use_new_phrase(self, user_id: str):
        if user_id not in self.data: return True
        last_phrase = self.data[user_id].get("last_new_phrase")
        if not last_phrase: return True
        last_date = datetime.fromisoformat(last_phrase).date()
        return last_date < datetime.now().date()

    def use_new_phrase(self, user_id: str):
        if not self.can_use_new_phrase(user_id): return False, 0
        amount = random.randint(5, 15)
        self.add_coins(user_id, amount)
        if user_id not in self.data:
            self.data[user_id] = {"coins": 0, "last_daily": None, "total_earned": 0, "last_new_phrase": None}
        self.data[user_id]["last_new_phrase"] = datetime.now().isoformat()
        self.save_data()
        return True, amount

coin_system = CoinSystem()

class GoodMorningView(discord.ui.View):
    def __init__(self, user_id: str, user_mention: str):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.user_mention = user_mention
        self.has_claimed = False
        self.has_used_new_phrase = False
        self.message = None

    async def on_timeout(self):
        if self.message:
            for item in self.children:
                item.disabled = True
            expired_embed = self.create_embed()
            expired_embed.set_footer(text="Esta sessão expirou. Use /daily novamente.")
            try:
                await self.message.edit(embed=expired_embed, view=self)
            except discord.NotFound:
                pass

    def get_greeting_phrases(self):
        greetings = ["☀️ Bom dia! Que seu dia seja repleto de alegria!", "🌅 Bom dia! Um novo dia, novas oportunidades!", "🌞 Bom dia! Que a energia positiva te acompanhe!", "🌻 Bom dia! Desperte com gratidão e determinação!", "🌈 Bom dia! Hoje é um ótimo dia para ser feliz!", "☕ Bom dia! Que seu café seja forte e seu dia seja incrível!", "🦋 Bom dia! Transforme cada momento em algo especial!", "🌺 Bom dia! Floresça onde você estiver plantado!", "✨ Bom dia! Brilhe como a estrela que você é!", "🎵 Bom dia! Que sua vida seja uma música feliz!"]
        return random.choice(greetings)

    def get_motivational_quote(self):
        quotes = ["💪 'O sucesso nasce do querer, da determinação e persistência em se chegar a um objetivo.'", "🚀 'Acredite em si próprio e chegará um dia em que os outros não terão outra escolha senão acreditar com você.'", "🌟 'O que nos move é a busca da felicidade, é acreditar que vale a pena viver.'", "🎯 'Grandes realizações são possíveis quando se dá importância aos pequenos começos.'", "🔥 'A persistência é o caminho do êxito.'", "🌱 'Cada dia é uma nova oportunidade de crescer e se tornar uma versão melhor de si mesmo.'", "⚡ 'A força não vem da capacidade física. Vem de uma vontade indomável.'", "🏆 'O futuro pertence àqueles que acreditam na beleza de seus sonhos.'", "💎 'Seja você mesmo, todos os outros já existem.'", "🌍 'A mudança que você quer ver no mundo, comece em você.'"]
        return random.choice(quotes)

    def create_embed(self):
        current_coins = coin_system.get_coins(self.user_id)
        embed = discord.Embed(title="🌅 Bom Dia!", description=f"{self.get_greeting_phrases()}\n\n{self.user_mention}", color=0xFFD700)
        embed.add_field(name="💭 Frase Motivacional", value=self.get_motivational_quote(), inline=False)
        embed.add_field(name="🪙 Seus Orbs", value=f"**{current_coins}** Orbs", inline=True)
        if coin_system.can_claim_daily(self.user_id):
            embed.add_field(name="🎁 Recompensa Diária", value="Disponível! Clique no botão abaixo.", inline=True)
        else:
            embed.add_field(name="⏰ Próxima Recompensa", value="Disponível amanhã!", inline=True)
        if coin_system.can_use_new_phrase(self.user_id) and not self.has_used_new_phrase:
            embed.add_field(name="✨ Nova Frase", value="Disponível! (5-15 Orbs)", inline=True)
        else:
            embed.add_field(name="🔄 Nova Frase", value="Usada hoje!", inline=True)
        embed.set_footer(text="💰 Ganhe Orbs interagindo com o bot!")
        embed.timestamp = discord.utils.utcnow()
        return embed

    @discord.ui.button(label="🎁 Recompensa Diária", style=discord.ButtonStyle.primary, emoji="💰")
    async def daily_reward_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != int(self.user_id):
            await interaction.response.send_message("<:policial:1387164051586682942> Esta recompensa não é para você!", ephemeral=True)
            return
        if self.has_claimed:
            await interaction.response.send_message("<:policial:1387164051586682942> Você já coletou sua recompensa diária!", ephemeral=True)
            return
        success, amount = coin_system.claim_daily(self.user_id)
        if not success:
            await interaction.response.send_message("<:policial:1387164051586682942> Você já coletou sua recompensa diária hoje! Volte amanhã.", ephemeral=True)
            return
        self.has_claimed = True
        button.disabled = True
        button.label = "✅ Coletado!"
        button.style = discord.ButtonStyle.success
        new_embed = self.create_embed()
        total_coins = coin_system.get_coins(self.user_id)
        success_embed = discord.Embed(title="Recompensa Coletada!", description=f"Você ganhou **{amount} Orbs**!\n\nTotal: **{total_coins} Orbs** 🪙", color=0x00FF00)
        success_embed.set_footer(text="Volte amanhã para mais recompensas!")
        await interaction.response.edit_message(embed=new_embed, view=self)
        await interaction.followup.send(embed=success_embed, ephemeral=True)

    @discord.ui.button(label="📊 Estatísticas", style=discord.ButtonStyle.secondary, emoji="📈")
    async def stats_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != int(self.user_id):
            await interaction.response.send_message("<:policial:1387164051586682942> Estas estatísticas não são suas!", ephemeral=True)
            return
        await interaction.response.send_message("Use o comando `/perfil` para ver suas estatísticas completas!", ephemeral=True)

    @discord.ui.button(label="🔄 Nova Frase", style=discord.ButtonStyle.secondary, emoji="✨")
    async def new_phrase_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != int(self.user_id):
            await interaction.response.send_message("<:pepebravo:1387163775810928782> Este botão não é para você, seu bobão!", ephemeral=True)
            return
        if self.has_used_new_phrase:
            await interaction.response.send_message("<:policial:1387164051586682942> Você já usou a nova frase hoje!", ephemeral=True)
            return
        success, coins_earned = coin_system.use_new_phrase(str(interaction.user.id))
        if not success:
            await interaction.response.send_message("<:policial:1387164051586682942> Você já gerou uma nova frase hoje! Volte amanhã para gerar outra.", ephemeral=True)
            return
        self.has_used_new_phrase = True
        button.disabled = True
        button.label = "Usada hoje!"
        button.style = discord.ButtonStyle.success
        new_embed = self.create_embed()
        await interaction.response.edit_message(embed=new_embed, view=self)
        await interaction.followup.send(f"✨ Nova frase gerada! Você ganhou **{coins_earned} Orbs** por interagir! 🪙", ephemeral=True)

class ProposalView(discord.ui.View):
    def __init__(self, proposer: discord.Member, target: discord.Member, cost: int):
        super().__init__(timeout=300)
        self.proposer = proposer
        self.target = target
        self.cost = cost
        self.result = None
        self.message = None

    async def on_timeout(self):
        if self.message:
            for item in self.children:
                item.disabled = True
            try:
                await self.message.edit(content=f"O pedido de casamento de {self.proposer.mention} para {self.target.mention} expirou por falta de resposta.", view=self)
            except discord.NotFound:
                pass

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.target.id:
            await interaction.response.send_message("Seu boboca, não se meta no casamento dos outros.", ephemeral=True)
            return False
        
        if coin_system.get_coins(str(self.target.id)) < self.cost:
            await interaction.response.send_message(f"Você não pode aceitar, pois não tem **{self.cost:,} Orbs** necessários!", ephemeral=True)
            self.result = "no_coins"
            self.stop()
            return False
        return True

    @discord.ui.button(label="Aceitar", style=discord.ButtonStyle.success, emoji="💍")
    async def accept_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.result = True
        self.stop()
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Recusar", style=discord.ButtonStyle.danger, emoji="💔")
    async def decline_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.result = False
        self.stop()
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(view=self)

class DivorceConfirmationView(discord.ui.View):
    def __init__(self, interaction: discord.Interaction):
        super().__init__(timeout=60)
        self.interaction = interaction
        self.confirmed = False
    
    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.interaction.edit_original_response(content="Perdeu o time, paizão", view=self)
        except discord.NotFound:
            pass

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.interaction.user.id

    @discord.ui.button(label="Confirmar Divórcio", style=discord.ButtonStyle.danger)
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.confirmed = True
        self.stop()
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(content="💔 Processando divórcio...", view=self)

    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.secondary)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(content="Operação cancelada.", view=self)

def setup_goodmorning_command(tree: app_commands.CommandTree):
    interagir_group = app_commands.Group(name="interagir", description="Interaja com outros usuários!")

    @tree.command(name="daily", description="Pegue sua recompensa diária de hoje!")
    async def goodmorning_command(interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        user_mention = interaction.user.mention
        view = GoodMorningView(user_id, user_mention)
        embed = view.create_embed()
        if interaction.client.user.avatar:
            embed.set_thumbnail(url=interaction.client.user.avatar.url)
        await interaction.response.send_message(embed=embed, view=view)
        view.message = await interaction.original_response()

    @tree.command(name="perfil", description="Veja seu perfil, Orbs e status de casamento! 🤵👰")
    @app_commands.describe(user="Opcional: veja o perfil de outro usuário.")
    async def profile_command(interaction: discord.Interaction, user: Optional[discord.Member] = None):
        target_user = user or interaction.user
        user_id = str(target_user.id)
        
        embed = discord.Embed(title=f"👤 Perfil de {target_user.display_name}", description=target_user.mention, color=0x7289DA)
        if target_user.avatar:
            embed.set_thumbnail(url=target_user.avatar.url)

        # Dados de Orbs
        current_coins = coin_system.get_coins(user_id)
        total_earned = coin_system.data.get(user_id, {}).get("total_earned", 0)
        embed.add_field(name="💰 Saldo Atual", value=f"**{current_coins:,}** Orbs", inline=True)
        embed.add_field(name="📈 Total Ganho", value=f"**{total_earned:,}** Orbs", inline=True)
        
        # Dados do Casamento
        marriage_data = marriage_system.get_marriage_data(user_id)
        if marriage_data:
            partner_id = marriage_data["partner_id"]
            affinity = marriage_data["affinity"]
            try:
                partner_member = await interaction.guild.fetch_member(int(partner_id))
                embed.add_field(name="💍 Estado Civil", value=f"Casado(a) com {partner_member.mention}", inline=False)
                embed.add_field(name="💕 Pontos de Afinidade", value=f"**{affinity}** / 20", inline=True)
            except discord.NotFound:
                 embed.add_field(name="💍 Estado Civil", value="Casado(a) com um mistério (usuário não encontrado)", inline=False)
        else:
            embed.add_field(name="💍 Estado Civil", value="Solteiro(a)", inline=False)

        # Dados de Interações Recebidas
        counts = coin_system.get_roleplay_counts(user_id)
        kisses = counts.get('kiss', 0)
        hugs = counts.get('hug', 0)
        pats = counts.get('pat', 0)
        
        if kisses > 0 or hugs > 0 or pats > 0:
            counts_text = f"😘 Beijos: **{kisses}**\n🤗 Abraços: **{hugs}**\n🥰 Cafunés: **{pats}**"
            embed.add_field(name="💖 Interações Recebidas", value=counts_text, inline=False)

        # Daily
        can_claim = coin_system.can_claim_daily(user_id)
        embed.add_field(name="🎁 Recompensa Diária", value="✅ Disponível!" if can_claim else "⏰ Disponível amanhã!", inline=True)
        embed.set_footer(text=f"ID do Usuário: {user_id}")
        embed.timestamp = discord.utils.utcnow()
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    @tree.command(name="casar", description="💍 Peça alguém em casamento!")
    @app_commands.describe(alvo="A pessoa com quem você quer casar.")
    async def marry_command(interaction: discord.Interaction, alvo: discord.Member):
        proposer = interaction.user
        cost = 25000

        if alvo.id == proposer.id:
            await interaction.response.send_message("Tá com muito amor próprio.", ephemeral=True)
            return
        if alvo.bot:
            await interaction.response.send_message("Você não pode se casar com um bot!", ephemeral=True)
            return
        if marriage_system.is_married(str(proposer.id)):
            await interaction.response.send_message("Você já está casado(a)! Use `/divorciar` primeiro.", ephemeral=True)
            return
        if marriage_system.is_married(str(alvo.id)):
            await interaction.response.send_message(f"Querendo pegar ele(a)? {alvo.display_name}, ele(a) já é casado, tome cuidado.", ephemeral=True)
            return
        if coin_system.get_coins(str(proposer.id)) < cost:
            await interaction.response.send_message(f"Você não tem Orbs o suficiente! O casamento custa **{cost:,} Orbs**.", ephemeral=True)
            return
        if coin_system.get_coins(str(alvo.id)) < cost:
            await interaction.response.send_message(f"Infelizmente, {alvo.display_name}, não possui os **{cost:,} Orbs** necessários para casar.", ephemeral=True)
            return

        view = ProposalView(proposer, alvo, cost)
        
        proposal_text = (
            f"💍 | {alvo.mention} Você recebeu uma proposta de casamento de {proposer.mention}!\n\n"
            f"💵 | Para aceitar, clique no 💍! Mas lembrando, o custo de um casamento é **50.000 Orbs** ({cost:,} para cada usuário) "
            f"e você perde **dois pontos de afinidade** todos os dias (cada casamento começa com 20 pontos), sendo possível ganhar pontos "
            f"enviando cartinhas de amor e usando ações fofinhas nos comandos de roleplay. Se você chegar em zero pontos, o seu casamento acaba...\n\n"
            f"<:pepeanalise:1387206432553959596> | O sistema de casamento pode mudar ao longo do tempo, então os valores podem ser alterados no futuro, fique de olho nas novidades!"
        )

        await interaction.response.send_message(content=proposal_text, view=view)
        view.message = await interaction.original_response()
        
        await view.wait()

        if view.result == "no_coins":
            await view.message.edit(content=f"{proposer.mention}, seu pedido foi recusado pois {alvo.mention} não tinha os Orbs necessários no momento do aceite.", view=None)
            return

        if view.result is True:
            coin_system.remove_coins(str(proposer.id), cost)
            coin_system.remove_coins(str(alvo.id), cost)
            marriage_system.marry(str(proposer.id), str(alvo.id))
            await view.message.edit(content=f"🎉 Parabéns, {proposer.mention} e {alvo.mention}!", view=None)
            await interaction.followup.send(f"Parabéns! {proposer.mention} e {alvo.mention} agora estão casados! ❤️")

        elif view.result is False:
            await view.message.edit(content=f"💔 Que pena, {proposer.mention}...", view=None)
            await interaction.followup.send(f"{alvo.mention} recusou o pedido de casamento de {proposer.mention}.")
        
    @tree.command(name="divorciar", description="💔 Termine seu casamento atual.")
    async def divorce_command(interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        if not marriage_system.is_married(user_id):
            await interaction.response.send_message("Você não está casado!", ephemeral=True)
            return
        partner_id = marriage_system.get_partner_id(user_id)
        try:
            partner = await interaction.guild.fetch_member(int(partner_id))
            partner_mention = partner.mention
        except (discord.NotFound, TypeError):
            partner_mention = "alguém que já não está mais por aqui"
        view = DivorceConfirmationView(interaction)
        await interaction.response.send_message(f"Vish, eu entendo que o amor não foi tão forte, mas, se decidir clicar no botão abaixo, vão se divorciar totalmente. Tem certeza que quer se divorciar dele(a) {partner_mention}?", view=view, ephemeral=True)
        await view.wait()
        if view.confirmed:
            marriage_system.divorce(user_id)
            await interaction.followup.send(f"{interaction.user.mention} se divorciou de {partner_mention}. A vida continua...")

    @tree.command(name="ranking", description="🏆 Veja os rankings de Orbs e de casais do servidor!")
    async def ranking(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        # --- RANKING DE RIQUEZA ---
        all_users_data = coin_system.data
        richest_users = sorted(all_users_data.items(), key=lambda item: item[1].get('coins', 0), reverse=True)
        
        richest_desc = ""
        for i, (user_id, data) in enumerate(richest_users[:3]):
            user = interaction.guild.get_member(int(user_id))
            if user:
                medals = ["🥇", "🥈", "🥉"]
                richest_desc += f"{medals[i]} {user.mention} - **{data.get('coins', 0):,}** Orbs\n"
        
        if not richest_desc:
            richest_desc = "Ninguém tem Orbs ainda."

        # --- RANKING DE CASAIS ---
        all_marriages_data = marriage_system.data
        processed_couples = set()
        couples_list = []
        for user_id, data in all_marriages_data.items():
            partner_id = data.get("partner_id")
            if user_id not in processed_couples and partner_id not in processed_couples:
                couples_list.append({
                    "user1_id": user_id,
                    "user2_id": partner_id,
                    "affinity": data.get("affinity", 0)
                })
                processed_couples.add(user_id)
                processed_couples.add(partner_id)
        
        top_couples = sorted(couples_list, key=lambda item: item['affinity'], reverse=True)
        
        couples_desc = ""
        for i, couple_data in enumerate(top_couples[:3]):
            user1 = interaction.guild.get_member(int(couple_data["user1_id"]))
            user2 = interaction.guild.get_member(int(couple_data["user2_id"]))
            if user1 and user2:
                medals = ["🥇", "🥈", "🥉"]
                couples_desc += f"{medals[i]} {user1.mention} & {user2.mention} - **{couple_data['affinity']}** de Afinidade ❤️\n"
        
        if not couples_desc:
            couples_desc = "Nenhum casal no servidor ainda."

        embed = discord.Embed(title=f"🏆 Rankings do Servidor {interaction.guild.name}", color=0xFFD700)
        embed.add_field(name="💰 Mais Ricos", value=richest_desc, inline=False)
        embed.add_field(name="💞 Casais do Ano", value=couples_desc, inline=False)
        embed.set_footer(text=f"Ranking gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}")
        
        await interaction.followup.send(embed=embed)

    # --- GRUPO DE COMANDOS DE INTERAÇÃO ---
    @interagir_group.command(name="beijar", description="😘 Dê um beijo em alguém!")
    @app_commands.describe(alvo="A pessoa que você quer beijar.")
    async def beijar(interaction: discord.Interaction, alvo: discord.Member):
        gifs = [
            "https://media.discordapp.net/attachments/1278504005542219900/1387210211726590053/dc5424c13451567db5d9d3d6fe9d0878cca8b11f.gif?ex=685c83af&is=685b322f&hm=38439ae3b55d8da93b274808ca1d5578193d68ad5bdce55b50aa2d4f6716f2be&=",
            "https://media.discordapp.net/attachments/1278504005542219900/1387210211428663317/J19WNqwS8.gif?ex=685c83af&is=685b322f&hm=6115019d4bf87f6b7a3b2e8324f05104a96f228b59bc6caff145260c1aa7f6bd&=",
            "https://media.discordapp.net/attachments/1278504005542219900/1387209806024146994/e1b824eef3ec2f3725cb07cdeb6314dcebc9caf6.png?ex=685c834e&is=685b31ce&hm=bdd34d5c15113507f3e4063155813f7897676535457da5ed664799a9d5793f6f&=&format=webp&quality=lossless"
        ]
        await handle_roleplay_action(interaction, alvo, "beijar", "beijou", random.choice(gifs), "kiss")

    @interagir_group.command(name="abracar", description="🤗 Dê um abraço em alguém!")
    @app_commands.describe(alvo="A pessoa que você quer abraçar.")
    async def abracar(interaction: discord.Interaction, alvo: discord.Member):
        gifs = [
            "https://i.pinimg.com/originals/3e/30/03/3e3003c2a6d2038749a34181a7894a8e.gif",
            "https://i.pinimg.com/originals/c3/11/17/c31117565778845f061e3328e13725f2.gif",
            "https://i.pinimg.com/originals/5e/b9/73/5eb973e6e8da6324a3c1032a56784b29.gif"
        ]
        await handle_roleplay_action(interaction, alvo, "abraçar", "abraçou", random.choice(gifs), "hug")

    @interagir_group.command(name="carinho", description="🥰 Faça um cafuné em alguém!")
    @app_commands.describe(alvo="A pessoa em quem você quer fazer cafuné.")
    async def carinho(interaction: discord.Interaction, alvo: discord.Member):
        gifs = [
            "https://i.pinimg.com/originals/a2/33/c2/a233c2a8f81156637372d8a398327c58.gif",
            "https://i.pinimg.com/originals/ca/36/57/ca36573e23a3f5a135315569477038c3.gif",
            "https://i.pinimg.com/originals/2e/27/41/2e274154407981548a8c43553580554c.gif"
        ]
        await handle_roleplay_action(interaction, alvo, "fazer carinho", "fez carinho em", random.choice(gifs), "pat")

    async def handle_roleplay_action(interaction: discord.Interaction, alvo: discord.Member, action_name: str, action_verb: str, gif_url: str, action_type: str):
        if alvo.id == interaction.user.id:
            await interaction.response.send_message(f"Você não pode {action_name} em si mesmo!", ephemeral=True)
            return
        if alvo.bot:
            await interaction.response.send_message("Você não pode interagir com bots.", ephemeral=True)
            return

        embed = discord.Embed(
            description=f"{interaction.user.mention} {action_verb} {alvo.mention}!",
            color=0x2F3136
        )
        embed.set_image(url=gif_url)
        
        await interaction.response.send_message(embed=embed)
        
        coin_system.increment_roleplay_count(str(alvo.id), action_type)
        
        user_id = str(interaction.user.id)
        partner_id = marriage_system.get_partner_id(user_id)
        
        if partner_id and int(partner_id) == alvo.id:
            affinity_gained = random.randint(1, 2)
            if marriage_system.record_and_update_affinity(user_id, action_type, affinity_gained):
                await interaction.followup.send(f"💕 Por essa ação, você e {alvo.mention} ganharam **+{affinity_gained} ponto(s) de afinidade!**", ephemeral=True)
            else:
                await interaction.followup.send(f"Vocês já demonstraram seu amor com esta ação hoje. Tente outra ou volte amanhã!", ephemeral=True)

    tree.add_command(interagir_group)