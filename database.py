import sqlite3
from datetime import datetime

import config
from utils import display_message

# Caminho do banco de dados
db_path = config.paths("db_path")

""" RESULTADOS """


def insert_resultado_final(codigo_partida, codigo_liga, nome_liga, time_casa, placar_casa, time_visitante,
                           placar_visitante, placar_final, resultado_partida):
    data_partida = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data_criacao = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        sql_insert_resultado = f"""
        INSERT INTO fifa_resultados_final (codigo_partida, codigo_liga, nome_liga, time_casa, placar_casa, time_visitante,
                                   placar_visitante, placar_final, resultado_partida, data_partida, data_criacao)
        VALUES ('{codigo_partida}', '{codigo_liga}', '{nome_liga}', '{time_casa}', {placar_casa}, '{time_visitante}',
                 {placar_visitante}, '{placar_final}', '{resultado_partida}', '{data_partida}', '{data_criacao}')
        """

        cursor.execute(sql_insert_resultado)

        conn.commit()
        conn.close()

    except Exception as e:

        message = f"Insert_resultado : Erro ao gravar no banco de dados: {str(e)}"
        display_message(message)


def select_resultados_final_partida(time_casa, time_visitante):
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Execute query to fetch all games' 'time_casa', 'time_visitante', 'descricao_resultado'
        all_games_query = (f""" 
                SELECT time_casa, time_visitante, resultado_partida
                FROM  fifa_resultados_final 
                WHERE time_casa = '{time_casa}' AND time_visitante = '{time_visitante}'
        """)

        cursor.execute(all_games_query)
        all_results = cursor.fetchall()
        conn.close()

        return all_results
    except sqlite3.Error as e:
        display_message(f"Database error: {e}")


def select_resultados_final_time(nome_time):
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Execute query to fetch all games' 'time_casa', 'time_visitante', 'descricao_resultado'
        all_games_query = (f""" SELECT '{nome_time}', 
            CASE WHEN resultado_partida = 'Empate' THEN 'Empatou' 
            WHEN (resultado_partida = time_casa AND time_casa = '{nome_time}') 
            OR (resultado_partida = time_visitante AND time_visitante =  '{nome_time}') THEN 'Venceu'  ELSE 'Perdeu'
            END AS resultado_partida 
        FROM fifa_resultados_final
        WHERE  time_casa = '{nome_time}' OR time_visitante = '{nome_time}'       
        """)

        cursor.execute(all_games_query)
        all_results = cursor.fetchall()

        conn.close()

        return all_results

    except sqlite3.Error as e:
        display_message(f"Database error: {e}")


""" ESTATISTICAS """


def insert_estatistica_partida(codigo_partida, time_casa, time_visitante, resultado, qtd_total, perc_total,
                               qtd_parcial, perc_parcial, dif_perc_total_parcial, seq_atual, seq_media, seq_maxima,
                               dif_seq_media_atual, dif_seq_media_max, atr_atual, atr_media, atr_maximo,
                               dif_atr_media_atual, dif_atr_media_max, data_criacao):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        query_percent_min = f""" 
        SELECT MIN(dif_perc_total_parcial) AS dif_perc_min
        FROM fifa_estatisticas_partida
        WHERE time_casa = '{time_casa}' AND time_visitante = '{time_visitante}' AND resultado = '{resultado}'
        GROUP BY time_casa, time_visitante, resultado
        """
        cursor.execute(query_percent_min)
        result = cursor.fetchall()

        if result:
            dif_perc_total_parcial_min = result[0][0]  # Pega o primeiro valor da primeira linha
        else:
            dif_perc_total_parcial_min = None  # Define um valor padrão caso não haja resultado

        # Verificar e converter valores para float
        dif_perc_total_parcial = float(dif_perc_total_parcial) if isinstance(dif_perc_total_parcial,
                                                                             str) else dif_perc_total_parcial
        dif_perc_total_parcial_min = float(dif_perc_total_parcial_min) if isinstance(dif_perc_total_parcial_min,
                                                                                     str) else dif_perc_total_parcial_min

        # Calcular diferença
        try:
            dif_perc_total_parcial_min_atual = dif_perc_total_parcial - dif_perc_total_parcial_min
        except (TypeError, ValueError) as e:
            print(f"Erro ao calcular a diferença: {e}")
            dif_perc_total_parcial_min_atual = None  # Valor padrão ou tratamento adicional

        sql_insert_estatistica_partida = f"""
        INSERT INTO fifa_estatisticas_partida (codigo_partida, time_casa, time_visitante, resultado, qtd_total, perc_total, qtd_parcial,
                            perc_parcial, dif_perc_total_parcial, dif_perc_total_parcial_min, dif_perc_total_parcial_min_atual,
                            seq_atual, seq_media, seq_maxima, dif_seq_media_atual, dif_seq_media_max, atr_atual, atr_media, 
                            atr_maximo, dif_atr_media_atual, dif_atr_media_max, data_criacao) VALUES
             ('{codigo_partida}', '{time_casa}', '{time_visitante}', '{resultado}', {qtd_total}, {perc_total}, {qtd_parcial},
              {perc_parcial}, {dif_perc_total_parcial}, {dif_perc_total_parcial_min}, {dif_perc_total_parcial_min_atual},
              {seq_atual}, {seq_media}, {seq_maxima}, {dif_seq_media_atual}, {dif_seq_media_max}, {atr_atual}, {atr_media},
              {atr_maximo}, {dif_atr_media_atual}, {dif_atr_media_max}, '{data_criacao}')"""

        cursor.execute(sql_insert_estatistica_partida)

        conn.commit()

    except Exception as e:
        message = f"Insert_estatistica_partida : Erro ao gravar no banco de dados: {str(e)}"
        display_message(message)


