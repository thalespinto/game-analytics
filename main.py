import time

from games_to_scraper.games import games
from games_to_scraper.games import franchises
from scraper.steamdb_scraper import MonthlyPlayersSteamDBScraper


def main():
    steamdb_scraper = MonthlyPlayersSteamDBScraper()
    steamdb_scraper.access_steamdb()
    steamdb_scraper.login()
    for game in games:
        steamdb_scraper.search_game(game)
        steamdb_scraper.enter_game(game)
        steamdb_scraper.proccess_game(csv_dir=game)
        print("O programa irá esperar por 10 segundso para evitar captcha.")
        time.sleep(10)

    for franchise in franchises:
        steamdb_scraper.search_game(franchise)
        steamdb_scraper.enter_franchise()
        steamdb_scraper.proccess_franchise(csv_dir=franchise)
        print("O programa irá esperar por 10 segundso para evitar captcha.")
        time.sleep(10)


if __name__ == '__main__':
    main()
