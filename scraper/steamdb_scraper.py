import os
from dotenv import load_dotenv
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
import time
import csv
import re
import random

load_dotenv()


class MonthlyPlayersSteamDBScraper:
    steamdb_user = os.getenv('STEAMDB_USER')
    steamdb_pwd = os.getenv('STEAMDB_PWD')

    # Constantes de delay para humanização (em segundos)
    TYPING_CHAR_DELAY_MIN = 0.06
    TYPING_CHAR_DELAY_MAX = 0.18
    PAUSE_AFTER_TYPING_MIN = 0.4
    PAUSE_AFTER_TYPING_MAX = 0.9
    ACTION_SHORT_PAUSE_MIN = 0.7
    ACTION_SHORT_PAUSE_MAX = 1.6
    ACTION_MEDIUM_PAUSE_MIN = 1.5
    ACTION_MEDIUM_PAUSE_MAX = 3.0
    PAGE_LOAD_PAUSE_MIN = 2.0
    PAGE_LOAD_PAUSE_MAX = 4.0
    POST_SCROLL_PAUSE = 0.5

    def __init__(self):
        options = uc.ChromeOptions()
        self.driver = uc.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 20)  # Um wait de 20 segundos é um bom padrão

    def _simulate_typing(self, element, text):
        """Simula a digitação de texto em um elemento, caractere por caractere."""
        for character in text:
            element.send_keys(character)
            time.sleep(random.uniform(self.TYPING_CHAR_DELAY_MIN, self.TYPING_CHAR_DELAY_MAX))
        time.sleep(random.uniform(self.PAUSE_AFTER_TYPING_MIN, self.PAUSE_AFTER_TYPING_MAX))

    def access_steamdb(self):
        print("Accessing steamdb.info...")
        self.driver.get("https://steamdb.info/")
        time.sleep(random.uniform(self.ACTION_MEDIUM_PAUSE_MIN, self.ACTION_MEDIUM_PAUSE_MAX))
        input("Resolva o captch e pressione Enter para continuar...")
        time.sleep(random.uniform(self.ACTION_SHORT_PAUSE_MIN, self.ACTION_SHORT_PAUSE_MAX))
        return

    def check_logged(self):
        # Check if already logged in by looking for the cookie
        if self.driver.get_cookie("__Host-steamdb"):
            print("Você já está logado.")
            return True
        return False

    def handle_header_login(self):
        # Click on the login link
        login_link = self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "header-login")))
        login_link.click()
        print("Clicked header login link.")
        time.sleep(random.uniform(self.ACTION_SHORT_PAUSE_MIN, self.ACTION_SHORT_PAUSE_MAX))

    def click_sign_in_via_steam(self):
        try:
            sign_in_button = self.wait.until(EC.element_to_be_clickable((By.ID, "js-sign-in")))
            sign_in_button.click()
            print("Clicked 'Sign in via Steam' button (js-sign-in).")
            time.sleep(random.uniform(self.ACTION_MEDIUM_PAUSE_MIN, self.ACTION_MEDIUM_PAUSE_MAX))
        except TimeoutException:
            print(
                "Could not find or click 'js-sign-in' button. Page structure might have changed or CAPTCHA interference.")
            raise TimeoutException("Could not find or click 'js-sign-in'")

    def fill_steam_credentials(self):
        try:
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="text"]')))
            print("Steam login page loaded.")
            time.sleep(random.uniform(self.ACTION_SHORT_PAUSE_MIN, self.ACTION_SHORT_PAUSE_MAX))
        except TimeoutException:
            print("Steam login page did not load as expected.")
            raise TimeoutException("Steam login page did not load as expected.")

        try:
            print("Attempting to fill Steam credentials...")
            time.sleep(random.uniform(self.ACTION_SHORT_PAUSE_MIN, self.ACTION_SHORT_PAUSE_MAX))
            username_input_steam = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input._2GBWeup5cttgbTw8FM3tfx")))
            self._simulate_typing(username_input_steam, self.steamdb_user)
            print(f"Filled username: {self.steamdb_user}")

            password_input_steam = self.driver.find_element(By.CSS_SELECTOR, 'input[type="password"]')
            self._simulate_typing(password_input_steam, self.steamdb_pwd)
            print("Filled password.")
            time.sleep(random.uniform(self.ACTION_SHORT_PAUSE_MIN, self.ACTION_SHORT_PAUSE_MAX))

            login_button_steam = self.driver.find_element(By.CLASS_NAME, "DjSvCZoKKfoNSmarsEcTS")
            login_button_steam.click()
            print("Clicked Steam login button.")
            time.sleep(random.uniform(self.PAGE_LOAD_PAUSE_MIN, self.PAGE_LOAD_PAUSE_MAX))

        except (NoSuchElementException, TimeoutException) as e:
            print(f"Could not find username/password fields or login button on Steam page: {e}")
            raise e

    def handle_two_auth(self):
        input("Realize a autenticação de dois fatores atrelada a sua conta e pressione enter")
        time.sleep(random.uniform(self.ACTION_SHORT_PAUSE_MIN, self.ACTION_SHORT_PAUSE_MAX))
        try:
            image_login_button = self.wait.until(EC.element_to_be_clickable((By.ID, "imageLogin")))
            print("Botão 'imageLogin' apareceu. Clicando nele para finalizar o login no Steam...")
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});",
                                       image_login_button)
            time.sleep(self.POST_SCROLL_PAUSE)
            self.driver.execute_script("arguments[0].click();", image_login_button)
            time.sleep(random.uniform(self.ACTION_SHORT_PAUSE_MIN, self.ACTION_SHORT_PAUSE_MAX))

            print("Aguardando redirecionamento para o SteamDB e pelo cookie de sessão...")
            self.wait.until(
                lambda d: d.get_cookie("__Host-steamdb") is not None and \
                          "steamdb.info" in d.current_url and \
                          "login" not in d.current_url.lower() and \
                          "steampowered.com" not in d.current_url.lower()
            )
            print(
                "Login bem-sucedido e redirecionado para o SteamDB após autenticação móvel e clique no 'imageLogin'.")
            time.sleep(random.uniform(self.ACTION_MEDIUM_PAUSE_MIN, self.ACTION_MEDIUM_PAUSE_MAX))

        except TimeoutException:
            print(
                "Botão 'imageLogin' não apareceu ou o redirecionamento para o SteamDB falhou após a etapa de autenticação móvel.")
            if self.driver.get_cookie("__Host-steamdb") and \
                    "steamdb.info" in self.driver.current_url and \
                    "login" not in self.driver.current_url.lower():
                print("No entanto, o login no SteamDB parece ter sido bem-sucedido (cookie encontrado).")
                time.sleep(random.uniform(self.ACTION_MEDIUM_PAUSE_MIN, self.ACTION_MEDIUM_PAUSE_MAX))
            else:
                print("O processo de login ficou parado ou falhou após a etapa de autenticação móvel.")
                time.sleep(random.uniform(self.ACTION_SHORT_PAUSE_MIN, self.ACTION_SHORT_PAUSE_MAX))

    def login(self):
        try:
            self.access_steamdb()  # Movido para cá para garantir que a página seja acessada antes de checar o login
            if self.check_logged():
                return
            print("Not logged in. Attempting login...")
            self.handle_header_login()
            self.click_sign_in_via_steam()
            self.fill_steam_credentials()
            self.handle_two_auth()

        except TimeoutException as e:
            print(f"A timeout occurred during login: {e}")
        except NoSuchElementException as e:
            print(f"An element was not found during login: {e}")
        except Exception as e:
            print(f"An unexpected error occurred during login: {e}")

    def search_game(self, game_name):
        try:
            print(f"Attempting to find search input with itemprop='query-input'.")
            time.sleep(random.uniform(self.ACTION_SHORT_PAUSE_MIN, self.ACTION_SHORT_PAUSE_MAX))
            search_input = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[itemprop="query-input"]'))
            )
            search_input.clear()
            time.sleep(random.uniform(0.3, 0.7))  # Pausa curta após limpar
            self._simulate_typing(search_input, game_name)
            print(f"Filled search input with '{game_name}'.")
            time.sleep(random.uniform(self.ACTION_SHORT_PAUSE_MIN, self.ACTION_SHORT_PAUSE_MAX))

            print(f"Attempting to find search button with aria-label='Perform search'.")
            search_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="Perform search"]'))
            )
            search_button.click()
            print("Clicked search button.")
            time.sleep(random.uniform(self.PAGE_LOAD_PAUSE_MIN, self.PAGE_LOAD_PAUSE_MAX))  # Esperar resultados
            print(f"Search for '{game_name}' performed.")

        except TimeoutException:
            print(f"Error: Could not find search elements or timed out waiting for them.")
        except NoSuchElementException:
            print(f"Error: One of the search elements was not found on the page.")
        except Exception as e:
            print(f"An unexpected error occurred during game search: {e}")

    def enter_game(self, game_name):
        """
        Na página de resultados da pesquisa, encontra e clica em um link de jogo
        dentro da tabela de resultados (ID "table-sortable") que corresponda exatamente a game_name.
        Espera-se que o link esteja na terceira coluna das linhas da tabela.
        """
        print(f"Tentando encontrar e clicar no jogo: '{game_name}' nos resultados da pesquisa.")
        search_results_url = self.driver.current_url

        try:
            self.wait.until(
                EC.presence_of_element_located((By.ID, "table-sortable"))
            )
            print("Tabela de resultados da pesquisa encontrada.")
            time.sleep(random.uniform(self.ACTION_SHORT_PAUSE_MIN, self.ACTION_SHORT_PAUSE_MAX))

            potential_links = self.driver.find_elements(By.XPATH, "//table[@id='table-sortable']/tbody/tr/td[3]/a")

            target_link = None
            for link_candidate in potential_links:
                link_text = self.driver.execute_script("return arguments[0].textContent;", link_candidate)
                if link_text and link_text.strip() == game_name:
                    target_link = link_candidate
                    break

            if not target_link:
                print(
                    f"Jogo '{game_name}' não encontrado na coluna de nome típica (td[3]/a). Tentando uma busca mais ampla nas linhas da tabela...")
                all_links_in_table_rows = self.driver.find_elements(By.XPATH,
                                                                    "//table[@id='table-sortable']/tbody//tr//td/a[@href]")
                for link_candidate in all_links_in_table_rows:
                    link_text = self.driver.execute_script("return arguments[0].textContent;",
                                                           link_candidate).strip()
                    if link_text == game_name:
                        href = link_candidate.get_attribute('href')
                        if href and self.driver.current_url not in href and "javascript:void(0)" not in href:
                            try:
                                parent_td = link_candidate.find_element(By.XPATH, "./parent::td")
                                first_td_in_row = parent_td.find_element(By.XPATH, "./parent::tr/td[1]")
                                if first_td_in_row.text.strip() != game_name:
                                    target_link = link_candidate
                                    print(
                                        f"Encontrado '{game_name}' com busca mais ampla, e não parece ser um link de ID.")
                                    break
                                else:
                                    print(
                                        f"Link candidato '{game_name}' encontrado na busca ampla, mas o texto da primeira célula é igual, possivelmente um link de ID. Continuando...")
                            except NoSuchElementException:
                                target_link = link_candidate
                                print(
                                    f"Encontrado '{game_name}' com busca mais ampla (verificação de TD pai/primeiro TD falhou ou não aplicável).")
                                break

                if not target_link:
                    raise NoSuchElementException(
                        f"Link do jogo com texto exato '{game_name}' não encontrado na tabela de resultados da pesquisa.")

            print(f"Link do jogo encontrado para '{game_name}'.")
            time.sleep(random.uniform(0.3, 0.7))

            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});",
                                       target_link)
            time.sleep(self.POST_SCROLL_PAUSE)
            self.driver.execute_script("arguments[0].click();", target_link)
            print(f"Link do jogo clicado para '{game_name}'.")

            self.wait.until(EC.not_(EC.url_to_be(search_results_url)))
            print(f"Navegado para fora dos resultados da pesquisa. URL atual: {self.driver.current_url}")
            time.sleep(random.uniform(self.PAGE_LOAD_PAUSE_MIN, self.PAGE_LOAD_PAUSE_MAX))

        except TimeoutException:
            print(
                f"Erro: Timeout ao tentar encontrar ou clicar no jogo '{game_name}'. Ele pode não estar nos resultados ou a estrutura da página mudou.")
        except NoSuchElementException as e:
            print(f"Erro: Link do jogo para '{game_name}' não encontrado. {e}")
        except Exception as e:
            print(f"Um erro inesperado ocorreu em enter_game para '{game_name}': {e}")

    def enter_franchise(self):
        """
        Encontra um elemento <i> com texto "Franchise", clica no <a> anterior.
        """
        try:
            print("Tentando encontrar o gatilho da franquia (<i>Franchise</i>)...")
            time.sleep(random.uniform(self.ACTION_SHORT_PAUSE_MIN, self.ACTION_SHORT_PAUSE_MAX))
            try:
                franchise_trigger_link = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH,
                                                "//i[@class='subinfo' and normalize-space(text())='Franchise']/preceding-sibling::a[1]"))
                )
            except TimeoutException:
                print("Nenhum link de franquia encontrado usando o gatilho <i>Franchise</i> e o irmão <a> anterior.")
                return

            franchise_link_href = franchise_trigger_link.get_attribute('href')
            print(f"Encontrado link da franquia através do gatilho <i>: {franchise_link_href}. Clicando nele...")
            franchise_trigger_link.click()
            time.sleep(random.uniform(self.ACTION_SHORT_PAUSE_MIN, self.ACTION_SHORT_PAUSE_MAX))

            self.wait.until(EC.url_contains("/franchise/"))
            print("Navegado para a página da franquia.")
            time.sleep(random.uniform(self.PAGE_LOAD_PAUSE_MIN, self.PAGE_LOAD_PAUSE_MAX))

        except TimeoutException:
            print("Erro: Timeout esperando pelo gatilho principal da franquia ou pela página da franquia carregar.")
        except NoSuchElementException:
            print("Erro: Não foi possível encontrar o gatilho principal da franquia.")
        except Exception as e:
            print(f"Um erro inesperado ocorreu em enter_franchise: {e}")

    def proccess_franchise(self, csv_dir):
        """
        Na página da franquia (que contém a tabela de jogos), itera pelas linhas da tabela.
        Para cada linha com um <div class="subinfo"> vazio, clica no link <a> correspondente.
        """
        print("\nIniciando processamento da tabela de vendas na página de franquia...")
        try:
            if "/franchise/" not in self.driver.current_url:
                print("Não parece estar em uma página de franquia. Abortando proccess_franchise.")
                print(f"URL Atual: {self.driver.current_url}")
                return

            table_id = "DataTables_Table_0"
            try:
                table_sales = self.wait.until(
                    EC.presence_of_element_located((By.ID, table_id))
                )
                print("Tabela de jogos encontrada.")
                time.sleep(random.uniform(self.ACTION_SHORT_PAUSE_MIN, self.ACTION_SHORT_PAUSE_MAX))
            except TimeoutException:
                print(f"Tabela de jogos (ID: {table_id}) não encontrada na página. Abortando.")
                return

            franchise_page_url = self.driver.current_url
            rows_to_process_info = []
            all_rows_in_table = table_sales.find_elements(By.CSS_SELECTOR, "tbody tr.app")

            for index, row_element in enumerate(all_rows_in_table):
                try:
                    subinfo_div = row_element.find_element(By.CSS_SELECTOR, "td div.subinfo")
                    is_empty_js = "return arguments[0].innerHTML.trim() === '';"
                    is_subinfo_empty = self.driver.execute_script(is_empty_js, subinfo_div)

                    if is_subinfo_empty:
                        link_to_click_in_row = row_element.find_element(By.CSS_SELECTOR, "td a.b")
                        link_href = link_to_click_in_row.get_attribute("href")
                        if link_href and link_href != franchise_page_url and "javascript:void(0)" not in link_href:
                            rows_to_process_info.append(
                                {"original_index": index, "href": link_href, "app_name": link_to_click_in_row.text})
                except NoSuchElementException:
                    pass  # Silenciosamente ignora linhas que não correspondem à estrutura

            num_rows_to_click = len(rows_to_process_info)
            print(f"Encontradas {num_rows_to_click} linhas com div.subinfo vazio para processar.")

            if num_rows_to_click == 0:
                return

            for i in range(num_rows_to_click):
                item_info = rows_to_process_info[i]
                original_row_index = item_info["original_index"]

                if self.driver.current_url != franchise_page_url:
                    print(f"Retornando para a página da tabela de franquia: {franchise_page_url}")
                    self.driver.get(franchise_page_url)
                    self.wait.until(lambda driver: driver.current_url == franchise_page_url)
                    self.wait.until(EC.presence_of_element_located((By.ID, table_id)))
                    time.sleep(random.uniform(self.PAGE_LOAD_PAUSE_MIN, self.PAGE_LOAD_PAUSE_MAX))

                try:
                    current_all_rows_recheck = self.driver.find_elements(By.CSS_SELECTOR, f"#{table_id} tbody tr.app")
                    if original_row_index >= len(current_all_rows_recheck):
                        print(
                            f"Índice da linha original {original_row_index} está fora dos limites ({len(current_all_rows_recheck)}). Pulando.")
                        continue
                    current_row_element_recheck = current_all_rows_recheck[original_row_index]
                    actual_subinfo_div_recheck = current_row_element_recheck.find_element(By.CSS_SELECTOR,
                                                                                          "td div.subinfo")
                    if not self.driver.execute_script("return arguments[0].innerHTML.trim() === '';",
                                                      actual_subinfo_div_recheck):
                        print(
                            f"Linha {original_row_index} (App: {item_info['app_name']}): div.subinfo não está mais vazio. Pulando.")
                        continue
                    link_element_to_click_recheck = current_row_element_recheck.find_element(By.CSS_SELECTOR, "td a.b")
                    print(
                        f"\nProcessando linha (índice original {original_row_index}, App: {item_info['app_name']}): Clicando no link {item_info['href']}")
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});",
                                               link_element_to_click_recheck)
                    time.sleep(self.POST_SCROLL_PAUSE)
                    self.driver.execute_script("arguments[0].click();", link_element_to_click_recheck)
                    self.wait.until(lambda driver: driver.current_url != franchise_page_url)
                    print(f"Navegado para: {self.driver.current_url}")
                    time.sleep(random.uniform(self.PAGE_LOAD_PAUSE_MIN, self.PAGE_LOAD_PAUSE_MAX))
                    self.proccess_game(csv_dir=csv_dir)  # Processa o jogo imediatamente após navegar
                except StaleElementReferenceException:
                    print(
                        f"StaleElementReferenceException para linha {original_row_index} (App: {item_info['app_name']}). O DOM mudou.")
                except TimeoutException:
                    print(
                        f"Timeout durante o processamento da linha {original_row_index} (App: {item_info['app_name']}).")
                except Exception as e:
                    print(
                        f"Erro inesperado ao processar linha {original_row_index} (App: {item_info['app_name']}): {e}")

            if self.driver.current_url != franchise_page_url:
                print(f"Retornando para a página da tabela de franquia ({franchise_page_url}) após o loop.")
                self.driver.get(franchise_page_url)
                self.wait.until(lambda driver: driver.current_url == franchise_page_url)
                time.sleep(random.uniform(self.ACTION_SHORT_PAUSE_MIN, self.ACTION_SHORT_PAUSE_MAX))
            print("\nProcessamento da tabela de franquia concluído.")
        except Exception as e:
            print(f"Um erro geral ocorreu em proccess_franchise: {e}")

    def proccess_game(self, csv_dir ):
        current_game_page_url = self.driver.current_url
        print(f"\nIniciando processamento dos gráficos do jogo: {current_game_page_url}")
        game_name_for_file = "dados_jogo_steamdb"
        try:
            h1_element = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1[itemprop='name']")))
            game_name_for_file = h1_element.text.strip()
            if not game_name_for_file: raise ValueError("H1 estava vazio.")
            print(f"Nome do jogo extraído do H1: '{game_name_for_file}'")
        except (NoSuchElementException, TimeoutException, ValueError) as e_h1:
            print(f"Não foi possível extrair o nome do jogo do H1 ({e_h1}), tentando pelo título...")
            try:
                page_title = self.driver.title
                if "· SteamDB" in page_title: game_name_for_file = page_title.split("· SteamDB")[0].strip()
                if "Price history" in game_name_for_file: game_name_for_file = game_name_for_file.replace(
                    "Price history", "").strip()
                if "Steam Charts" in game_name_for_file: game_name_for_file = game_name_for_file.replace("Steam Charts",
                                                                                                         "").strip()
                if not game_name_for_file: game_name_for_file = "dados_jogo_steamdb"
                print(f"Nome do jogo extraído do título: '{game_name_for_file}'")
            except Exception as e_title:
                print(f"Erro ao obter nome do título: {e_title}. Usando nome padrão.")
                game_name_for_file = "dados_jogo_steamdb"
        game_name_for_file = re.sub(r'[^\w\s._-]', '', game_name_for_file).strip().replace(' ', '_')
        if not game_name_for_file: game_name_for_file = "dados_steamdb"
        csv_filename = f"{game_name_for_file}_chart_month_data.csv"

        try:
            print("Tentando clicar na aba 'Charts' (id='tab-charts')...")
            charts_tab_button = self.wait.until(EC.element_to_be_clickable((By.ID, "tab-charts")))
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});",
                                       charts_tab_button)
            time.sleep(self.POST_SCROLL_PAUSE)
            self.driver.execute_script("arguments[0].click();", charts_tab_button)
            print("Aba 'Charts' clicada.")
            time.sleep(random.uniform(self.ACTION_SHORT_PAUSE_MIN, self.ACTION_SHORT_PAUSE_MAX))
            self.wait.until(EC.any_of(EC.url_contains("/charts/"),
                                      EC.presence_of_element_located((By.CSS_SELECTOR, "a#tab-charts.selected"))))
            print(f"Navegado para a aba de gráficos. URL: {self.driver.current_url}")
            table_id = "chart-month-table"
            loading_div_id = "js-chart-month-loading"
            print(f"Esperando pelo div de loading '{loading_div_id}' ficar oculto...")
            self.wait.until(EC.invisibility_of_element_located((By.ID, loading_div_id)))
            time.sleep(random.uniform(0.3, 0.8))  # Pausa após loading sumir
            print(f"Esperando pela tabela '{table_id}' ficar visível...")
            data_table = self.wait.until(EC.visibility_of_element_located((By.ID, table_id)))
            time.sleep(random.uniform(self.ACTION_MEDIUM_PAUSE_MIN,
                                      self.ACTION_MEDIUM_PAUSE_MAX))  # Pausa maior para renderizar tabela
            print("Tabela de dados mensais encontrada e visível.")
            headers = []
            header_elements = data_table.find_elements(By.CSS_SELECTOR, "thead tr th")
            if header_elements:
                headers = [header.text.strip() for header in header_elements]
            else:
                try:
                    first_row_th = data_table.find_elements(By.CSS_SELECTOR, "tbody tr:first-child th")
                    if first_row_th:
                        headers = [th.text.strip() for th in first_row_th]
                    else:
                        first_row_td = data_table.find_elements(By.CSS_SELECTOR, "tbody tr:first-child td")
                        if first_row_td: headers = [td.text.strip() for td in first_row_td]
                except:
                    pass
            if not headers:
                first_data_row_cells_count = data_table.find_elements(By.CSS_SELECTOR, "tbody tr:first-child td")
                if first_data_row_cells_count:
                    headers = [f"Coluna_{i + 1}" for i in range(len(first_data_row_cells_count))]
                else:
                    headers = ["Dados"]; print("Não foi possível determinar os cabeçalhos, usando placeholder.")
            print(f"Cabeçalhos extraídos: {headers}")
            all_rows_data = []
            body_rows = data_table.find_elements(By.CSS_SELECTOR, "tbody tr")
            for row in body_rows:
                cols = row.find_elements(By.TAG_NAME, "td")
                row_data = [ele.text.strip() for ele in cols]
                if any(rd for rd in row_data if rd): all_rows_data.append(row_data)
            if not all_rows_data:
                print(f"Nenhum dado encontrado na tabela '{table_id}'.");
                return
            print(f"Extraídas {len(all_rows_data)} linhas de dados.")
            time.sleep(random.uniform(0.3, 0.7))  # Pausa antes de escrever
            self.csv_writer(headers, all_rows_data, table_id, csv_dir, csv_filename)
        except TimeoutException:
            print(f"Timeout ao processar {current_game_page_url} (gráficos/tabela).")
        except NoSuchElementException:
            print(f"Elemento não encontrado em {current_game_page_url}.")
        except Exception as e:
            print(f"Erro em proccess_game para {current_game_page_url}: {e}")
        finally:
            print(f"Processamento de {current_game_page_url} concluído.")

    def csv_writer(self, headers, rows_data, table_id, csv_dir, csv_filename):
        output_dir = f"csv_data/{csv_dir}"
        os.makedirs(output_dir, exist_ok=True)
        full_csv_path = os.path.join(output_dir, csv_filename)
        with open(full_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            if headers:
                writer.writerow(headers)
            writer.writerows(rows_data)
        print(f"Dados da tabela '{table_id}' salvos em '{full_csv_path}'")

    def close_browser(self):
        if hasattr(self, 'driver'):
            print("Fechando navegador.")
            self.driver.quit()
