import os
import sys
import numpy as np

try:
    import xgboost as xgb
except ImportError as exc:
    raise SystemExit("xgboost is not installed. Install with: pip install xgboost") from exc


def load_npz_features(npz_path: str):
    if not os.path.exists(npz_path):
        raise FileNotFoundError(f"Missing file: {npz_path}")
    d = np.load(npz_path)
    try:
        if "X" in d and "y" in d:
            X = d["X"]
            y = d["y"]
        elif "arr_0" in d and "arr_1" in d:
            X = d["arr_0"]
            y = d["arr_1"]
        else:
            raise KeyError(f"Unrecognized keys in {npz_path}: {list(d.keys())}")
    finally:
        # np.load returns an NpzFile which doesn't need explicit close for in-memory .npz
        # keeping symmetry in case of future changes
        pass
    return X, y


def compute_basic_metrics(y_true: np.ndarray, y_prob: np.ndarray):
    # Threshold at 0.5 for class predictions
    y_pred = (y_prob >= 0.5).astype(np.int32)
    correct = (y_true == y_pred).sum()
    total = y_true.size
    accuracy = float(correct) / float(total) if total else 0.0

    # Precision/Recall/F1 (binary, positive=1)
    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())
    tn = int(((y_true == 0) & (y_pred == 0)).sum())

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    # Rates
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    tpr = recall
    return accuracy, precision, recall, f1, fpr, tpr


def main():
    test_path = os.path.join("defender", "models", "features", "test-features.npz")
    val_path = os.path.join("defender", "models", "features", "validation-features.npz")

    print("Loading training (test-features.npz) ...")
    X_train, y_train = load_npz_features(test_path)
    print(f"Train X: {X_train.shape}, y: {y_train.shape}")

    print("Loading validation (validation-features.npz) ...")
    X_val, y_val = load_npz_features(val_path)
    print(f"Val X: {X_val.shape}, y: {y_val.shape}")

    # Reduce memory: optional subsampling
    # Configure sample sizes via environment variables; defaults keep it manageable
    rng = np.random.default_rng(seed=42)
    train_limit = int(os.environ.get("XGB_TRAIN_SAMPLES", "150000"))
    val_limit = int(os.environ.get("XGB_VAL_SAMPLES", "100000"))

    if X_train.shape[0] > train_limit:
        idx = rng.choice(X_train.shape[0], size=train_limit, replace=False)
        X_train = X_train[idx]
        y_train = y_train[idx]
        print(f"Subsampled train to: {X_train.shape}")

    if X_val.shape[0] > val_limit:
        idx = rng.choice(X_val.shape[0], size=val_limit, replace=False)
        X_val = X_val[idx]
        y_val = y_val[idx]
        print(f"Subsampled val to: {X_val.shape}")

    # Ensure float32 to lower memory footprint
    if X_train.dtype != np.float32:
        X_train = X_train.astype(np.float32, copy=False)
    if X_val.dtype != np.float32:
        X_val = X_val.astype(np.float32, copy=False)

    # XGBoost DMatrix
    dtrain = xgb.DMatrix(X_train, label=y_train)
    dval = xgb.DMatrix(X_val, label=y_val)

    # Simple, reasonable defaults
    params = {
        "objective": "binary:logistic",
        "eval_metric": ["auc", "logloss"],
        "eta": 0.1,
        "max_depth": 6,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "tree_method": "hist",  # fast, memory friendly
        # "device": "cuda",  # uncomment if CUDA available
        "nthread": int(os.environ.get("XGB_NTHREAD", str(os.cpu_count() or 4))),
    }

    evals = [(dtrain, "train"), (dval, "validation")]
    print("Training XGBoost ... (this may take a while)")
    booster = xgb.train(
        params=params,
        dtrain=dtrain,
        num_boost_round=200,
        evals=evals,
        early_stopping_rounds=20,
        verbose_eval=25,
    )

    print("Scoring on validation set ...")
    # Use best_iteration when early stopping is enabled; fall back to full model
    best_it = getattr(booster, "best_iteration", None)
    if isinstance(best_it, int) and best_it >= 0:
        val_probs = booster.predict(dval, iteration_range=(0, best_it + 1))
    else:
        val_probs = booster.predict(dval)
    acc, prec, rec, f1, fpr, tpr = compute_basic_metrics(y_val.astype(np.int32), val_probs)
    print(f"Validation accuracy: {acc:.4f}")
    print(f"Validation precision: {prec:.4f}")
    print(f"Validation recall: {rec:.4f}")
    print(f"Validation F1: {f1:.4f}")
    print(f"Validation FPR (threshold=0.5): {fpr:.4f}")
    print(f"Validation TPR (threshold=0.5): {tpr:.4f}")

    # Save model
    out_path = os.path.join("defender", "models", "xgb_model.json")
    booster.save_model(out_path)
    print(f"Saved model to: {out_path}")


if __name__ == "__main__":
    # Allow overriding paths via CLI if needed
    if len(sys.argv) >= 3:
        # Usage: python train_xgb.py <train_npz> <val_npz>
        # Supports either (X,y) or (arr_0,arr_1) keys
        train_npz = sys.argv[1]
        val_npz = sys.argv[2]
        def _load_override(p):
            return load_npz_features(p)
        X_train, y_train = _load_override(train_npz)
        X_val, y_val = _load_override(val_npz)

        dtrain = xgb.DMatrix(X_train, label=y_train)
        dval = xgb.DMatrix(X_val, label=y_val)
        params = {
            "objective": "binary:logistic",
            "eval_metric": ["auc", "logloss"],
            "eta": 0.1,
            "max_depth": 6,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "tree_method": "hist",
        }
        evals = [(dtrain, "train"), (dval, "validation")]
        booster = xgb.train(params=params, dtrain=dtrain, num_boost_round=200, evals=evals, early_stopping_rounds=20, verbose_eval=25)
        val_probs = booster.predict(dval, iteration_range=(0, booster.best_ntree_limit))
        acc, prec, rec, f1, fpr, tpr = compute_basic_metrics(y_val.astype(np.int32), val_probs)
        print(f"Validation accuracy: {acc:.4f}")
        print(f"Validation precision: {prec:.4f}")
        print(f"Validation recall: {rec:.4f}")
        print(f"Validation F1: {f1:.4f}")
        print(f"Validation FPR (threshold=0.5): {fpr:.4f}")
        print(f"Validation TPR (threshold=0.5): {tpr:.4f}")
        booster.save_model("xgb_model.json")
        print("Saved model to xgb_model.json")
    else:
        main()


