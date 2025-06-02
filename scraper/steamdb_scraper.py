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

load_dotenv()


class MonthlyPlayersSteamDBScraper:
    steamdb_user = os.getenv('STEAMDB_USER')
    steamdb_pwd = os.getenv('STEAMDB_PWD')

    def __init__(self):
        options = uc.ChromeOptions()
        self.driver = uc.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 20)

    def access_steamdb(self):
        print("Accessing steamdb.info...")
        self.driver.get("https://steamdb.info/")

        input("Resolva o captch e pressione Enter para continuar...")
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

    def click_sign_in_via_steam(self):
        try:
            sign_in_button = self.wait.until(EC.element_to_be_clickable((By.ID, "js-sign-in")))
            sign_in_button.click()
            print("Clicked 'Sign in via Steam' button (js-sign-in).")
        except TimeoutException:
            print(
                "Could not find or click 'js-sign-in' button. Page structure might have changed or CAPTCHA interference.")
            raise TimeoutException("Could not find or click 'js")

    def fill_steam_credentials(self):
        try:
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="text"]')))
            print("Steam login page loaded.")
        except TimeoutException:
            print("Steam login page did not load as expected.")
            raise TimeoutException("Steam login page did not load as expected.")

        try:
            print("Attempting to fill Steam credentials...")
            username_input_steam = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input._2GBWeup5cttgbTw8FM3tfx")))
            username_input_steam.send_keys(self.steamdb_user)
            print(f"Filled username: {self.steamdb_user}")

            password_input_steam = self.driver.find_element(By.CSS_SELECTOR, 'input[type="password"]')
            password_input_steam.send_keys(self.steamdb_pwd)
            print("Filled password.")

            login_button_steam = self.driver.find_element(By.CLASS_NAME, "DjSvCZoKKfoNSmarsEcTS")
            login_button_steam.click()
            print("Clicked Steam login button.")

        except (NoSuchElementException, TimeoutException) as e:
            print(f"Could not find username/password fields or login button on Steam page: {e}")
            raise e

    def handle_two_auth(self):
        input("Realize a autenticação de dois fatores atrelada a sua conta e pressione enter")
        try:
            image_login_button = self.wait.until(EC.element_to_be_clickable((By.ID, "imageLogin")))
            print("Botão 'imageLogin' apareceu. Clicando nele para finalizar o login no Steam...")
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});",
                                       image_login_button)
            time.sleep(0.3)
            self.driver.execute_script("arguments[0].click();", image_login_button)

            print("Aguardando redirecionamento para o SteamDB e pelo cookie de sessão...")
            self.wait.until(
                lambda d: d.get_cookie("__Host-steamdb") is not None and \
                          "steamdb.info" in d.current_url and \
                          "login" not in d.current_url.lower() and \
                          "steampowered.com" not in d.current_url.lower()
                # Garante que não estamos mais no domínio do Steam
            )
            print(
                "Login bem-sucedido e redirecionado para o SteamDB após autenticação móvel e clique no 'imageLogin'.")

        except TimeoutException:
            # Isso significa que o 'imageLogin' não apareceu como esperado ou o redirecionamento final falhou
            print(
                "Botão 'imageLogin' não apareceu ou o redirecionamento para o SteamDB falhou após a etapa de autenticação móvel.")
            # Verificar se, apesar disso, o login no SteamDB foi bem-sucedido (ex: redirecionamento automático do Steam)
            if self.driver.get_cookie("__Host-steamdb") and \
                    "steamdb.info" in self.driver.current_url and \
                    "login" not in self.driver.current_url.lower():
                print("No entanto, o login no SteamDB parece ter sido bem-sucedido (cookie encontrado).")
            else:
                print("O processo de login ficou parado ou falhou após a etapa de autenticação móvel.")

    def login(self):
        try:
            if self.check_logged():
                return
            print("Not logged in. Attempting login...")
            self.handle_header_login()
            self.click_sign_in_via_steam()
            self.fill_steam_credentials()
            self.handle_two_auth()

        except TimeoutException as e:
            print(f"A timeout occurred: {e}")
        except NoSuchElementException as e:
            print(f"An element was not found: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    def search_game(self, game_name):
        try:
            # It's good practice to wait for the search input to be ready
            print(f"Attempting to find search input with itemprop='query-input'.")
            search_input = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[itemprop="query-input"]'))
            )
            search_input.clear() # Clear any existing text
            search_input.send_keys(game_name)
            print(f"Filled search input with '{game_name}'.")

            print(f"Attempting to find search button with aria-label='Perform search'.")
            search_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="Perform search"]'))
            )
            search_button.click()
            print("Clicked search button.")
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
        """
        print(f"Tentando encontrar e clicar no jogo: '{game_name}' nos resultados da pesquisa.")

        try:
            # Esperar que a tabela esteja presente
            self.wait.until(
                EC.presence_of_element_located((By.ID, "table-sortable"))
            )  #
            print("Tabela de resultados da pesquisa encontrada.")

            # Obter todos os links de nome de jogo da terceira coluna de cada linha relevante no corpo da tabela
            potential_links = self.driver.find_elements(By.XPATH, "//table[@id='table-sortable']/tbody/tr/td[3]/a")  #

            target_link = None
            for link_candidate in potential_links:
                # Usar JavaScript para obter textContent pode ser mais confiável do que .text para correspondências exatas
                link_text = self.driver.execute_script("return arguments[0].textContent;", link_candidate)  #
                if link_text and link_text.strip() == game_name:  #
                    target_link = link_candidate
                    break

            print(f"Link do jogo encontrado para '{game_name}'.")

            # Rolar até o elemento e clicar
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});",
                                       target_link)  #
            time.sleep(0.5)  # Breve pausa após rolar antes de clicar
            self.driver.execute_script("arguments[0].click();",
                                       target_link)  # Clique com JavaScript pode ser mais robusto #
            print(f"Link do jogo clicado para '{game_name}'.")

            print(f"Navegado para fora dos resultados da pesquisa. URL atual: {self.driver.current_url}")
            time.sleep(1)  # Permitir um segundo para a nova página começar a renderizar

        except TimeoutException:
            print(
                f"Erro: Timeout ao tentar encontrar ou clicar no jogo '{game_name}'. Ele pode não estar nos resultados ou a estrutura da página mudou.")
            # raise # Re-levante se o chamador precisar lidar com isso, ou lide aqui
        except NoSuchElementException as e:
            print(f"Erro: Link do jogo para '{game_name}' não encontrado. {e}")
            # raise
        except Exception as e:
            print(f"Um erro inesperado ocorreu em enter_game para '{game_name}': {e}")
            # raise

    def enter_franchise(self):
        """
        Encontra um elemento <i> com texto "Franchise", clica no <a> anterior.
        """
        try:
            print("Tentando encontrar o gatilho da franquia (<i>Franchise</i>)...")
            try:
                # Tentativa de encontrar o link <a> diretamente com XPath
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

            self.wait.until(EC.url_contains("/franchise/"))
            print("Navegado para a página da franquia.")
            time.sleep(1)

        except TimeoutException:
            print("Erro: Timeout esperando pelo gatilho principal da franquia ou pela página da franquia carregar.")
        except NoSuchElementException:  # Embora o try/except interno já pegue Timeout para o link
            print("Erro: Não foi possível encontrar o gatilho principal da franquia.")
        except Exception as e:
            print(f"Um erro inesperado ocorreu em enter_franchise: {e}")

    def proccess_franchise(self):
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

            table_id = "DataTables_Table_0"  # ID da tabela de jogos
            try:
                table_sales = self.wait.until(
                    EC.presence_of_element_located((By.ID, table_id))
                )
                print("Tabela de jogos encontrada.")
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
                        link_to_click_in_row = row_element.find_element(By.CSS_SELECTOR,
                                                                        "td a.b")  # Link do nome do jogo
                        link_href = link_to_click_in_row.get_attribute("href")
                        if link_href and link_href != franchise_page_url and "javascript:void(0)" not in link_href:
                            rows_to_process_info.append(
                                {"original_index": index, "href": link_href, "app_name": link_to_click_in_row.text})
                            print(
                                f"Linha {index}: div.subinfo está vazio. Link para clicar: {link_href} ({link_to_click_in_row.text})")
                except NoSuchElementException:
                    print(f"Linha {index} não tem a estrutura esperada (td a.b ou div.subinfo). Ignorando.")
                    pass

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
                    self.wait.until(lambda driver: driver.current_url == franchise_page_url)  # Verifica igualdade exata
                    self.wait.until(EC.presence_of_element_located((By.ID, table_id)))
                    time.sleep(1)

                try:
                    current_all_rows_recheck = self.driver.find_elements(By.CSS_SELECTOR, f"#{table_id} tbody tr.app")
                    if original_row_index >= len(current_all_rows_recheck):
                        print(
                            f"Índice da linha original {original_row_index} está fora dos limites após recarregar ({len(current_all_rows_recheck)} linhas). Pulando.")
                        continue

                    current_row_element_recheck = current_all_rows_recheck[original_row_index]

                    actual_subinfo_div_recheck = current_row_element_recheck.find_element(By.CSS_SELECTOR,
                                                                                          "td div.subinfo")
                    is_empty_js_recheck = "return arguments[0].innerHTML.trim() === '';"
                    if not self.driver.execute_script(is_empty_js_recheck, actual_subinfo_div_recheck):
                        print(f"Linha {original_row_index}: div.subinfo não está mais vazio (re-verificação). Pulando.")
                        continue

                    link_element_to_click_recheck = current_row_element_recheck.find_element(By.CSS_SELECTOR, "td a.b")

                    print(
                        f"\nProcessando linha (índice original {original_row_index}, App: {item_info['app_name']}): Clicando no link {item_info['href']}")

                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});",
                                               link_element_to_click_recheck)
                    time.sleep(0.5)
                    self.driver.execute_script("arguments[0].click();", link_element_to_click_recheck)
                    self.wait.until(lambda driver: driver.current_url != franchise_page_url)
                    print(f"Navegado para: {self.driver.current_url}")
                    time.sleep(1)

                except StaleElementReferenceException:
                    print(
                        f"StaleElementReferenceException para linha com índice original {original_row_index}. O DOM mudou.")
                    continue
                except TimeoutException:
                    print(f"Timeout durante o processamento da linha {original_row_index}.")
                    continue
                except Exception as e:
                    print(
                        f"Erro inesperado ao processar linha {original_row_index} (link: {item_info.get('href', 'N/A')}): {e}")
                    continue
                self.proccess_game()

            if self.driver.current_url != franchise_page_url:
                print(f"Retornando para a página da tabela de franquia ({franchise_page_url}) após o loop.")
                self.driver.get(franchise_page_url)
                self.wait.until(lambda driver: driver.current_url == franchise_page_url)

            print("\nProcessamento da tabela de franquia concluído.")

        except Exception as e:
            print(f"Um erro geral ocorreu em proccess_franchise: {e}")

    def proccess_game(self):
        """
        Na página de um jogo, clica na aba de gráficos e extrai dados da tabela mensal para CSV.
        """
        current_game_page_url = self.driver.current_url  # URL da página do jogo atual
        print(f"\nIniciando processamento dos gráficos do jogo: {current_game_page_url}")

        game_name_for_file = "dados_jogo_steamdb"  # Nome padrão
        try:
            # Extrair nome do jogo do H1 (prioritário)
            h1_element = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1[itemprop='name']")))
            game_name_for_file = h1_element.text.strip()
            if not game_name_for_file:
                raise ValueError("H1 estava vazio.")
            print(f"Nome do jogo extraído do H1: '{game_name_for_file}'")
        except (NoSuchElementException, TimeoutException, ValueError) as e_h1:
            print(f"Não foi possível extrair o nome do jogo do H1 ({e_h1}), tentando pelo título da página...")
            try:
                page_title = self.driver.title
                # Ex: "The Witcher 3: Wild Hunt Price history · SteamDB" ou "The Witcher 3: Wild Hunt Steam Charts · SteamDB"
                if "· SteamDB" in page_title:
                    game_name_for_file = page_title.split("· SteamDB")[0].strip()
                if "Price history" in game_name_for_file:  # Remover "Price history" se presente
                    game_name_for_file = game_name_for_file.replace("Price history", "").strip()
                if "Steam Charts" in game_name_for_file:  # Remover "Steam Charts" se presente
                    game_name_for_file = game_name_for_file.replace("Steam Charts", "").strip()

                if not game_name_for_file: game_name_for_file = "dados_jogo_steamdb"
                print(f"Nome do jogo extraído do título da página: '{game_name_for_file}'")
            except Exception as e_title:
                print(f"Erro ao tentar obter o nome do jogo do título da página: {e_title}. Usando nome padrão.")
                game_name_for_file = "dados_jogo_steamdb"  # Garante que temos um nome

        # Limpar nome do jogo para ser um nome de arquivo válido
        game_name_for_file = re.sub(r'[^\w\s._-]', '', game_name_for_file).strip().replace(' ', '_')
        if not game_name_for_file: game_name_for_file = "dados_steamdb"  # Último fallback
        csv_filename = f"{game_name_for_file}_chart_month_data.csv"

        try:
            # 1. Clicar na aba de gráficos
            print("Tentando clicar na aba 'Charts' (id='tab-charts')...")
            charts_tab_button = self.wait.until(EC.element_to_be_clickable((By.ID, "tab-charts")))
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});",
                                       charts_tab_button)
            time.sleep(0.3)
            self.driver.execute_script("arguments[0].click();", charts_tab_button)
            print("Aba 'Charts' clicada.")

            # Esperar a URL mudar para a aba de charts OU a aba se tornar 'selected'
            self.wait.until(EC.any_of(
                EC.url_contains("/charts/"),
                EC.presence_of_element_located((By.CSS_SELECTOR, "a#tab-charts.selected"))
            ))
            print(f"Navegado para a aba de gráficos. URL: {self.driver.current_url}")

            # 2. Esperar e localizar a tabela de dados mensais
            table_id = "chart-month-table"
            loading_div_id = "js-chart-month-loading"

            # Esperar o div de loading desaparecer (se tornar hidden) E a tabela estar visível
            print(f"Esperando pelo div de loading '{loading_div_id}' ficar oculto...")
            self.wait.until(EC.invisibility_of_element_located(
                (By.ID, loading_div_id)))

            print(f"Esperando pela tabela de dados mensais (id='{table_id}') ficar visível...")
            data_table = self.wait.until(EC.visibility_of_element_located((By.ID, table_id)))
            time.sleep(1)  # Pausa adicional para garantir que os dados internos da tabela estejam renderizados
            print("Tabela de dados mensais encontrada e visível.")

            # 3. Extrair cabeçalhos da tabela
            headers = []
            header_elements = data_table.find_elements(By.CSS_SELECTOR, "thead tr th")
            if header_elements:
                headers = [header.text.strip() for header in header_elements]
            else:  # Fallback se não houver thead, tentar a primeira linha do tbody
                try:
                    first_row_th = data_table.find_elements(By.CSS_SELECTOR, "tbody tr:first-child th")
                    if first_row_th:
                        headers = [th.text.strip() for th in first_row_th]
                    else:  # Se não houver th na primeira linha, tentar td
                        first_row_td = data_table.find_elements(By.CSS_SELECTOR, "tbody tr:first-child td")
                        if first_row_td: headers = [td.text.strip() for td in first_row_td]
                except:
                    pass  # Ignorar se não conseguir pegar cabeçalhos do tbody

            if not headers:
                first_data_row_cells_count = data_table.find_elements(By.CSS_SELECTOR, "tbody tr:first-child td")
                if first_data_row_cells_count:
                    headers = [f"Coluna_{i + 1}" for i in range(len(first_data_row_cells_count))]
                else:
                    headers = ["Dados"]  # Fallback final
                    print("Não foi possível determinar os cabeçalhos da tabela, usando placeholder.")
            print(f"Cabeçalhos extraídos: {headers}")

            # 4. Extrair linhas de dados da tabela
            all_rows_data = []
            body_rows = data_table.find_elements(By.CSS_SELECTOR, "tbody tr")

            for row in body_rows:
                cols = row.find_elements(By.TAG_NAME, "td")
                row_data = [ele.text.strip() for ele in cols]
                if any(rd for rd in row_data if
                       rd):  # Adicionar apenas se a linha não estiver completamente vazia (ignorando células vazias)
                    all_rows_data.append(row_data)

            if not all_rows_data:
                print(f"Nenhum dado encontrado no corpo da tabela '{table_id}'.")
                return  # Não criar CSV se não houver dados.

            print(f"Extraídas {len(all_rows_data)} linhas de dados.")
            self.csv_writer(headers, all_rows_data, table_id, csv_filename)

        except TimeoutException:
            print(
                f"Timeout ao tentar processar a página do jogo {current_game_page_url} (aba de gráficos ou tabela não encontrada).")
        except NoSuchElementException:
            print(f"Elemento crucial não encontrado na página do jogo {current_game_page_url}.")
        except Exception as e:
            print(f"Um erro inesperado ocorreu em proccess_game para {current_game_page_url}: {e}")
        finally:
            print(f"Processamento da página do jogo {current_game_page_url} concluído.")
            # A navegação de volta é responsabilidade da função chamadora (proccess_franchise)

    def csv_writer(self, headers, rows_data, table_id, csv_filename):
        output_dir = "csv_data"
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


if __name__ == '__main__':
    if not os.getenv('STEAMDB_USER') or not os.getenv('STEAMDB_PWD'):
        print("Please set STEAMDB_USER and STEAMDB_PWD environment variables in your .env file.")
    else:
        print("Attempting to log in to SteamDB using undetected_chromedriver...")
        steam_db_instance = None  # Initialize to ensure it's defined for finally block
        try:
            steam_db_instance = MonthlyPlayersSteamDBScraper()
            if steam_db_instance.driver.get_cookie("__Host-steamdb"):
                print("Login successful. Browser will remain open.")
                print("You can add more automation steps here.")
                input("Press Enter to close the browser and exit...")  # Keep browser open until user interaction
            else:
                print("Login was not successful. Please check the console output.")

        except Exception as e:
            print(f"An error occurred during the process: {e}")
        finally:
            if steam_db_instance:
                steam_db_instance.close_browser()  # Ensure browser is closed
            print("Program finished.")