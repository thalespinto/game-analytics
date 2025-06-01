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
        # Initialize the undetected_chromedriver WebDriver
        options = uc.ChromeOptions()  # MODIFIED (or use webdriver.ChromeOptions() which uc usually accepts)
        # options.add_argument('--headless')  # Headless with uc can be less effective against detection
        # options.add_argument('--disable-gpu')
        # If you want to use a specific browser version with uc (advanced):
        # self.driver = uc.Chrome(options=options, version_main=114) # Example: use Chrome version 114
        self.driver = uc.Chrome(options=options)  # MODIFIED
        self.wait = WebDriverWait(self.driver, 20)  # Increased wait time for reliability
        self.login()
        self.search_game()
        self.enter_franchise()
        self.proccess_franchise()

    def login(self):
        try:
            print("Accessing steamdb.info...")
            # It's generally better to try and load the page first to see if a CAPTCHA appears,
            # then let the user solve it, then proceed with login logic.
            self.driver.get("https://steamdb.info/")  # Go to main page first

            input("Resolva o captch e pressione Enter para continuar...")

            # Now navigate to the specific page or perform actions
            self.driver.get("https://steamdb.info/watching/")  # Or your target page after CAPTCHA
            print("Navigated to watching page (or your target page).")

            # Check if already logged in by looking for the cookie
            # This check should ideally happen after successfully handling any CAPTCHAs
            # and navigating to a page where login status is clear.
            if self.driver.get_cookie("__Host-steamdb"):
                print("Você já está logado.")
                # self.driver.quit() # Consider if you want to quit immediately or do other things
                # sys.exit()
                return  # Exit the login method if already logged in, but don't exit the whole program yet

            else:
                print("Not logged in. Attempting login...")
                # Click on the login link
                # Ensure the page context is correct after manual CAPTCHA solving
                login_link = self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "header-login")))
                login_link.click()
                print("Clicked header login link.")

                try:
                    sign_in_button = self.wait.until(EC.element_to_be_clickable((By.ID, "js-sign-in")))
                    sign_in_button.click()
                    print("Clicked 'Sign in via Steam' button (js-sign-in).")
                except TimeoutException:
                    print(
                        "Could not find or click 'js-sign-in' button. Page structure might have changed or CAPTCHA interference.")
                    # self.driver.quit() # Decide on error handling
                    return

                try:
                    self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="text"]')))
                    print("Steam login page loaded.")
                except TimeoutException:
                    print("Steam login page did not load as expected.")
                    try:
                        direct_submit_button = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
                        if direct_submit_button.is_displayed() and direct_submit_button.is_enabled():
                            direct_submit_button.click()
                            print("Você fez o login com sua conta Steam (direct submit).")
                            self.wait.until(EC.url_contains("steamdb.info"))
                            print("Login successful, redirected back to SteamDB.")
                            # self.driver.quit()
                            # sys.exit()
                            return
                    except NoSuchElementException:
                        print("No direct submit button found initially on Steam page.")
                    except TimeoutException:
                        print("Timed out waiting for redirection after direct submit.")
                        # self.driver.quit()
                        return

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
                    try:
                        fallback_submit_button = self.wait.until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="submit"]')))
                        fallback_submit_button.click()
                        print(
                            "Você fez o login com sua conta Steam (fallback submit after attempting credential entry).")
                        self.wait.until(EC.url_contains("steamdb.info"))
                        print("Login successful, redirected back to SteamDB.")
                        # self.driver.quit()
                        # sys.exit()
                        return
                    except (NoSuchElementException, TimeoutException):
                        print("No fallback submit button found either. Login process stuck.")
                        # self.driver.quit()
                        return

                try:
                    mobile_auth_text_xpath = "//*[contains(text(), 'Use o aplicativo móvel do Steam para confirmar o início de sessão') or contains(text(), 'Use the Steam Guard Mobile Authenticator to sign in')]"
                    self.wait.until(EC.presence_of_element_located((By.XPATH, mobile_auth_text_xpath)))
                    print("Steam Guard (mobile app confirmation) detected. Please authorize on your mobile device.")
                    print("Waiting for mobile authorization...")

                    # Improved wait after mobile auth: wait for a specific, reliable element on steamdb.info
                    # or a significant URL change that confirms login.
                    # Example: Wait for an element that only appears when logged in on steamdb.info/watching/
                    # This is more robust than just url_contains("steamdb.info/")
                    self.wait.until(lambda d: d.get_cookie(
                        "__Host-steamdb") is not None and "steamdb.info/watching" in d.current_url)
                    print("Successfully logged in and redirected to SteamDB after mobile auth.")

                    # Attempting to click a final submit button on Steam's page after mobile auth is less common
                    # if Steam automatically redirects. The wait above should handle the redirection.
                    # If a final submit IS needed on Steam's side before redirecting:
                    # try:
                    #     final_submit_button_on_steam = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="submit"], input[type="submit"]'))) # More generic
                    #     print("Found a final submit/authorize button on Steam page after mobile auth.")
                    #     final_submit_button_on_steam.click()
                    #     print("Clicked final submit/authorize button.")
                    #     self.wait.until(EC.url_contains("steamdb.info")) # Wait for redirection
                    #     print("Successfully logged in and redirected to SteamDB after mobile auth and final submit.")
                    # except TimeoutException:
                    #     print("No final submit button found on Steam page after mobile auth, or already redirected.")
                    #     if "__Host-steamdb" in (c['name'] for c in self.driver.get_cookies()) and "steamdb.info" in self.driver.current_url:
                    #          print("Successfully logged in and redirected to SteamDB after mobile auth (checked cookie).")
                    #     else:
                    #         print("Stuck after mobile auth, did not redirect to SteamDB as expected.")


                except TimeoutException:
                    print(
                        "Mobile authenticator prompt not detected, or timed out waiting for login after mobile auth. Checking for other outcomes or trying a generic submit.")
                    try:
                        general_submit_button = self.wait.until(EC.element_to_be_clickable(
                            (By.CSS_SELECTOR, 'button[type="submit"], input[type="submit"]')))
                        general_submit_button.click()
                        print("Clicked a general submit button.")
                        self.wait.until(EC.url_contains("steamdb.info"))
                        # self.wait.until(EC.not_(EC.url_contains("login/"))) # This might be too restrictive if steamdb.info/login is a valid intermediate
                        print("Você fez o login com sua conta Steam (after general submit).")

                    except TimeoutException:
                        print("No general submit button found, or login failed before Steam Guard step.")
                        if self.driver.get_cookie("__Host-steamdb") and "steamdb.info" in self.driver.current_url:
                            print("Login appears successful (cookie found on steamdb.info).")
                        else:
                            print("Login failed or process is stuck.")

        except TimeoutException as e:
            print(f"A timeout occurred: {e}")
        except NoSuchElementException as e:
            print(f"An element was not found: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        # finally: # Consider when to quit. If the script is meant to do more, don't quit here.
        # if hasattr(self, 'driver'):
        #     print("Process finished. To close browser, do it manually or add driver.quit() at the end of your main script flow.")
        #     # self.driver.quit() # Uncomment if you want to close browser at the end of login() regardless
        # sys.exit() # Avoid exiting mid-process if the class is to be used for more tasks

    def search_game(self, game_name="fallout"): # Added game_name parameter
        """
        Searches for a game on SteamDB.
        """
        try:
            # It's good practice to wait for the search input to be ready
            print(f"Attempting to find search input with itemprop='query-input'.")
            search_input = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[itemprop="query-input"]'))
            )
            search_input.clear() # Clear any existing text
            search_input.send_keys(game_name)
            print(f"Filled search input with '{game_name}'.")

            # Find and click the search button
            # The aria-label might be specific, ensure it's correct.
            # Using CSS selector for aria-label.
            print(f"Attempting to find search button with aria-label='Perform search'.")
            search_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="Perform search"]'))
            )
            search_button.click()
            print("Clicked search button.")
            print(f"Search for '{game_name}' performed. Check the browser.")
            # Add a small delay to see the search results page load if needed
            # import time
            # time.sleep(5)

        except TimeoutException:
            print(f"Error: Could not find search elements or timed out waiting for them.")
        except NoSuchElementException:
            print(f"Error: One of the search elements was not found on the page.")
        except Exception as e:
            print(f"An unexpected error occurred during game search: {e}")

    def enter_franchise(self):
        """
        Encontra um elemento <i> com texto "Franchise", clica no <a> anterior,
        e então itera pelas seções subinfo para clicar em links, ir para gráficos e voltar.
        """
        try:
            print("Tentando encontrar o gatilho da franquia (<i>Franchise</i>)...")
            # Assumindo que estamos em uma página onde tal gatilho pode existir (ex: página de um jogo)
            # Se não, navegue para uma página relevante primeiro:
            # self.driver.get("URL_DE_UMA_PAGINA_DE_JOGO_COM_GATILHO_DE_FRANQUIA")
            # time.sleep(2) # Permite que a página carregue

            # Encontra todos os elementos <i> com classe 'subinfo' e texto 'Franchise'
            # Usar XPath para encontrar o <i> e depois seu irmão <a> anterior
            # //i[@class='subinfo' and normalize-space(text())='Franchise']/preceding-sibling::a[1]
            # O [1] garante que pegamos o irmão <a> mais próximo antes do <i>
            franchise_trigger_link = None
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
            # Scroll para o elemento pode ser útil se ele não estiver visível
            # self.driver.execute_script("arguments[0].scrollIntoView(true);", franchise_trigger_link)
            # time.sleep(0.5)
            franchise_trigger_link.click()

            self.wait.until(EC.url_contains("/franchise/"))  # Espera que a URL mude para a página da franquia
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
        Na página da franquia (que contém a tabela de vendas), itera pelas linhas da tabela.
        Para cada linha com um <div class="subinfo"> vazio, clica no link <a> correspondente.
        """
        print("\nIniciando processamento da tabela de vendas na página de franquia...")
        try:
            if "/franchise/" not in self.driver.current_url:
                print("Não parece estar em uma página de franquia. Abortando proccess_franchise.")
                print(f"URL Atual: {self.driver.current_url}")
                return

            table_id = "DataTables_Table_0"  # ID da tabela de vendas
            try:
                table_sales = self.wait.until(
                    EC.presence_of_element_located((By.ID, table_id))
                )
                print("Tabela de vendas encontrada.")
            except TimeoutException:
                print(f"Tabela de vendas (ID: {table_id}) não encontrada na página. Abortando.")
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
                    # else:
                    # content_debug = self.driver.execute_script("return arguments[0].innerHTML;", subinfo_div).strip()
                    # print(f"Linha {index}: div.subinfo NÃO está vazio. Conteúdo: '{content_debug[:50]}...'")
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

                    # ----- PONTO DA MODIFICAÇÃO PRINCIPAL -----
                    # Substituir EC.not_(EC.url_to_be(franchise_page_url))
                    self.wait.until(lambda driver: driver.current_url != franchise_page_url)
                    # -------------------------------------------
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
            # h1_element = self.driver.find_element(By.CSS_SELECTOR, "div.pagehead-title h1[itemprop='name']") # Mais específico
            game_name_for_file = h1_element.text.strip()
            if not game_name_for_file:
                raise ValueError("H1 estava vazio.")  # Usar ValueError para ser pego pelo except abaixo
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
            time.sleep(0.3)  # Pausa após scroll
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
                (By.ID, loading_div_id)))  # Espera até que o loader não seja mais visível

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

            # 6. Escrever dados no arquivo CSV
            # Certificar-se de que o diretório 'csv_data' existe
            output_dir = "csv_data"
            os.makedirs(output_dir, exist_ok=True)
            full_csv_path = os.path.join(output_dir, csv_filename)

            with open(full_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                if headers:
                    writer.writerow(headers)
                writer.writerows(all_rows_data)

            print(f"Dados da tabela '{table_id}' salvos em '{full_csv_path}'")

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
            # The login logic is called in __init__
            # If login is successful and you want to do more, add code here.
            # For example, after login:
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