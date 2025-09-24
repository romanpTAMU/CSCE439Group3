import os
import sys
import json
import numpy as np

# Apply runtime compatibility shims (modeled after test_ember_simple_fix)
def apply_runtime_fixes():
    import numpy as _np
    if not hasattr(_np, 'int'):
        _np.int = int  # type: ignore[attr-defined]
    try:
        import lief as _lief
        _lief.bad_format = _lief.lief_errors.file_format_error
        _lief.bad_file = _lief.lief_errors.file_error
        _lief.pe_error = _lief.lief_errors.parsing_error
        _lief.parser_error = _lief.lief_errors.parsing_error
        _lief.read_out_of_bound = _lief.lief_errors.read_out_of_bound
        _lief.not_implemented = _lief.lief_errors.not_implemented
    except Exception:
        pass
    try:
        from sklearn.feature_extraction._hash import FeatureHasher as _FH
        _orig = _FH.transform
        def _patched(self, X, *args, **kwargs):
            if isinstance(X, str) or (isinstance(X, list) and len(X) == 1 and isinstance(X[0], str)):
                X = [[X] if isinstance(X, str) else X]
            return _orig(self, X, *args, **kwargs)
        _FH.transform = _patched  # type: ignore[assignment]
    except Exception:
        pass


def extract_features_from_exe(exe_path: str) -> np.ndarray:
    """
    Extract a (1, 2381) feature vector from a Windows PE executable using Ember.
    """
    apply_runtime_fixes()
    try:
        from ember.features import PEFeatureExtractor
    except Exception as exc:
        raise RuntimeError("Failed to import ember. Ensure ember is installed.") from exc

    if not os.path.exists(exe_path):
        raise FileNotFoundError(f"File not found: {exe_path}")

    with open(exe_path, "rb") as f:
        bytez = f.read()

    extractor = PEFeatureExtractor()
    vec = extractor.feature_vector(bytez)
    arr = np.asarray(vec, dtype=np.float32).reshape(1, -1)
    if arr.shape[1] != 2381:
        raise ValueError(f"Expected 2381 features, got {arr.shape[1]}")
    return arr


def score_exe(exe_path: str, threshold: float = 0.5) -> dict:
    # Robust import whether run as a module or a script
    try:
        from defender.models.predict_xgb import predict_proba, predict_label  # type: ignore
    except Exception:
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
        if root not in sys.path:
            sys.path.insert(0, os.path.abspath(os.path.join(root, os.pardir)))
        from defender.models.predict_xgb import predict_proba, predict_label  # type: ignore
    X = extract_features_from_exe(exe_path)
    prob = float(predict_proba(X)[0])
    label = int(prob >= threshold)
    return {
        "prob_malware": prob,
        "label": label,
        "threshold": threshold,
        "num_features": int(X.shape[1]),
    }


def _cli():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python defender/inference_service.py <path_to_exe>")
        raise SystemExit(2)
    exe_path = sys.argv[1]
    res = score_exe(exe_path)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    _cli()


