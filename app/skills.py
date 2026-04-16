import joblib
from pathlib import Path

MODELS_DIR = Path(__file__).parent.parent / "models"


class Skills:
    """Loads all .pkl models from /models/. Add methods as needed."""

    def __init__(self) -> None:
        self.models: dict = {}
        self._load_models()

    def _load_models(self) -> None:
        for pkl_file in MODELS_DIR.glob("*.pkl"):
            self.models[pkl_file.stem] = joblib.load(pkl_file)

    def available_models(self) -> list[str]:
        return list(self.models.keys())
