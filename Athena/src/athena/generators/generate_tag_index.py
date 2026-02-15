#!/usr/bin/env python3
"""
Generate TAG_INDEX.md from YAML frontmatter in .context and .agent files.

Usage:
    python3 generate_tag_index.py

Scans all .md files in .context/ and .agent/ for YAML frontmatter with 'tags' field,
then generates a consolidated TAG_INDEX.md in .context/.
"""

import os
import re
from pathlib import Path
from collections import defaultdict

ROOT_DIR = Path(__file__).parent.parent.parent.parent
CONTEXT_DIR = ROOT_DIR / ".context"
AGENT_DIR = ROOT_DIR / ".agent"

# Sharded output paths to avoid token bomb
TAG_INDEX_AM_PATH = CONTEXT_DIR / "TAG_INDEX_A-M.md"
TAG_INDEX_NZ_PATH = CONTEXT_DIR / "TAG_INDEX_N-Z.md"
TAG_INDEX_LEGACY_PATH = CONTEXT_DIR / "TAG_INDEX.md"  # For archiving

# Expanded scan directories for comprehensive zero-blind-spot coverage
DIRS_TO_SCAN = [
    CONTEXT_DIR,
    AGENT_DIR,
    ROOT_DIR / ".framework",
    ROOT_DIR / ".projects",
    ROOT_DIR / "Athena-Public",
    ROOT_DIR / "analysis",
]


def extract_tags_from_file(filepath: Path) -> list[str]:
    """Extract tags from YAML frontmatter AND inline #tags at end of file."""
    tags = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Method 1: Match YAML frontmatter tags
        match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
        if match:
            frontmatter = match.group(1)
            tags_match = re.search(r"^tags:\s*\[(.*?)\]", frontmatter, re.MULTILINE)
            if tags_match:
                tags_str = tags_match.group(1)
                yaml_tags = [t.strip().strip("\"'") for t in tags_str.split(",")]
                tags.extend(
                    [f"#{t}" if not t.startswith("#") else t for t in yaml_tags if t]
                )

        # Method 2: Extract ALL inline #tags from file content
        # Simple pattern: match any #word pattern (no lookahead/lookbehind complexity)
        inline_tags = re.findall(r"#([a-zA-Z][a-zA-Z0-9_-]*)", content)
        tags.extend(
            [f"#{t}" for t in inline_tags if len(t) > 1 and f"#{t}" not in tags]
        )

        return list(set(tags))
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return []


def scan_directories() -> dict[str, list[str]]:
    """Scan targeted directories for tags using parallel processing."""
    tag_to_files = defaultdict(list)
    files_to_scan = []

    # 1. Collect all files first
    for scan_dir in DIRS_TO_SCAN:
        if not scan_dir.exists():
            continue
        for md_file in scan_dir.rglob("*.md"):
            if md_file.name == "TAG_INDEX.md":
                continue
            files_to_scan.append(md_file)

    # 2. Process in parallel
    import concurrent.futures

    # Pre-calculate relative paths to avoid doing it in threads if possible,
    # though pathlib is thread-safe.

    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Map extract_tags_from_file to files
        future_to_file = {
            executor.submit(extract_tags_from_file, f): f for f in files_to_scan
        }

        for future in concurrent.futures.as_completed(future_to_file):
            md_file = future_to_file[future]
            try:
                tags = future.result()

                # Method 3: Fallback Auto-Tagging (Directory-based)
                if not tags:
                    parent_dir = md_file.parent.name
                    auto_tag = "#" + re.sub(r"[^a-zA-Z0-9_-]", "", parent_dir).lower()
                    if len(auto_tag) > 1:
                        tags.append(auto_tag)

                # Calculate path relative to TAG_INDEX location for clickable links
                try:
                    relative_path = os.path.relpath(md_file, CONTEXT_DIR)
                    link_path = relative_path
                except ValueError:
                    link_path = str(md_file)

                for tag in tags:
                    tag_to_files[tag].append(link_path)

            except Exception as e:
                print(f"Error processing {md_file}: {e}")

    return dict(tag_to_files)


