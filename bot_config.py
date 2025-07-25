# bot_config.py
import json
import os
from typing import Optional

class BotConfig:
    def __init__(self, filename="bot_config.json"):
        self.filename = filename
        self.data = self.load_data()

    def load_data(self):
        """Carrega a configuração do bot do arquivo JSON."""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def save_data(self):
        """Salva a configuração atual no arquivo JSON."""
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

    def set_presence(self, status: str, activity_type: Optional[str], name: Optional[str], url: Optional[str] = None, emoji: Optional[str] = None):
        """Salva as informações de presença, incluindo o novo campo emoji."""
        self.data['status'] = status
        self.data['activity_type'] = activity_type
        self.data['name'] = name
        self.data['url'] = url
        self.data['emoji'] = emoji  # Novo campo
        self.save_data()

    def get_presence(self):
        """Retorna as informações de presença salvas."""
        return self.data

# Instância global
bot_config = BotConfig()