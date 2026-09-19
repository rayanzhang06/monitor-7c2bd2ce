# Monitor

Public, read-only strategy dashboard. No authentication: published holdings and amounts are publicly readable, including earlier committed snapshots. Search-engine exclusion is not access control.

The Mac runs the production model and independently verifies its authority. This repository only displays its results; GitHub Actions validates and deploys the static `site/` directory.

`snapshot.json` and `calendar.json` are generated together. The page compares their dates against the current XSHG session and labels stale observations as historical. Reloading the page does not trigger computation.

Source baseline: existing Sites version 11, commit `1b5f485c3aadf3ee551145dcb4d9999012a2792b`. UI and asset overlay calculations were preserved; server-only endpoints were removed.

Validation: `python3 validate.py` and `node --test tests/*.test.cjs`.

Never add credentials, raw account evidence, source account routes, local paths, or strategy runtime code. Model computations and confirmed account records remain outside this repository.
