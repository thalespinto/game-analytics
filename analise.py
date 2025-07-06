import glob
import matplotlib.pyplot as plt
import os
import pandas as pd
from scipy.stats import ttest_ind, shapiro, mannwhitneyu
from pandas.api.types import is_string_dtype
import seaborn as sns

class Analyzer(object):
    def __init__(self, media_name, game_franchise_name, media_type, release_dates, combine=False, metric="Average"):
        self.media_name = media_name
        self.game_franchise_name = game_franchise_name
        self.media_type = media_type
        self.release_dates = release_dates
        self.combine = combine
        self.metric = metric

    def create_graph(self, df, output_graph_dir, csv_filename, combined_plot_title=None):
        """
        Cria e salva um gráfico.
        Se combined_plot_title for fornecido e 'Source' estiver nas colunas do df,
        trata como um gráfico combinado com múltiplas fontes.
        """
        plt.figure(figsize=(15, 7)) # Aumentado um pouco para melhor visualização de múltiplos plots
        title_metric_name = 'Média' if self.metric == "Average" else self.metric

        if 'Source' in df.columns and combined_plot_title:  # Gráfico combinado
            # Agrupa por 'Source' e plota cada um
            for source_name, group in df.groupby('Source'):
                # Ordena cada grupo por data para garantir que as linhas sejam desenhadas corretamente
                group_sorted = group.sort_values("Month")
                plt.plot(group_sorted["Month"], group_sorted[self.metric], label=f"{source_name} - {self.metric}", marker='o', linestyle='-')
            plt.title(combined_plot_title)
            # Nome do arquivo para o gráfico combinado
            graph_filename_base = f"combined_{self.game_franchise_name}_{self.metric.replace(' ', '_').lower()}"
        else:  # Gráfico individual
            plt.plot(df["Month"], df[self.metric], label=f"{self.metric}", marker='o', linestyle='-')
            plt.title(f"{title_metric_name} de Jogadores Mensais: {os.path.splitext(csv_filename)[0]}")
            graph_filename_base = os.path.splitext(csv_filename)[0]

        # Lógica para desenhar linhas verticais de datas de lançamento
        current_release_dates = {}
        if isinstance(self.release_dates, dict):
            current_release_dates = self.release_dates
        elif isinstance(self.release_dates, str):
            current_release_dates = {"Release": self.release_dates}
        # Não mostrar print se não houver datas, especialmente no modo combinado

        for event_name, date_str in current_release_dates.items():
            try:
                release_date = pd.to_datetime(date_str, errors='raise') # 'raise' para capturar datas inválidas
                plt.axvline(x=release_date, color='r', linestyle='--',
                            label=f'{event_name} Release ({release_date.strftime("%Y-%m-%d")})')
            except ValueError:
                print(f"Data de lançamento '{event_name}' ('{date_str}') é inválida e não será plotada.")
            except Exception as e:
                print(f"Erro ao processar data de lançamento '{event_name}' ('{date_str}'): {e}")


        plt.xlabel("Mês")
        plt.ylabel(f"{title_metric_name} de Jogadores")
        plt.legend(loc='upper left', bbox_to_anchor=(1,1)) # Ajusta a posição da legenda
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout(rect=[0, 0, 0.85, 1]) # Ajusta o layout para caber a legenda fora

        graph_filename = f"{graph_filename_base}_{self.metric.replace(' ', '_').lower()}_analysis.png"
        graph_filepath = os.path.join(output_graph_dir, graph_filename)
        plt.savefig(graph_filepath)
        plt.close()
        print(f"Gráfico salvo em: {graph_filepath}")

    def analyze_media(self):
        if not self.game_franchise_name:
            print("Nome da franquia não definido. Abortando analyze_media.")
            return

        # Caminho para os arquivos CSV (ajuste conforme necessário)
        csv_dir_path = os.path.join("/csv_data", self.game_franchise_name)
        if not os.path.isdir(csv_dir_path):
            print(f"Diretório CSV não encontrado: {csv_dir_path}")
            return

        output_graph_dir = os.path.join("graphs")
        os.makedirs(output_graph_dir, exist_ok=True)

        all_dfs_for_combine = [] # Lista para armazenar DataFrames se self.combine for True

        for csv_filename in os.listdir(csv_dir_path):
            if csv_filename.endswith(".csv"):
                csv_filepath = os.path.join(csv_dir_path, csv_filename)
                print(f"Analisando arquivo: {csv_filepath} para a métrica: {self.metric}")
                try:
                    df = pd.read_csv(csv_filepath)

                    if "Month" not in df.columns:
                        print(f"Coluna 'Month' não encontrada em {csv_filename}. Pulando.")
                        continue
                    if self.metric not in df.columns: # Corrigido para usar self.metric diretamente
                        print(f"Coluna da métrica '{self.metric}' não encontrada em {csv_filename}. Pulando.")
                        continue

                    # Limpeza e conversão da coluna 'Month'
                    df["Month"] = df["Month"].astype(str)
                    df = df[~df["Month"].str.contains("Last 30 Days", na=False, case=False)]
                    df["Month"] = pd.to_datetime(df["Month"].apply(lambda x: x + " 1" if isinstance(x, str) else x),
                                                 format='%B %Y %d', errors='coerce')
                    df.dropna(subset=["Month"], inplace=True)

                    if df.empty:
                        print(f"Nenhum dado de data válido encontrado em {csv_filename} após a conversão. Pulando.")
                        continue

                    # Limpeza e conversão da coluna da métrica
                    df[self.metric] = pd.to_numeric(
                        df[self.metric].astype(str).str.replace(",", "", regex=False),
                        errors='coerce'
                    )
                    # Remove linhas onde a métrica é NaN APÓS a conversão.
                    # Isso é importante para não tentar plotar NaNs ou ter problemas na combinação.
                    df.dropna(subset=[self.metric], inplace=True)


                    if df.empty or df[self.metric].isnull().all():
                        print(f"DataFrame vazio ou sem dados válidos para a métrica '{self.metric}' em {csv_filename} após limpeza. Pulando.")
                        continue

                    df.sort_values("Month", inplace=True)

                    if self.combine:
                        df['Source'] = os.path.splitext(csv_filename)[0]  # Adiciona nome do arquivo como fonte
                        # Seleciona apenas as colunas necessárias e faz uma cópia
                        all_dfs_for_combine.append(df[["Month", self.metric, "Source"]].copy())
                    else:
                        # Lógica original para gráficos individuais e filtro por data de lançamento
                        oldest_date_in_csv = df["Month"].min()
                        if pd.isna(oldest_date_in_csv):
                            print(f"Não foi possível determinar a data mais antiga em {csv_filename}. Pulando.")
                            continue

                        main_release_date_str = None
                        if self.media_type == "Series" and isinstance(self.release_dates, dict) and "S1" in self.release_dates:
                            main_release_date_str = self.release_dates["S1"]
                        elif isinstance(self.release_dates, str):
                            main_release_date_str = self.release_dates
                        elif isinstance(self.release_dates, dict) and self.release_dates:
                            try:
                                main_release_date_str = next(iter(self.release_dates.values()))
                            except StopIteration:
                                pass # main_release_date_str continua None

                        if main_release_date_str:
                            try:
                                compare_release_date = pd.to_datetime(main_release_date_str, errors='raise')
                                if oldest_date_in_csv < compare_release_date:
                                    print(f"Gerando gráfico para {csv_filename} pois {oldest_date_in_csv.strftime('%Y-%m-%d')} < {compare_release_date.strftime('%Y-%m-%d')}")
                                    self.create_graph(df=df, output_graph_dir=output_graph_dir, csv_filename=csv_filename)
                                else:
                                    print(f"Dados em {csv_filename} ({oldest_date_in_csv.strftime('%Y-%m-%d')}) não são anteriores à data de lançamento principal ({compare_release_date.strftime('%Y-%m-%d')}). Nenhum gráfico gerado.")
                            except ValueError:
                                print(f"Data de lançamento principal ('{main_release_date_str}') é inválida. Gerando gráfico para {csv_filename} sem filtro de data.")
                                self.create_graph(df=df, output_graph_dir=output_graph_dir, csv_filename=csv_filename)
                        else:
                            print(f"Gerando gráfico para {csv_filename} (sem data de lançamento principal para filtro).")
                            self.create_graph(df=df, output_graph_dir=output_graph_dir, csv_filename=csv_filename)

                except Exception as e:
                    print(f"Erro ao processar o arquivo {csv_filepath}: {e}")
                    import traceback
                    traceback.print_exc() # Para depuração mais detalhada

        # Após o loop, se self.combine for True e houver dados, criar o gráfico combinado
        if self.combine and all_dfs_for_combine:
            if not all_dfs_for_combine: # Verificação redundante, mas segura
                print("Modo de combinação ativado, mas nenhum dado foi coletado dos arquivos CSV.")
                return

            combined_df = pd.concat(all_dfs_for_combine, ignore_index=True)

            if not combined_df.empty:
                # Ordenar por data geral para o eixo X e depois por fonte para consistência na legenda
                combined_df.sort_values(by=["Month", "Source"], inplace=True)
                title_metric_name = 'Média' if self.metric == "Average" else self.metric
                combined_title = f"{title_metric_name} de Jogadores Mensais Combinada: {self.game_franchise_name}"
                print(f"Gerando gráfico combinado para {self.game_franchise_name}...")
                # Passar um nome de arquivo "placeholder" para csv_filename, pois o nome do gráfico combinado é gerado internamente
                self.create_graph(df=combined_df, output_graph_dir=output_graph_dir, csv_filename="combined_data", combined_plot_title=combined_title)
            else:
                print("Nenhum dado para combinar após processar todos os arquivos.")
        elif self.combine and not all_dfs_for_combine: # Caso self.combine seja True mas nenhum dado foi coletado
             print("Modo de combinação ativado, mas nenhum dado foi coletado dos arquivos CSV.")