def generate_index(
    tag_to_files: dict[str, list[str]], shard_name: str = "", shard_range: tuple = None
) -> str:
    """Generate markdown table for TAG_INDEX.md (supports sharding)."""

    # Filter tags by shard range if specified
    if shard_range:
        start_char, end_char = shard_range

        filtered_tags = {}
        for k, v in tag_to_files.items():
            # Strip leading # for comparison
            compare_key = k.lstrip("#").upper()
            if not compare_key:  # Handle empty tag case
                continue

            if compare_key[0] >= start_char and compare_key[0] <= end_char:
                filtered_tags[k] = v
    else:
        filtered_tags = tag_to_files

    lines = [
        f"# 🏷️ TAG INDEX {shard_name} — Global Hashtag System",
        "",
        "> **Purpose**: Instant file retrieval via keywords.",
        f"> **Shard**: {shard_name} ({len(filtered_tags)} tags)",
        "> **Auto-generated**: Run `python3 .agent/scripts/generate_tag_index.py` to update.",
        "",
        "---",
        "",
        "## 🔍 Tag → Files",
        "",
        "| Tag | Files |",
        "|-----|-------|",
    ]

    for tag in sorted(filtered_tags.keys()):
        files = sorted(set(filtered_tags[tag]))  # Dedup and sort
        files_links = ", ".join([f"`{f}`" for f in files])
        lines.append(f"| {tag} | {files_links} |")

    # Generate Reverse Index (File -> Tags)
    file_to_tags = defaultdict(list)
    for tag, files in filtered_tags.items():
        for file in files:
            file_to_tags[file].append(tag)

    lines.extend(
        [
            "",
            "---",
            "",
            "## 📂 File → Tags",
            "",
            "| File | Tags |",
            "|------|------|",
        ]
    )

    for file in sorted(file_to_tags.keys()):
        tags = sorted(set(file_to_tags[file]))
        tags_str = " ".join(tags)
        lines.append(f"| `{file}` | {tags_str} |")

    lines.extend(
        [
            "",
            "---",
            "",
            f"*{len(filtered_tags)} tags across {len(file_to_tags)} files.*",
        ]
    )

    return "\n".join(lines)


def main():
    print(f"Scanning directories: {[d.name for d in DIRS_TO_SCAN]}...")
    tag_to_files = scan_directories()

    if not tag_to_files:
        print("No tags found.")
        return

    # Generate sharded output files
    shards = [
        (TAG_INDEX_AM_PATH, "(A-M)", ("#", "M")),  # # through M
        (TAG_INDEX_NZ_PATH, "(N-Z)", ("N", "z")),  # N through z
    ]

    for shard_path, shard_name, shard_range in shards:
        index_content = generate_index(tag_to_files, shard_name, shard_range)

        with open(shard_path, "w", encoding="utf-8") as f:
            f.write(index_content)

        print(f"✅ Generated {shard_path.name}")

    # Archive the legacy monolithic file if it exists
    if TAG_INDEX_LEGACY_PATH.exists():
        archive_path = CONTEXT_DIR / "archive" / "TAG_INDEX_legacy.md"
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        TAG_INDEX_LEGACY_PATH.rename(archive_path)
        print(f"📦 Archived legacy TAG_INDEX.md to {archive_path}")

    print(f"   Total: {len(tag_to_files)} unique tags indexed.")

    # Auto-regenerate SKILL_INDEX.md when tag index updates
    skill_index_script = ROOT_DIR / "src/athena/generators/generate_skill_index.py"
    if skill_index_script.exists():
        import subprocess

        try:
            result = subprocess.run(
                ["python3", str(skill_index_script)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                print("✅ SKILL_INDEX.md auto-regenerated")
            else:
                print(f"⚠️  SKILL_INDEX generation failed: {result.stderr[:100]}")
        except Exception as e:
            print(f"⚠️  SKILL_INDEX generation error: {e}")


if __name__ == "__main__":
    main()
