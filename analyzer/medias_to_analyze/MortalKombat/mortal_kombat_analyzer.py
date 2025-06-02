from analyzer.analyzer import Analyzer
from analyzer.medias_to_analyze.MortalKombat.mortal_kombat import MortalKombat


class MortalKombatAnalyzer(MortalKombat):
    def __init__(self):
        super().__init__()
        self.analyzer = Analyzer(
            media_name=self.media_name,
            game_franchise_name=self.game_franchise_name,
            media_type=self.media_type,
            release_dates=self.release_dates,
            metric="Average"
        )

    def analyze(self):
        self.analyzer.analyze_media()


def main():
    fallout_analyzer = MortalKombatAnalyzer()
    fallout_analyzer.analyze()


if __name__ == "__main__":
    main()