def generate_boxplot(antes, depois, nome_arquivo_saida):
    plt.figure(figsize=(12, 8))
    sns.set_theme(style="whitegrid")
    antes["periodo"] = "antes"
    depois["periodo"] = "depois"
    df_plot = pd.concat([antes, depois])

    if not df_plot.empty:
        sns.boxplot(data=df_plot, x='periodo', y='Peak', palette="pastel", width=0.5)

        plt.title('Comparação Mensal do Pico de Jogadores', fontsize=16)
        plt.ylabel('Pico por mês', fontsize=12)
        plt.xlabel('Períodos', fontsize=12)
        plt.tight_layout()

        try:
            plt.savefig(f"{nome_arquivo_saida}_boxplot.png")
            print(f"\nGráfico salvo com sucesso como '{nome_arquivo_saida}_boxplot.png'")
        except Exception as e:
            print(f"\nOcorreu um erro ao salvar o gráfico: {e}")
    else:
        print("\nNenhum dado para plotar.")

def analisar_impacto_lancamento(caminho_csv, mes_lancamento, nome_audiovisual):
    """
    Analisa o impacto de um lançamento, diagnosticando os dados para escolher
    automaticamente o teste estatístico mais apropriado (Teste t ou Mann-Whitney U).

    Args:
        caminho_csv (str): O caminho para o arquivo CSV com os dados de jogadores.
        mes_lancamento (str): A data de lançamento no formato 'AAAA-MM'.
        nome_audiovisual (str): O nome do audiovisual para exibição nos resultados.
    """

    log_file = os.path.splitext(caminho_csv)[0] + nome_audiovisual + ".txt"
    with open(log_file, 'w', encoding='utf-8') as f:
        print(f"--- Análise de Impacto: {nome_audiovisual} ---", file=f)

        # ... (O código de carregamento e limpeza dos dados permanece o mesmo)
        try:
            df = pd.read_csv(caminho_csv)
            if 'Peak' in df.columns and is_string_dtype(df['Peak']):
                df['Peak'] = df['Peak'].str.replace(',', '', regex=False)
            df['Peak'] = pd.to_numeric(df['Peak'], errors='coerce')
            df['Month'] = pd.to_datetime(df['Month'], errors='coerce')
            df = df.dropna(subset=['Month', 'Peak'])
            df['Month'] = df['Month'].dt.to_period('M')
            df = df.set_index('Month')
        except (FileNotFoundError, KeyError) as e:
            print(f"Erro ao carregar ou processar o CSV: {e}", file=f)
            return

        data_lancamento = pd.Period(mes_lancamento, 'M')
        if data_lancamento not in df.index:
            print(f"Erro: A data de lançamento '{mes_lancamento}' não foi encontrada nos dados.", file=f)
            return


        print("\n[ Análise de Impacto Imediato ]", file=f)
        mes_anterior = data_lancamento - 1
        if mes_anterior in df.index:
            pico_mes_lancamento = df.loc[data_lancamento]['Peak']
            pico_mes_anterior = df.loc[mes_anterior]['Peak']
            variacao_imediata = ((pico_mes_lancamento - pico_mes_anterior) / pico_mes_anterior) * 100
            print(f"Pico de jogadores no mês anterior ('{mes_anterior}'): {pico_mes_anterior:,.0f}", file=f)
            print(f"Pico de jogadores no mês do lançamento ('{data_lancamento}'): {pico_mes_lancamento:,.0f}", file=f)
            print(f"Variação imediata: {variacao_imediata:+.2f}%", file=f)
        else:
            print(f"Não foi possível calcular o impacto imediato: mês anterior ('{mes_anterior}') não encontrado.", file=f)

        print("\n[ Análise de Impacto a Longo Prazo (6 meses) ]", file=f)
        periodo_antes = df.loc[data_lancamento - 1:data_lancamento - 6].copy()
        periodo_depois = df.loc[data_lancamento + 6:data_lancamento + 1].copy()

        if len(periodo_antes) == 6 and len(periodo_depois) == 6:
            print("---6 meses antes----", file=f)
            print(periodo_antes.describe().to_string(), file=f)
            print("---6 meses depois----", file=f)
            print(periodo_depois.describe().to_string(), file=f)
            generate_boxplot(periodo_antes, periodo_depois, os.path.splitext(caminho_csv)[0] + nome_audiovisual + ".png")
            alpha = 0.05
            # Este teste é mais seguro para dados não normais ou amostras pequenas.
            stat, p_value = mannwhitneyu(periodo_depois['Peak'], periodo_antes['Peak'], alternative='greater')

            print(f"p-valor do teste: {p_value:.4f}", file=f)
            if p_value < alpha:
                print(f"Conclusão: Como o p-valor ({p_value:.4f}) é menor que {alpha}, o resultado é ESTATISTICAMENTE SIGNIFICATIVO.", file=f)
            else:
                print(f"Conclusão: Como o p-valor ({p_value:.4f}) é maior que {alpha}, não há evidência estatística de um aumento significativo.", file=f)

        else:
            print("Não foi possível realizar a análise de longo prazo: dados insuficientes para os períodos de 6 meses.", file=f)

        print("-" * 50, file=f)


def main():
    csv_folder = "csv_data"
    csv_game_folder = "tomb_raider"
    csv_files_to_process = glob.glob(os.path.join(csv_folder, csv_game_folder, "*.csv"))

    for csv_path in csv_files_to_process:
        analisar_impacto_lancamento(csv_path, '2018-03', "_1_temp")



if __name__ == '__main__':
    main()
