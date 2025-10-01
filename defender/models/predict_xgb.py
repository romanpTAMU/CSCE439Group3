import os
import sys
import numpy as np

try:
    import xgboost as xgb
except ImportError as exc:
    raise SystemExit("xgboost is not installed. Install with: pip install xgboost") from exc


_CACHED_BOOSTER = None
_MODEL_PATH = os.path.join("defender", "models", "xgb_model.json")


def load_booster(model_path: str = None) -> xgb.Booster:
    global _CACHED_BOOSTER
    if _CACHED_BOOSTER is not None:
        return _CACHED_BOOSTER
    path = model_path or _MODEL_PATH
    if not os.path.exists(path):
        raise FileNotFoundError(f"Model not found at {path}. Train with train_xgb.py first.")
    booster = xgb.Booster()
    booster.load_model(path)
    _CACHED_BOOSTER = booster
    return booster


def predict_proba(features: np.ndarray, model_path: str = None) -> np.ndarray:
    if features.ndim != 2:
        raise ValueError(f"features must be 2D (n_samples, n_features); got shape {features.shape}")
    if features.dtype != np.float32:
        features = features.astype(np.float32, copy=False)
    booster = load_booster(model_path)
    dmat = xgb.DMatrix(features)
    # Use best_iteration when available
    best_it = getattr(booster, "best_iteration", None)
    if isinstance(best_it, int) and best_it >= 0:
        probs = booster.predict(dmat, iteration_range=(0, best_it + 1))
    else:
        probs = booster.predict(dmat)
    return probs


def predict_label(features: np.ndarray, threshold: float = 0.5, model_path: str = None) -> np.ndarray:
    probs = predict_proba(features, model_path=model_path)
    return (probs >= threshold).astype(np.int32)


def _cli():
    if len(sys.argv) < 2:
        print("Usage: python defender/models/predict_xgb.py <npy_or_npz_path>")
        sys.exit(2)
    inp = sys.argv[1]
    X = None
    if inp.endswith(".npz"):
        d = np.load(inp)
        if "X" in d:
            X = d["X"]
        elif "arr_0" in d:
            X = d["arr_0"]
        else:
            raise SystemExit(f"Unsupported npz keys: {list(d.keys())}")
    else:
        X = np.load(inp)
    probs = predict_proba(X)
    print(probs[:10])


if __name__ == "__main__":
    _cli()
