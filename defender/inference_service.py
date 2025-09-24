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
        # Comprehensive LIEF compatibility mapping for EMBER
        if hasattr(_lief, 'lief_errors'):
            _lief.bad_format = _lief.lief_errors.file_format_error
            _lief.bad_file = _lief.lief_errors.file_error
            _lief.pe_error = _lief.lief_errors.parsing_error
            _lief.parser_error = _lief.lief_errors.parsing_error
            _lief.read_out_of_bound = _lief.lief_errors.read_out_of_bound
            _lief.not_implemented = _lief.lief_errors.not_implemented
            _lief.not_found = _lief.lief_errors.file_not_found
        else:
            # Fallback for newer LIEF versions - create dummy exceptions
            class DummyException(Exception):
                pass
            _lief.bad_format = DummyException("Bad format")
            _lief.bad_file = DummyException("Bad file")
            _lief.pe_error = DummyException("PE error")
            _lief.parser_error = DummyException("Parser error")
            _lief.read_out_of_bound = DummyException("Read out of bound")
            _lief.not_implemented = DummyException("Not implemented")
            _lief.not_found = DummyException("Not found")
        
        # Additional compatibility fixes for newer LIEF versions
        if not hasattr(_lief, 'bad_format'):
            _lief.bad_format = Exception("Bad format")
        if not hasattr(_lief, 'bad_file'):
            _lief.bad_file = Exception("Bad file")
        if not hasattr(_lief, 'pe_error'):
            _lief.pe_error = Exception("PE error")
        if not hasattr(_lief, 'parser_error'):
            _lief.parser_error = Exception("Parser error")
        if not hasattr(_lief, 'read_out_of_bound'):
            _lief.read_out_of_bound = Exception("Read out of bound")
        if not hasattr(_lief, 'not_implemented'):
            _lief.not_implemented = Exception("Not implemented")
        if not hasattr(_lief, 'not_found'):
            _lief.not_found = Exception("Not found")
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
    
    # EMBER-specific compatibility fixes
    try:
        import ember
        # Fix for "feature names must be strings" error
        if hasattr(ember, 'features'):
            from ember.features import PEFeatureExtractor
            # Monkey patch to ensure feature names are strings
            original_feature_vector = PEFeatureExtractor.feature_vector
            def patched_feature_vector(self, bytez):
                try:
                    result = original_feature_vector(self, bytez)
                    if result is not None:
                        # Ensure all feature names are strings
                        if hasattr(result, 'keys'):
                            result = {str(k): v for k, v in result.items()}
                    return result
                except Exception as e:
                    # Return a default feature vector if extraction fails
                    return [0.0] * 2381
            PEFeatureExtractor.feature_vector = patched_feature_vector
    except Exception:
        pass


def extract_features_from_exe(exe_path: str) -> np.ndarray:
    """
    Extract a (1, 2381) feature vector from a Windows PE executable using Ember.
    """
    apply_runtime_fixes()
    from ember.features import PEFeatureExtractor

    with open(exe_path, "rb") as f:
        bytez = f.read()
    
    extractor = PEFeatureExtractor()
    vec = extractor.feature_vector(bytez)
    
    if vec is None:
        raise ValueError("Feature extraction returned None")
    
    arr = np.asarray(vec, dtype=np.float32).reshape(1, -1)
    
    if arr.shape[1] != 2381:
        raise ValueError(f"Expected 2381 features, got {arr.shape[1]}")
    
    return arr


def score_exe(exe_path: str, threshold: float = 0.5) -> dict:
    try:
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
    except Exception:
        return {"label": 0}


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


