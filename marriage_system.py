# marriage_system.py
import json
import os
from datetime import datetime

class MarriageSystem:
    def __init__(self, filename="marriages.json"):
        """Inicializa o sistema de casamento."""
        self.filename = filename
        self.data = self.load_data()

    def load_data(self):
        """Carrega os dados de casamento do arquivo JSON."""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def save_data(self):
        """Salva os dados de casamento no arquivo JSON."""
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

    def is_married(self, user_id: str):
        """Verifica se um usuário está casado."""
        return user_id in self.data

    def get_partner_id(self, user_id: str):
        """Obtém o ID do parceiro de um usuário."""
        if self.is_married(user_id):
            return self.data[user_id].get("partner_id")
        return None
        
    def get_marriage_data(self, user_id: str):
        """Obtém todos os dados do casamento de um usuário."""
        return self.data.get(user_id)

    def marry(self, user1_id: str, user2_id: str):
        """Casa dois usuários, definindo a afinidade e os cooldowns iniciais."""
        initial_affinity = 20
        # Cooldowns para as ações de afinidade
        cooldowns = {
            "last_kiss": None,
            "last_hug": None,
            "last_pat": None
        }
        self.data[user1_id] = {"partner_id": user2_id, "affinity": initial_affinity, **cooldowns}
        self.data[user2_id] = {"partner_id": user1_id, "affinity": initial_affinity, **cooldowns}
        self.save_data()

    def divorce(self, user_id: str):
        """Realiza o divórcio de um usuário."""
        marriage_data = self.get_marriage_data(user_id)
        if marriage_data:
            partner_id = marriage_data["partner_id"]
            if user_id in self.data:
                del self.data[user_id]
            if partner_id in self.data:
                del self.data[partner_id]
            self.save_data()
            return partner_id
        return None

    def can_perform_action(self, user_id: str, action_type: str) -> bool:
        """Verifica se uma ação de afinidade pode ser realizada (cooldown diário)."""
        marriage_data = self.get_marriage_data(user_id)
        if not marriage_data:
            return False
        
        last_action_timestamp = marriage_data.get(f"last_{action_type}")
        if not last_action_timestamp:
            return True # Nunca realizou a ação
            
        last_date = datetime.fromisoformat(last_action_timestamp).date()
        return last_date < datetime.now().date()

    def record_and_update_affinity(self, user_id: str, action_type: str, points: int) -> bool:
        """Registra a ação e atualiza a afinidade para o casal."""
        if not self.can_perform_action(user_id, action_type):
            return False

        partner_id = self.get_partner_id(user_id)
        if not partner_id:
            return False

        # Atualiza o timestamp para ambos
        timestamp = datetime.now().isoformat()
        self.data[user_id][f"last_{action_type}"] = timestamp
        self.data[partner_id][f"last_{action_type}"] = timestamp
        
        # Atualiza a afinidade para ambos (com limite de 20)
        new_affinity = min(self.data[user_id]["affinity"] + points, 20)
        self.data[user_id]["affinity"] = new_affinity
        self.data[partner_id]["affinity"] = new_affinity
        
        self.save_data()
        return True

# Instância global do sistema de casamento
marriage_system = MarriageSystem()