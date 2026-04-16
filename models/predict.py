import joblib
from sklearn.pipeline import Pipeline


def load_model(path: str) -> Pipeline:
    return joblib.load(path)


def predict_category(model: Pipeline, text: str) -> str:
    return model.predict([text])[0]