def select_estatisticas_por_partida(time_casa, time_visitante):
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # SQL query to fetch data
        query = f"""
        SELECT 
            time_casa AS 'Time Casa', 
            time_visitante AS 'Time Visitante', 
            resultado AS 'Resultado',
            dif_perc_total_parcial AS 'Percentual', 
            dif_perc_total_parcial_min_atual AS 'Diferenca Percentual/Minima', 
            seq_atual AS 'Sequencia Atual', 
            dif_seq_media_atual  AS 'Diferenca Sequencia/Media', 
            dif_seq_media_max AS 'Diferenca Sequencia/Maxima', 
            atr_atual AS 'Atraso Atual',
            dif_atr_media_atual AS 'Diferenca Atraso/Media', 
            dif_atr_media_max AS 'Diferenca Atraso/Maxima'
        FROM fifa_estatisticas_partida
        WHERE time_casa = ? AND time_visitante = ?
        ORDER BY id DESC
        LIMIT 3
        """

        # Execute the query with parameters
        cursor.execute(query, (time_casa, time_visitante))
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()

        # Convert results to a list of dictionaries
        all_results = [dict(zip(columns, row)) for row in rows]

        conn.close()
        return all_results

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []


# noinspection GrazieInspection
def insert_estatistica_time(codigo_partida, nome_time, resultado, qtd_total, perc_total, qtd_parcial,
                            perc_parcial, dif_perc_total_parcial, seq_atual, seq_media, seq_maxima,
                            dif_seq_media_atual, dif_seq_media_max, atr_atual, atr_media, atr_maximo,
                            dif_atr_media_atual, dif_atr_media_max, data_criacao):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        query_percent_min = f""" 
        SELECT MIN(dif_perc_total_parcial) AS dif_perc_total_parcial_min
        FROM fifa_estatisticas_time
        WHERE (time = '{nome_time}') AND resultado = '{resultado}'
        GROUP BY time, resultado
        """
        cursor.execute(query_percent_min)
        result = cursor.fetchall()

        print("-- sql : " + query_percent_min)

        if result:
            dif_perc_total_parcial_min = result[0][0]  # Pega o primeiro valor da primeira linha
        else:
            dif_perc_total_parcial_min = None  # Define um valor padrão caso não haja resultado

        # Verificar e converter valores para float
        dif_perc_total_parcial = float(dif_perc_total_parcial) if isinstance(dif_perc_total_parcial,
                                                                             str) else dif_perc_total_parcial
        dif_perc_total_parcial_min = float(dif_perc_total_parcial_min) if isinstance(dif_perc_total_parcial_min,
                                                                                     str) else dif_perc_total_parcial_min
        # Calcular diferença
        try:
            dif_perc_total_parcial_min_atual = dif_perc_total_parcial - dif_perc_total_parcial_min
        except (TypeError, ValueError) as e:
            print(f"Erro ao calcular a diferença: {e}")
            dif_perc_total_parcial_min_atual = None  # Valor padrão ou tratamento adicional

        sql_insert_estatistica_time = f"""INSERT INTO fifa_estatisticas_time (codigo_partida, time, resultado, qtd_total, perc_total, qtd_parcial,
              perc_parcial, dif_perc_total_parcial, dif_perc_total_parcial_min, dif_perc_total_parcial_min_atual,
              seq_atual, seq_media, seq_maxima, dif_seq_media_atual, dif_seq_media_max, atr_atual, atr_media, atr_maximo, 
              dif_atr_media_atual, dif_atr_media_max, data_criacao) VALUES
              ('{codigo_partida}', '{nome_time}', '{resultado}', {qtd_total}, {perc_total}, {qtd_parcial},
                {perc_parcial}, {dif_perc_total_parcial}, {dif_perc_total_parcial_min}, {dif_perc_total_parcial_min_atual}, 
                {seq_atual}, {seq_media}, {seq_maxima}, {dif_seq_media_atual}, {dif_seq_media_max}, {atr_atual}, {atr_media}, 
                {atr_maximo}, {dif_atr_media_atual}, {dif_atr_media_max}, '{data_criacao}') """

        print(sql_insert_estatistica_time)

        cursor.execute(sql_insert_estatistica_time)
        conn.commit()
        conn.close()

        # display_message(f"Dados da partida inseridos com sucesso")
    except Exception as e:
        message = f"Insert_estatistica_time: Erro ao gravar no banco de dados: {str(e)}"
        display_message(message)


