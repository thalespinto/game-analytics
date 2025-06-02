from analyzer.analyzer import Analyzer
from analyzer.medias_to_analyze.Fallout.fallout import Fallout


class FalloutAnalyzer(Fallout):
    def __init__(self):
        super().__init__()
        self.analyzer = Analyzer(
            media_name=self.media_name,
            game_franchise_name=self.game_franchise_name,
            media_type=self.media_type,
            release_dates=self.release_dates,
        )

    def analyze(self):
        self.analyzer.analyze_media()


def analyze_fallout():
    fallout_analyzer = FalloutAnalyzer()
    fallout_analyzer.analyze()
