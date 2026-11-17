"""What the agent may touch: the two connectors it reads from, and the read-only tools it may call on each.

Everything here is plain data, so the tests can check the policy without a model or a Studio workspace.
"""

import os

import mistralai.agents as agents

# Studio gives every connector a unique name (such as `sentry_d183`), so each workspace supplies its own through the environment.
SENTRY_CONNECTOR_ENV = "SENTRY_CONNECTOR_NAME"
GITHUB_CONNECTOR_ENV = "GITHUB_CONNECTOR_NAME"

# Reviewed read-only tools, per connector. Anything not listed here is denied by the permission policy.
SENTRY_READ_TOOLS = frozenset({"find_organizations", "find_projects", "get_sentry_resource", "search_events", "search_issues"})
GITHUB_READ_TOOLS = frozenset(
    {
        "get_commit",
        "get_file_contents",
        "get_latest_release",
        "get_release_by_tag",
        "get_tag",
        "issue_read",
        "list_branches",
        "list_commits",
        "list_issues",
        "list_pull_requests",
        "list_releases",
        "list_tags",
        "pull_request_read",
        "search_code",
        "search_commits",
        "search_pull_requests",
        "search_repositories",
    }
)


def connector_name(env_var: str) -> str:
    """Read a connector name from the environment, failing loudly so a typo cannot silently drop a connector."""
    name = os.environ.get(env_var, "").strip()
    if not name:
        raise RuntimeError(f"{env_var} is not set. Set it to the name of your connector in the Studio workspace (see README).")
    return name


def connector_namespace(name: str) -> str:
    """The tool namespace the SDK gives a connector: `connector_<name>` with every non-alphanumeric character replaced by `_`."""
    safe = "".join(character if character.isalnum() else "_" for character in name).strip("_")
    return f"connector_{safe or 'connector'}"


def tool_ids(name: str, tools: frozenset[str]) -> tuple[str, ...]:
    """The stable tool IDs (`<namespace>.<tool>`) of `tools` on connector `name`, the form permission rules match on."""
    namespace = connector_namespace(name)
    return tuple(sorted(f"{namespace}.{tool}" for tool in tools))


def read_only_tool_ids(sentry: str, github: str) -> tuple[str, ...]:
    """Every tool ID the agent may call on its two connectors."""
    return tool_ids(sentry, SENTRY_READ_TOOLS) + tool_ids(github, GITHUB_READ_TOOLS)


def permission_policy(sentry: str, github: str) -> agents.PermissionPolicy:
    """Deny every tool call except the reviewed read-only connector tools and the built-ins the agent needs.

    `skill.*` lets the model load the bundled skills; `self.*` and `agents.*` are orchestration tools the runtime always
    allows. The default denies everything else, so a connector that grows a write tool tomorrow stays unreachable.
    """
    return agents.PermissionPolicy(
        default="deny",
        rules=(
            agents.PermissionRule(tools=read_only_tool_ids(sentry, github), decision="allow"),
            agents.PermissionRule(tools=("skill.*",), decision="allow"),
        ),
    )
