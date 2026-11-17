---
name: query-sentry
description: Query Sentry issues, events, stack traces, releases, environments, and tags for read-only production investigation evidence.
---
Start with `find_organizations`; if it is empty, ask for the org slug or take it from a shared Sentry link, then call `find_projects` with that organization and pass it onward. Omit `regionUrl` unless a tool supplies one.
1. Establish project, environment, release, and time range (discover them if not given).
2. Search issues broadly with `search_issues`; open relevant ones with `get_sentry_resource` and inspect representative events with `search_events`, not just titles or counts.
3. Capture exception type and message, responsible frames (file path, function, line), first/last seen, volume, release, environment, and the tags: `repository` is the GitHub owner/repo that holds the code, `release` is the commit SHA that was running, `scenario` is the test case.
4. Classify: new, regressed, ongoing, resolved, or telemetry noise; state uncertainty.
5. Correlate with GitHub via the `repository` tag, the responsible frames and the release: load `query-github` to find the code and the change behind it.
6. Cite the issue or event link and the exact supporting evidence.
Read-only: never change issue state, assignments, ownership, or alerts. Never reproduce secrets, tokens, personal data, or full payloads.
