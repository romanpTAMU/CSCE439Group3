import os
import sys
import argparse
import numpy as np


# Ensure project root is on sys.path so `defender` can be imported when running this file directly
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_THIS_DIR, os.pardir))
if _PROJECT_ROOT not in sys.path:
	sys.path.insert(0, _PROJECT_ROOT)


def _find_features_and_labels_keys(data: np.lib.npyio.NpzFile) -> tuple[str, str]:
	"""
	Detect keys for features and labels in a flexible way.
	Searches common names used across our datasets.
	"""
	feature_candidates = ["features", "X", "arr_0"]
	label_candidates = ["labels", "y", "arr_1"]

	feature_key = None
	for k in feature_candidates:
		if k in data and len(np.asarray(data[k]).shape) == 2:
			feature_key = k
			break
	if feature_key is None:
		raise KeyError(f"Could not find features key among {feature_candidates}; found: {list(data.files)}")

	label_key = None
	for k in label_candidates:
		if k in data and len(np.asarray(data[k]).shape) == 1:
			label_key = k
			break
	if label_key is None:
		raise KeyError(f"Could not find labels key among {label_candidates}; found: {list(data.files)}")

	return feature_key, label_key


def _iter_candidate_files(path: str):
	"""Yield executable-like files under path. Accept no-extension files too."""
	valid_exts = {".exe", ".dll", ".sys", ".scr"}
	if os.path.isdir(path):
		seen = set()
		for root, _, files in os.walk(path):
			for name in files:
				p = os.path.join(root, name)
				ext = os.path.splitext(name)[1].lower()
				if ext in valid_exts or ext == "":
					# de-dup by inode-ish tuple (path lower)
					key = os.path.normcase(os.path.abspath(p))
					if key in seen:
						continue
					seen.add(key)
					yield p
	else:
		yield path


def main():
	parser = argparse.ArgumentParser(description="Validate ember_compat and feature vector alignment")
	parser.add_argument("input", help="Path to PE file or directory of files to test")
	parser.add_argument("--val-npz", dest="val_npz", default=os.path.join("defender", "models", "features", "validation-features.npz"), help="Path to validation-features.npz")
	args = parser.parse_args()

	# Install shims and verify legacy names exist
	from defender.ember_compat import apply_ember_lief_shims
	apply_ember_lief_shims()
	import lief  # type: ignore
	for legacy_name in ("bad_format", "bad_file", "pe_error", "parser_error", "read_out_of_bound", "not_implemented", "not_found"):
		if not hasattr(lief, legacy_name):
			raise RuntimeError(f"ember_compat shim failed to expose lief.{legacy_name}")

	# Load validation features to determine expected dimensionality
	if not os.path.exists(args.val_npz):
		raise FileNotFoundError(f"Validation npz not found: {args.val_npz}")
	val = np.load(args.val_npz)
	feat_k, label_k = _find_features_and_labels_keys(val)
	X_val = np.asarray(val[feat_k])
	expected_dim = int(X_val.shape[1])

	# Use project extractor (ensures same runtime fixes)
	from defender.inference_service import extract_features_from_exe

	files = list(_iter_candidate_files(args.input))
	if not files:
		raise SystemExit("No candidate files found to test.")

	total = 0
	ok = 0
	fail = 0
	for fpath in files:
		total += 1
		try:
			X = extract_features_from_exe(fpath)
			if X.shape != (1, expected_dim):
				print(f"FAIL: {fpath} -> shape {X.shape}, expected (1,{expected_dim})")
				fail += 1
				continue
			if not np.all(np.isfinite(X)):
				print(f"FAIL: {fpath} -> non-finite values in vector")
				fail += 1
				continue
			print(f"OK:   {fpath} -> (1,{expected_dim})")
			ok += 1
		except Exception as exc:
			print(f"ERROR: {fpath} -> {exc}")
			fail += 1

	print("")
	print(f"Summary: total={total} ok={ok} fail={fail} expected_dim={expected_dim}")
	if fail > 0:
		raise SystemExit(1)


if __name__ == "__main__":
	main()


