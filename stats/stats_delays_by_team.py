from collections import defaultdict, Counter
from statistics import mean


def stats_delays_by_team(results_list):
    match_delay_data = defaultdict(lambda: defaultdict(Counter))

    # Variáveis para rastrear atrasos
    current_delays = defaultdict(int)  # Armazena o atraso atual por resultado

    for time, resultado in results_list:
        # Atualizar atrasos para cada tipo de resultado
        for res in ["Venceu", "Perdeu", "Empatou"]:
            if res == resultado:
                # Se o resultado ocorreu, zerar o atraso atual
                delay = current_delays[res]
                if delay > 0:
                    match_delay_data[time][res][delay] += 1
                current_delays[res] = 0
            else:
                # Se o resultado não ocorreu, incrementar o atraso atual
                current_delays[res] += 1

        # Atualizar "current_delay" no dicionário de dados
        for res in ["Venceu", "Perdeu", "Empatou"]:
            match_delay_data[time][res]["current_delay"] = current_delays[res]

    # Finalizar atrasos pendentes
    for time in match_delay_data:
        for res in match_delay_data[time]:
            delay = match_delay_data[time][res]["current_delay"]
            if delay > 0:
                match_delay_data[time][res][delay] += 1
                match_delay_data[time][res]["current_delay"] = delay

    # Preparar os dados detalhados
    detailed_data = []

    for time, results in match_delay_data.items():
        for resultado, counters in results.items():
            delays = [delay_len for delay_len in counters if isinstance(delay_len, int)]

            # Calcular métricas para atrasos
            current_delay = counters["current_delay"] if "current_delay" in counters else 0
            max_delay = max(delays) if delays else 0
            mean_delay = int(mean(delays)) if delays else 0
            dif_atr_media_atual = mean_delay - current_delay
            dif_atr_media_max = max_delay - mean_delay

            detailed_data.append({
                "nome_time": time,
                "resultado": resultado,
                "atr_atual": current_delay,
                "atr_media": mean_delay,
                "atr_maximo": max_delay,
                "dif_atr_media_atual": dif_atr_media_atual,
                "dif_atr_media_max": dif_atr_media_max,
            })

    return detailed_data
