import sys

from analyzer.medias_to_analyze.Fallout.fallout_analyzer import analyze_fallout
from analyzer.medias_to_analyze.MortalKombat.mortal_kombat_analyzer import analyze_mortal_kombat
from analyzer.medias_to_analyze.TheWitcher.the_witcher_analyzer import analyze_the_witcher
from scraper.execute_scraper import execute_scraper
from scraper.games_to_scraper.games import franchises, games


def main():
    if len(sys.argv) < 2:
        print("Você precisa passar a ação a ser executada(analyze [nome do jogo] ou scraper)")
        return

    action = sys.argv[1]
    if action == "analyze":
        game_name = sys.argv[2]

        if game_name == "thewitcher":
            analyze_the_witcher()
            return

        if game_name == "fallout":
            analyze_fallout()
            return

        if game_name == "mortalkombat":
            analyze_mortal_kombat()
            return

        print("Insira um jogo válido")
        return

    execute_scraper()


if __name__ == "__main__":
    main()
