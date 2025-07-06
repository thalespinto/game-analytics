from analise import Analyzer
from analise.medias_to_analyze.TheWitcher.the_witcher import TheWitcher


class TheWitcherAnalyzer(TheWitcher):
    def __init__(self):
        super().__init__()
        self.analyzer = Analyzer(
            media_name=self.media_name,
            game_franchise_name=self.game_franchise_name,
            media_type=self.media_type,
            release_dates=self.release_dates,
            combine=True,
            metric="Peak"
        )

    def analyze(self):
        self.analyzer.analyze_media()


def analyze_the_witcher():
    fallout_analyzer = TheWitcherAnalyzer()
    fallout_analyzer.analyze()
