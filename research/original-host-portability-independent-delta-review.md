# Independent original-host portability delta review

Verdict: PASS for the narrowly scoped wrapper delta. This review does not replace the historical portable-unittest review and does not change any frozen source, test, runtime manifest, or guard.

Reviewed identities:

- `research/portable_unittest.py`: `145fb07c9b460f1d3901286a12a0f78800ef4ff10937cf65069c3612e8895a06`
- `tests/test_original_host_test_portability.py`: `7b10388d431f147e8e12d75dc7535824eb6eeed616639bd697973d1f14a20d48`
- Fixed runtime manifest required by the wrapper: `1bac1b03987d26c32a58575b66f569cf5d5561adc4f0952dfb96ade82d8b5f8a`

The manifest bytes are hashed before its paths are trusted. Its absolute interpreter must appear in its nonempty pin mapping. Every present pin is checked even when a preceding pin is absent. Only `FileNotFoundError` constitutes absence; other read failures propagate. Missing pins are permitted only on the exact platform string `linux` and only when the original interpreter is absent. A matching library may remain when the interpreter is absent: this is explicitly permitted by the predicate, and is not a waiver for any mismatched present pin. Missing files on macOS or another platform, or a missing library with a present interpreter, fail.

Selection requires exactly one occurrence of each of the five explicit test IDs, accepting the optional `tests.` module prefix. Missing or duplicate target IDs fail before running the suite. Only those five instances are wrapped; availability errors remain errors, and an available runtime runs the original test. The existing separate anchor integration policy remains independently applied and unchanged. Thus the whole wrapper has that historical anchor target plus these five newly reviewed host integration targets; this delta should not be described as only five skips across the entire suite.

Executed `.venv/bin/python -m unittest tests.test_original_host_test_portability tests.test_portable_unittest -v`: all 16 tests passed. Independently exercised nine temporary-fixture cases: a complete macOS runtime; Linux interpreter absence with a matching present library; absence on each of darwin, win32, freebsd, and differently capitalized Linux; a synthetic permission error; a mismatched library following an absent interpreter; and a missing library with a present interpreter. All expected outcomes passed. No saved proof, solver, source decode, or large-grid geometry was executed.

The wrapper is a portability policy, not evidence that the five skipped integrations passed on Linux. All other discovered tests retain their original behavior.
