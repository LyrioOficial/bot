# config_system.py
import json
import os

class ConfigSystem:
    def __init__(self, filename="server_configs.json"):
        """Inicializa o sistema de configuração."""
        self.filename = filename
        self.data = self.load_data()

    def load_data(self):
        """Carrega os dados de configuração do arquivo JSON."""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def save_data(self):
        """Salva os dados de configuração no arquivo JSON."""
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

    def get_guild_config(self, guild_id: str):
        """Obtém a configuração para um servidor específico."""
        return self.data.get(guild_id, {})

    def set_log_channel(self, guild_id: str, channel_id: int):
        """Define o canal de log para um servidor."""
        if guild_id not in self.data:
            self.data[guild_id] = {}
        self.data[guild_id]["log_channel"] = channel_id
        self.save_data()

    def get_log_channel(self, guild_id: str):
        """Obtém o ID do canal de log para um servidor."""
        return self.get_guild_config(guild_id).get("log_channel")

    def remove_log_channel(self, guild_id: str):
        """Remove a configuração do canal de log para um servidor."""
        if guild_id in self.data and "log_channel" in self.data[guild_id]:
            del self.data[guild_id]["log_channel"]
            self.save_data()
            return True
        return False

# Instância global do sistema de configuração
config_system = ConfigSystem()