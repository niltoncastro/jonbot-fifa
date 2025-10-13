class GameState:
    def __init__(self, codigo_partida, codigo_liga):
        self.sigla_estado_partida = None
        self.codigo_partida_atual = codigo_partida
        self.codigo_liga = codigo_liga
        self.last_start_time = None
        self.match_status = None
        self.placar_casa = "0"
        self.placar_visitante = "0"
        self.resultado_partida = None
        self.time_casa = None
        self.time_visitante = None
        self.flg_aposta = None
        self.nome_liga = None

    def reset_state(self):
        """Reseta todas as variáveis do estado para seus valores padrão."""
        self.match_status = None
        self.sigla_estado_partida = None
        self.placar_casa = "0"
        self.placar_visitante = "0"
        self.resultado_partida = None
        self.time_casa = None
        self.time_visitante = None
        self.flg_aposta = None
        self.nome_liga = None


# Dicionário para armazenar o estado de cada torneio ou partida
game_states = {}
