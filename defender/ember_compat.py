import typing as _t


def apply_ember_lief_shims() -> None:
	"""
	Install runtime shims so EMBER written for older LIEF releases runs on LIEF >= 0.12.

	- Map legacy exception names (e.g., lief.bad_format) to the modern lief.lief_errors.*
	- Quiet LIEF logger by default to avoid overhead on large/malformed binaries.
	- Provide minimal attribute back-compat where feasible.
	"""
	try:
		import lief  # type: ignore
		# Configure logger (quiet by default). If LEVEL is not present, ignore.
		try:
			from lief import Logger, LEVEL  # type: ignore
			Logger.set_level(LEVEL.ERROR)
		except Exception:
			pass

		# Map legacy exception names expected by EMBER to modern ones
		# Modern LIEF exposes typed errors under lief.lief_errors
		try:
			errors = getattr(lief, "lief_errors")
			_legacy_to_modern: dict[str, str] = {
				"bad_format": "file_format_error",
				"bad_file": "file_error",
				"pe_error": "parsing_error",
				"parser_error": "parsing_error",
				"read_out_of_bound": "read_out_of_bound",
				"not_implemented": "not_implemented",
				"not_found": "file_not_found",
			}
			for legacy_name, modern_name in _legacy_to_modern.items():
				if not hasattr(lief, legacy_name):
					modern_exc = getattr(errors, modern_name, Exception)
					setattr(lief, legacy_name, modern_exc)
		except Exception:
			# Fallback: synthesize Exception classes so try/except in EMBER still works
			class _DummyException(Exception):
				pass
			for legacy_name in (
				"bad_format",
				"bad_file",
				"pe_error",
				"parser_error",
				"read_out_of_bound",
				"not_implemented",
				"not_found",
			):
				if not hasattr(lief, legacy_name):
					setattr(lief, legacy_name, _DummyException)

		# Optional: provide Section.data back-compat where possible
		try:
			PE = getattr(lief, "PE")
			Section = getattr(PE, "Section")
			# Only patch if attribute doesn't already exist
			if not hasattr(Section, "data") and hasattr(Section, "content"):
				# Expose read-only view that returns the same as content
				def _get_data(self: _t.Any):  # type: ignore[no-redef]
					return self.content
				setattr(Section, "data", property(_get_data))
		except Exception:
			pass
	except Exception:
		# If lief is not available, do nothing; caller will handle import errors
		pass


