import sys

from analyzer.medias_to_analyze.Fallout.fallout_analyzer import analyze_fallout
from analyzer.medias_to_analyze.MortalKombat.mortal_kombat_analyzer import analyze_mortal_kombat
from analyzer.medias_to_analyze.TheWitcher.the_witcher_analyzer import analyze_the_witcher
from scraper.execute_scraper import execute_scraper
from scraper.games_to_scraper.games import franchises, games


def main():
    execute_scraper()


if __name__ == "__main__":
    main()
