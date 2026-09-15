#!/usr/bin/env python3
"""Rewrite the unguard image tags in a chart values.yaml.

Used by .github/workflows/deploy-eks.yml so a deploy can pick up images that
src-ghcr-build.yml just published under a commit-SHA tag, without anyone having to
commit a values.yaml change first.

Only unguard's own images are touched. Third-party images (curl, busybox, mariadb,
ollama, ...) keep their pinned tags, because a unguard commit SHA is meaningless to them.

    ./set-image-tag.py chart/values.yaml d60cce9
"""
import sys

from ruamel.yaml import YAML

# Match on the repository path, not a substring of the whole string: 'dynatrace-oss' in
# repo would also rewrite something like ghcr.io/someone/dynatrace-oss-mirror/....
UNGUARD_IMAGE_PREFIXES = (
    "ghcr.io/dynatrace-oss/unguard/",
    "ghcr.io/appsec-ai-initiative-dev/unguard/",
)


def retag(node, tag, changed):
    """Walk the values tree and retag every {repository, tag} pair we own."""
    if isinstance(node, dict):
        repo = node.get("repository")
        if (
            "tag" in node
            and isinstance(repo, str)
            and repo.startswith(UNGUARD_IMAGE_PREFIXES)
        ):
            node["tag"] = tag
            changed.append(repo)
        for value in node.values():
            retag(value, tag, changed)
    elif isinstance(node, list):
        for item in node:
            retag(item, tag, changed)


def main():
    if len(sys.argv) != 3:
        sys.exit(f"usage: {sys.argv[0]} <values.yaml> <image-tag>")
    values_path, tag = sys.argv[1], sys.argv[2]

    yaml = YAML()
    yaml.preserve_quotes = True
    # Match the chart's existing style so the rewrite touches only the tag lines.
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.width = 4096  # never re-wrap long scalars (e.g. attackerIps)
    with open(values_path, encoding="utf-8") as f:
        values = yaml.load(f)

    changed = []
    retag(values, tag, changed)
    if not changed:
        sys.exit(
            f"no unguard images found in {values_path}; expected repositories under "
            f"{' or '.join(UNGUARD_IMAGE_PREFIXES)}"
        )

    with open(values_path, "w", encoding="utf-8") as f:
        yaml.dump(values, f)

    print(f"retagged {len(changed)} image(s) to '{tag}':")
    for repo in changed:
        print(f"  {repo}")


if __name__ == "__main__":
    main()