def select_estatisticas_por_time():
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Execute query to fetch all games' 'time_casa', 'time_visitante', 'descricao_resultado'
        all_games_query = (f""" SELECT 
			time AS 'Time', 
			resultado AS 'Resultado',
			dif_perc_total_parcial AS 'Percentual', 
			dif_perc_total_parcial_min_atual AS 'Diferenca da Minima', 
			seq_atual AS 'Sequencia Atual', 
			dif_seq_media_atual AS 'Diferenca Sequencia Da Media', 
			dif_seq_media_max AS 'Diferenca Sequencia Da Maxima', 
			atr_atual AS 'Atraso Atual',
			dif_atr_media_atual AS 'Diferenca Atraso Da Media', 
			dif_atr_media_max AS 'Diferenca Atraso Da Maxima'
		FROM (
			SELECT 
				time, 
				resultado, 
				dif_perc_total_parcial, 
				dif_perc_total_parcial_min_atual, 
				seq_atual, 
				dif_seq_media_atual, 
				dif_seq_media_max, 
				atr_atual, 
				dif_atr_media_atual, 
				dif_atr_media_max,
				ROW_NUMBER() OVER (PARTITION BY time, resultado ORDER BY id DESC) AS row_num
			FROM fifa_estatisticas_time
		)
		WHERE row_num = 1
		ORDER BY time, resultado;       
        """)

        cursor.execute(all_games_query)
        all_results = cursor.fetchall()

        conn.close()

        return all_results

    except sqlite3.Error as e:
        display_message(f"Database error: {e}")


""" APOSTAS """


def insert_aposta(tipo_aposta, time_casa, time_visitante, codigo_partida, aposta_partida, multiplicador):
    # print("entrou insert_aposta")

    data_criacao = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Verifica se ja existe aposta em aberto para a partida
    aposta_aberta = select_aposta_aberta(time_casa, time_visitante, aposta_partida)

    # Se nao existe cria novo codigo e reinicia a sequencia
    if aposta_aberta == 0:
        codigo_aposta = select_max_codigo_aposta() + 1
        aposta_sequencia = 1
    else:
        codigo_aposta = aposta_aberta
        aposta_sequencia = select_aposta_sequencia(time_casa, time_visitante, aposta_partida, codigo_aposta) + 1

    # Seleciona a ODD
    valor_odd = select_odd_resultado_partida(time_casa, time_visitante, aposta_partida)

    # Seleciona valor da aposta
    valor_aposta = select_aposta_valor(time_casa, time_visitante, aposta_partida, aposta_sequencia) * multiplicador

    # Calcula valor do premio
    valor_premio = int(valor_aposta) * valor_odd

    # Calcula valor total gasto
    valor_gasto_total = int(valor_aposta) + select_sum_valor_aposta(codigo_aposta)

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(f"""
                INSERT INTO fifa_aposta   
                    (codigo_aposta, tipo_aposta, time_casa, time_visitante, sequencia, codigo_partida, aposta_partida, valor_odd,
                    valor_aposta, valor_premio, valor_gasto_total, data_criacao)            
                 VALUES ({codigo_aposta},' {tipo_aposta}', '{time_casa}', '{time_visitante}', {aposta_sequencia}, '{codigo_partida}', 
                    '{aposta_partida}', {valor_odd}, {valor_aposta}, {valor_premio}, {valor_gasto_total}, '{data_criacao}')
                """)

        conn.commit()
        conn.close()

        display_message("Aposta inserida com sucesso no banco")

    except Exception as e:
        message = f"Erro ao inserir aposta no banco de dados: {str(e)}"
        display_message(message)
        return message


