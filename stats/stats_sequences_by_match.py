from collections import defaultdict, Counter
from statistics import mean

global time_casa, time_visitante


def stats_sequences_by_match(results_list):
    global time_casa, time_visitante
    match_sequence_data = defaultdict(lambda: defaultdict(Counter))

    # Initialize tracking variables for sequences
    last_result = None
    current_streak = 0
    streaks_by_result = defaultdict(int)

    for time_casa, time_visitante, descricao_resultado in results_list:
        match = f"{time_casa} vs {time_visitante}"
        resultado = descricao_resultado

        if resultado == last_result:
            current_streak += 1
        else:
            if last_result is not None:
                streaks_by_result[last_result] = current_streak
                match_sequence_data[match][last_result][current_streak] += 1
            last_result = resultado
            current_streak = 1

        match_sequence_data[match][resultado]["current_sequence"] = current_streak

    # Finalize the last streak
    if last_result is not None:
        streaks_by_result[last_result] = current_streak
        match_sequence_data[match][last_result][current_streak] += 1

    # Add calculation for additional metrics
    detailed_data = []

    for match, results in match_sequence_data.items():
        for resultado, counters in results.items():
            sequences = [seq_len for seq_len in counters if isinstance(seq_len, int)]

            # Only use the sequence lengths (ignore occurrences) for these calculations
            current_sequence = current_streak if resultado == last_result else 0
            mean_sequence = int(mean(sequences)) if sequences else 0
            max_sequence = max(sequences) if sequences else 0
            dif_seq_media_atual = mean_sequence - current_sequence
            dif_seq_media_max = max_sequence - mean_sequence

            detailed_data.append({
                "time_casa": time_casa,
                "time_visitante": time_visitante,
                "resultado": resultado,
                "seq_atual": current_sequence,
                "seq_media": mean_sequence,
                "seq_maxima": max_sequence,
                "dif_seq_media_atual": dif_seq_media_atual,
                "dif_seq_media_max": dif_seq_media_max
            })

    return detailed_data
