import pandas as pd
import matplotlib.pyplot as plt
import os


class Analyzer(object):
    def __init__(self, media_name, game_franchise_name, media_type, release_dates, metric="Average"):
        self.media_name = media_name
        self.game_franchise_name = game_franchise_name
        self.media_type = media_type
        self.release_dates = release_dates
        self.metric = metric  # Corrigido: Atribuir o parâmetro metric a self.metric

    def create_graph(self, df, output_graph_dir, csv_filename):
        plt.figure(figsize=(12, 6))
        # Plot only non-NaN values for the metric
        plt.plot(df["Month"], df[f"{self.metric}"], label=f"{self.metric}", marker='o', linestyle='-')

        # Adicionar linha vertical para S1 (ou outras datas de lançamento)
        # Assegurar que release_dates seja um dicionário, mesmo para tipos de mídia não-Series
        # Para simplificar, vamos assumir que se media_type não for "Series", release_dates é uma string de data única
        # e a transformamos em um dicionário com uma chave genérica como "Release"

        current_release_dates = {}
        if isinstance(self.release_dates, dict):
            current_release_dates = self.release_dates
        elif isinstance(self.release_dates, str):
            # Se for uma string de data única (para filmes, etc.), crie um dicionário
            current_release_dates = {"Release": self.release_dates}
        else:
            print(f"Formato de release_dates ('{self.release_dates}') não suportado para plotagem de linhas verticais.")
            # Prosseguir sem linhas verticais se o formato for inesperado

        for season_or_event, date_str in current_release_dates.items():
            release_date = pd.to_datetime(date_str, errors='coerce')
            if pd.isna(release_date):
                print(f"Data de lançamento {season_or_event} ('{date_str}') é inválida.")
                # Não retorna, apenas pula esta linha vertical
            else:
                plt.axvline(x=release_date, color='r', linestyle='--',
                            label=f'{season_or_event} Release ({release_date.strftime("%Y-%m-%d")})')

        title_metric_name = 'Média' if self.metric == "Average" else self.metric  # Usar o nome da métrica diretamente se não for "Average"
        plt.title(
            f"{title_metric_name} de Jogadores Mensais: {os.path.splitext(csv_filename)[0]}")
        plt.xlabel("Mês")
        plt.ylabel(f"{title_metric_name} de Jogadores")
        plt.legend()
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()

        graph_filename = f"{os.path.splitext(csv_filename)[0]}_{self.metric.replace(' ', '_').lower()}_analysis.png"  # Incluir métrica no nome do arquivo
        graph_filepath = os.path.join(output_graph_dir, graph_filename)
        plt.savefig(graph_filepath)
        plt.close()
        print(f"Gráfico salvo em: {graph_filepath}")

    def analyze_media(self):
        if not self.game_franchise_name or not self.release_dates:
            print("Nome da franquia ou data de lançamento não definidos. Abortando analyze_media.")
            return

        csv_dir_path = os.path.join("C:/Users/thales/Documents/UFF/game-analytics/csv_data",
                                    self.game_franchise_name)  # Mantenha seu caminho ou parametrize
        if not os.path.isdir(csv_dir_path):
            print(f"Diretório CSV não encontrado: {csv_dir_path}")
            return

        output_graph_dir = os.path.join("graphs")
        os.makedirs(output_graph_dir, exist_ok=True)

        for csv_filename in os.listdir(csv_dir_path):
            if csv_filename.endswith(".csv"):
                csv_filepath = os.path.join(csv_dir_path, csv_filename)
                print(f"Analisando arquivo: {csv_filepath} para a métrica: {self.metric}")
                try:
                    df = pd.read_csv(csv_filepath)

                    # Verificar se as colunas necessárias existem
                    if "Month" not in df.columns:
                        print(f"Coluna 'Month' não encontrada em {csv_filename}. Pulando.")
                        continue

                    if f"{self.metric}" not in df.columns:
                        print(f"Coluna da métrica '{self.metric}' não encontrada em {csv_filename}. Pulando.")
                        continue

                    # Limpar e converter a coluna 'Month' para datetime
                    df["Month"] = df["Month"].astype(str)
                    df = df[~df["Month"].str.contains("Last 30 Days", na=False, case=False)]

                    df["Month"] = pd.to_datetime(df["Month"].apply(lambda x: x + " 1" if isinstance(x, str) else x),
                                                 format='%B %Y %d',
                                                 errors='coerce')
                    df.dropna(subset=["Month"], inplace=True)

                    if df.empty:
                        print(f"Nenhum dado de data válido encontrado em {csv_filename} após a conversão. Pulando.")
                        continue

                    # Converter a coluna da métrica para numérico.
                    # Valores como "1,234" tornam-se 1234.0.
                    # Valores como "-" ou outras strings não numéricas tornam-se NaN.
                    df[f"{self.metric}"] = pd.to_numeric(
                        df[f"{self.metric}"].astype(str).str.replace(",", "", regex=False),
                        errors='coerce'
                    )

                    # Se a métrica for "Average", remover linhas onde a conversão para numérico falhou (ou seja, tornou-se NaN).
                    # É aqui que as linhas com "-" na coluna "Average" seriam descartadas.
                    if self.metric == "Average":
                        df.dropna(subset=[f"{self.metric}"], inplace=True)
                    # Se a métrica não for "Average", as linhas com NaN (por exemplo, de "-") na coluna da métrica são mantidas.
                    # Isso resultará em lacunas no gráfico.

                    # Verificar se o DataFrame está vazio após o processamento.
                    if df.empty:
                        print(
                            f"DataFrame ficou vazio após processamento inicial ou da métrica para {csv_filename}. Pulando.")
                        continue

                    # Verificar adicionalmente: se a coluna da métrica agora é toda NaN, não há nada para plotar.
                    if df[f"{self.metric}"].isnull().all():
                        print(
                            f"Coluna '{self.metric}' em {csv_filename} contém apenas valores inválidos (NaN) após conversão. Nada para plotar. Pulando.")
                        continue

                    df.sort_values("Month", inplace=True)

                    # Lógica para decidir se o gráfico deve ser gerado com base nas datas
                    # (mantida a lógica original, adaptada para release_dates como dicionário ou string)
                    oldest_date_in_csv = df["Month"].min()
                    if pd.isna(oldest_date_in_csv):
                        print(f"Não foi possível determinar a data mais antiga em {csv_filename}. Pulando.")
                        continue

                    # Determinar a data de lançamento principal para comparação
                    main_release_date_str = None
                    if self.media_type == "Series" and isinstance(self.release_dates,
                                                                  dict) and "S1" in self.release_dates:
                        main_release_date_str = self.release_dates["S1"]
                    elif isinstance(self.release_dates, str):  # Filme ou jogo com data única
                        main_release_date_str = self.release_dates
                    elif isinstance(self.release_dates, dict):  # Pegar a primeira data se for um dict genérico
                        try:
                            main_release_date_str = next(iter(self.release_dates.values()))
                        except StopIteration:
                            pass  # Fica None

                    if main_release_date_str:
                        compare_release_date = pd.to_datetime(main_release_date_str, errors='coerce')
                        if pd.isna(compare_release_date):
                            print(
                                f"Data de lançamento principal ('{main_release_date_str}') é inválida. Não é possível comparar datas para {csv_filename}.")
                        elif oldest_date_in_csv < compare_release_date:
                            print(
                                f"Gerando gráfico para {csv_filename} pois {oldest_date_in_csv.strftime('%Y-%m-%d')} < {compare_release_date.strftime('%Y-%m-%d')}")
                            self.create_graph(df=df, output_graph_dir=output_graph_dir, csv_filename=csv_filename)
                        else:
                            print(
                                f"Dados em {csv_filename} ({oldest_date_in_csv.strftime('%Y-%m-%d')}) não são anteriores à data de lançamento principal ({compare_release_date.strftime('%Y-%m-%d')}). Nenhum gráfico gerado.")
                    else:
                        # Se não houver uma data de lançamento principal clara para comparar (ou se não for para filtrar por data), gerar o gráfico
                        print(
                            f"Gerando gráfico para {csv_filename} (sem filtro de data de lançamento principal ou data inválida).")
                        self.create_graph(df=df, output_graph_dir=output_graph_dir, csv_filename=csv_filename)

                except Exception as e:
                    print(f"Erro ao processar o arquivo {csv_filepath}: {e}")