def update_verificacao_resultado_aposta(codigo_partida, resultado):
    mensagem = None

    # Chama a função para obter os dados da aposta
    aposta_dados = select_aposta_partida(codigo_partida)

    # Verifica se os dados foram retornados corretamente
    if aposta_dados and len(aposta_dados) > 0:
        # Descompacta os campos da linha retornada
        codigo_aposta, sequencia, codigo_partida, aposta_partida, valor_premio, valor_gasto_total, resultado_partida = \
            aposta_dados[0]

        if aposta_partida == resultado:
            flg_acertou = 'S'
            saldo = valor_premio - valor_gasto_total
            mensagem = f"<<< Ganhou. Cod: {str(codigo_aposta).zfill(5)} Seq: {str(sequencia).zfill(2)} >>>" \
                       f"\n<+++ Valor: {int(saldo)} +++>"
        else:
            flg_acertou = 'N'
            saldo = int(valor_gasto_total) * -1
            mensagem = f"<<< Perdeu. Cod: {str(codigo_aposta).zfill(5)} Seq:  {str(sequencia).zfill(2)} >>>" \
                       f"\n<--- Saldo: {int(saldo)} --->"

        try:
            # Connect to the database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            sql = f"""
                UPDATE fifa_aposta
                SET resultado_partida = '{resultado}', 
                    flg_acertou = '{flg_acertou}',
                    valor_saldo = {saldo},
                WHERE codigo_partida = '{codigo_partida}'
            """

            # print(sql)

            # Atualiza a tabela com base no resultado
            cursor.execute(sql)

            conn.commit()
            conn.close()

        except sqlite3.Error as e:
            display_message(f"Erro ao realizar update na tabela de apostas: {e}")

    print("finalizada a verificacao de aposta")

    return mensagem


def select_codigo_aposta(codigo_partida):
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Execute query to fetch the latest 'codigo_aposta' for the given 'codigo_partida'
        cursor.execute(f"""
                SELECT codigo_aposta
                FROM fifa_aposta
                WHERE codigo_partida = ?
                ORDER BY ID DESC
                LIMIT 1
        """, (codigo_partida,))  # Use parameterized query for safety

        # Fetch the first result
        row = cursor.fetchone()

        conn.close()

        # Return the result if it exists, otherwise None
        return row[0] if row else None

    except sqlite3.Error as e:
        display_message(f"Database error: {e}")
        return None


def select_aposta_aberta(time_casa, time_visitante, aposta_partida):
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Execute query to fetch the latest 'codigo_aposta' for the given 'codigo_partida'
        cursor.execute(f"""
        SELECT codigo_aposta
        FROM fifa_aposta
        WHERE ID = 
            (SELECT MAX(ID)
            FROM fifa_aposta
            WHERE time_casa = ?
            AND time_visitante = ?
            AND aposta_partida = ?)
        """, (time_casa, time_visitante, aposta_partida))

        # Fetch the first result
        row = cursor.fetchone()

        # Return the result if it exists and is not None, otherwise 0
        return row[0] if row is not None and row[0] is not None else 0

    except sqlite3.Error as e:
        display_message(f"Database error: {e}")
        return 0


def select_aposta_sequencia(time_casa, time_visitante, aposta_partida, codigo_aposta):
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Execute query to sum 'valor_aposta' for the given 'codigo_aposta'
        cursor.execute(f"""
            SELECT MAX(sequencia)
            FROM fifa_aposta
            WHERE time_casa = '{time_casa}'
            AND time_visitante = '{time_visitante}'
            AND aposta_partida = '{aposta_partida}'
            AND codigo_aposta = '{codigo_aposta}'
            """)

        # Fetch the result
        row = cursor.fetchone()

        conn.close()

        # Return the sum if it exists, otherwise return 0
        return row[0] if row[0] is not None else 0

    except sqlite3.Error as e:
        display_message(f"Database error: {e}")
        return 0


def select_odd_resultado_partida(time_casa, time_visitante, resultado):
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Execute query to sum 'valor_aposta' for the given 'codigo_aposta'
        cursor.execute(f"""
            SELECT valor_odd
            FROM fifa_odd_resultado_partida
            WHERE time_casa = '{time_casa}'
            AND   time_visitante = '{time_visitante}'
            AND   resultado_partida = '{resultado}'
            """)

        # Fetch the result
        row = cursor.fetchone()

        conn.close()

        # Return the sum if it exists, otherwise return 0
        return row[0] if row[0] is not None else 3

    except sqlite3.Error as e:
        display_message(f"Database error: {e}")
        return 0


def select_max_codigo_aposta():
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Execute query to fetch the maximum 'codigo_aposta' or 1 if no records exist
        cursor.execute(f"""
            SELECT COALESCE(MAX(codigo_aposta), 0) AS max_codigo_aposta
            FROM fifa_aposta;
        """)

        # Fetch the result
        row = cursor.fetchone()

        conn.close()

        # Return the maximum code if it exists, otherwise 1
        return row[0] if row[0] is not None else 0

    except sqlite3.Error as e:
        display_message(f"Database error: {e}")
        return 0


def select_sum_valor_aposta(codigo_aposta):
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Execute query to sum 'valor_aposta' for the given 'codigo_aposta'
        cursor.execute(f"""
            SELECT SUM(valor_aposta) AS total_valor_aposta
            FROM fifa_aposta
            WHERE codigo_aposta = ?
        """, (codigo_aposta,))  # Use parameterized query for safety

        # Fetch the result
        row = cursor.fetchone()

        conn.close()

        # Return the sum if it exists, otherwise return 0
        return row[0] if row[0] is not None else 0

    except sqlite3.Error as e:
        display_message(f"Database error: {e}")
        return 0


def select_aposta_valor(time_casa, time_visitante, resultado, sequencia):
    # print("select_aposta_valor")

    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        sql = f"""
            SELECT valor_aposta
            FROM fifa_aposta_valor
            WHERE time_casa = '{time_casa}'
            AND   time_visitante = '{time_visitante}'
            AND   resultado_partida = '{resultado}'
            AND   sequencia = {sequencia}
            """

        # print(sql)

        # Execute query to sum 'valor_aposta' for the given 'codigo_aposta'
        cursor.execute(sql)

        # Fetch the result
        row = cursor.fetchone()

        conn.close()

        valor_aposta = row[0] if row[0] is not None else 3

        # Return the sum if it exists, otherwise return 0
        return str(valor_aposta)

    except sqlite3.Error as e:
        display_message(f"Database error: {e}")
        return 0


def select_aposta_partida(codigo_partida):
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Execute query to fetch the latest 'codigo_aposta' for the given 'codigo_partida'
        cursor.execute(f"""
            SELECT codigo_aposta, sequencia, codigo_partida, aposta_partida, valor_premio, valor_gasto_total, resultado_partida
            FROM fifa_aposta
            WHERE codigo_partida = '{codigo_partida}'
        """)

        # Fetch the first result
        row = cursor.fetchall()

        conn.close()

        # Return the result if it exists, otherwise 0
        return row if row is not None else 0

    except sqlite3.Error as e:
        display_message(f"Database error: {e}")
        return 0


def select_condicao_atraso_percentual(time_casa, time_visitante, resultado):
    # ahahprint("entrou select_condicao_atraso_percentual")

    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        sql = f"""

        SELECT CASE 
           WHEN EXISTS (
               SELECT 1
               FROM (
                   SELECT dif_atr_media_atual, atr_media / 2 AS indice  
                   FROM fifa_estatisticas_partida
                   WHERE time_casa = '{time_casa}' 
                     AND time_visitante = '{time_visitante}' 
                     AND resultado = '{resultado}'
                   ORDER BY ID DESC 
                   LIMIT 1
               ) AS subquery
               WHERE dif_atr_media_atual < indice
           ) THEN 'True'
           ELSE 'False'
       END AS resultado;
        """

        # Print(sql)

        # Execute query to sum 'valor_aposta' for the given 'codigo_aposta'
        cursor.execute(sql)

        # Fetch the result
        row = cursor.fetchone()

        conn.close()

        # Return the result if it exists and is not None
        if row and row[0] is not None:
            # print(row[0])
            return row[0]
        else:
            return 3

    except sqlite3.Error as e:
        display_message(f"Database error: {e}")
        return 0
