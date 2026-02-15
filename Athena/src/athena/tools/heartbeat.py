"""
athena.tools.heartbeat
======================

Read-Only File Watcher — Auto-indexes new/modified documents to Supabase.

Design constraints:
    - READ-ONLY: Only reads source files, writes to Supabase + log
    - Never modifies source files
    - Debounces rapid edits (5s window)
    - Watches all CORE_DIRS and EXTENDED_DIRS from config.py

Usage:
    python3 -m athena heartbeat              # Run as foreground daemon
    python3 -m athena heartbeat --dry-run    # Test mode (log only, no sync)
    python3 -m athena heartbeat --once       # Single scan then exit

Dependencies:
    pip install watchdog
"""

import logging
import sys
import threading
import time
from pathlib import Path
from typing import Dict, Optional

try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer
except ImportError:
    Observer = None
    FileSystemEventHandler = object
    print("⚠️ watchdog not installed. Run: pip install watchdog", file=sys.stderr)

from athena.core.config import (
    PROJECT_ROOT,
    CORE_DIRS,
    EXTENDED_DIRS,
)

# ── Logging ───────────────────────────────────────────────────────────────────

LOG_DIR = PROJECT_ROOT / ".athena"
LOG_FILE = LOG_DIR / "heartbeat.log"

logger = logging.getLogger("athena.heartbeat")


def setup_logging():
    """Configure file + stderr logging."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    )
    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    logger.setLevel(logging.INFO)


# ── Table Routing ─────────────────────────────────────────────────────────────


def resolve_table(file_path: Path) -> Optional[str]:
    """
    Determine which Supabase table a file should sync to.
    Returns None if the file is not in a watched directory.
    """
    str_path = str(file_path.resolve())

    # Check CORE_DIRS first (more specific)
    for table_name, dir_path in CORE_DIRS.items():
        if str_path.startswith(str(dir_path.resolve())):
            return table_name

    # Check EXTENDED_DIRS
    for dir_path, table_name in EXTENDED_DIRS:
        if str_path.startswith(str(dir_path.resolve())):
            return table_name

    return None


# ── Debounced Sync Handler ────────────────────────────────────────────────────


class DebouncedSyncHandler(FileSystemEventHandler if Observer else object):
    """
    File event handler with debouncing.
    Batches rapid edits into a single sync operation per file.
    """

    DEBOUNCE_SECONDS = 5.0

    def __init__(self, dry_run: bool = False):
        super().__init__()
        self.dry_run = dry_run
        self._pending: Dict[str, threading.Timer] = {}
        self._lock = threading.Lock()
        self._stats = {"synced": 0, "skipped": 0, "errors": 0}

    def on_modified(self, event):
        if event.is_directory:
            return
        self._schedule_sync(event.src_path)

    def on_created(self, event):
        if event.is_directory:
            return
        self._schedule_sync(event.src_path)

    def _schedule_sync(self, path: str):
        """Schedule a debounced sync for the given file."""
        file_path = Path(path)

        # Only process markdown files
        if file_path.suffix.lower() != ".md":
            return

        # Skip hidden files and temp files
        if file_path.name.startswith(".") or file_path.name.startswith("~"):
            return

        with self._lock:
            # Cancel any pending timer for this file
            if path in self._pending:
                self._pending[path].cancel()

            # Schedule new sync after debounce period
            timer = threading.Timer(
                self.DEBOUNCE_SECONDS,
                self._do_sync,
                args=(file_path,),
            )
            timer.daemon = True
            timer.start()
            self._pending[path] = timer

    def _do_sync(self, file_path: Path):
        """Execute the actual sync operation."""
        table = resolve_table(file_path)
        if not table:
            logger.debug(f"⏩ Ignored (no table mapping): {file_path.name}")
            self._stats["skipped"] += 1
            return

        if self.dry_run:
            logger.info(f"🔍 [DRY RUN] Would sync: {file_path.name} → {table}")
            return

        try:
            from athena.memory.sync import sync_file_to_supabase

            logger.info(f"📡 Syncing: {file_path.name} → {table}")
            sync_file_to_supabase(file_path, table)
            self._stats["synced"] += 1
            logger.info(f"✅ Synced: {file_path.name}")

        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"❌ Sync failed for {file_path.name}: {e}")

        # Cleanup pending reference
        with self._lock:
            self._pending.pop(str(file_path), None)

    @property
    def stats(self):
        return dict(self._stats)


# ── Heartbeat Daemon ──────────────────────────────────────────────────────────


class Heartbeat:
    """
    File watcher daemon that auto-indexes documents.

    Args:
        dry_run: If True, log what would be synced without actually syncing
    """

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.watch_dirs: list[Path] = []
        self.handler = DebouncedSyncHandler(dry_run=dry_run)
        self.observer = None

        # Collect all watch directories
        for dir_path in CORE_DIRS.values():
            if dir_path.exists():
                self.watch_dirs.append(dir_path)

        for dir_path, _ in EXTENDED_DIRS:
            if dir_path.exists() and dir_path not in self.watch_dirs:
                self.watch_dirs.append(dir_path)

    def start(self):
        """Start the file watcher daemon."""
        if Observer is None:
            print("❌ Cannot start heartbeat: watchdog not installed", file=sys.stderr)
            print("   Install with: pip install watchdog", file=sys.stderr)
            return False

        setup_logging()
        self.observer = Observer()

        logger.info("💓 Athena Heartbeat starting...")
        logger.info(f"   📂 Watching {len(self.watch_dirs)} directories")
        logger.info(f"   🔄 Debounce: {DebouncedSyncHandler.DEBOUNCE_SECONDS}s")
        logger.info(f"   {'🔍 DRY RUN MODE' if self.dry_run else '📡 LIVE SYNC MODE'}")

        for dir_path in self.watch_dirs:
            self.observer.schedule(self.handler, str(dir_path), recursive=True)
            logger.info(f"   👁️  {dir_path.relative_to(PROJECT_ROOT)}")

        self.observer.start()
        logger.info("💓 Heartbeat active. Press Ctrl+C to stop.")
        return True

    def stop(self):
        """Stop the file watcher."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            stats = self.handler.stats
            logger.info(
                f"💓 Heartbeat stopped. "
                f"Synced: {stats['synced']}, "
                f"Skipped: {stats['skipped']}, "
                f"Errors: {stats['errors']}"
            )

    def run_forever(self):
        """Run until interrupted."""
        if not self.start():
            return

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("\n⛔ Shutdown signal received.")
        finally:
            self.stop()

    def scan_once(self):
        """Single scan: find all unsynced files and sync them."""
        setup_logging()
        logger.info("🔍 Running single-pass scan...")

        from athena.memory.sync import sync_file_to_supabase, load_manifest, get_file_hash

        manifest = load_manifest()
        synced = 0
        skipped = 0

        for dir_path in self.watch_dirs:
            table = None
            # Resolve table for this directory
            for tname, tpath in CORE_DIRS.items():
                if dir_path == tpath:
                    table = tname
                    break
            if not table:
                for tpath, tname in EXTENDED_DIRS:
                    if dir_path == tpath:
                        table = tname
                        break

            if not table:
                continue

            for md_file in dir_path.rglob("*.md"):
                rel = str(md_file.relative_to(PROJECT_ROOT))
                content = md_file.read_text(encoding="utf-8", errors="replace")
                current_hash = get_file_hash(content)

                if manifest.get(rel) == current_hash:
                    skipped += 1
                    continue

                if self.dry_run:
                    logger.info(f"🔍 [DRY RUN] Would sync: {md_file.name} → {table}")
                else:
                    try:
                        sync_file_to_supabase(
                            md_file, table, manifest=manifest, save_on_success=False
                        )
                        synced += 1
                    except Exception as e:
                        logger.error(f"❌ {md_file.name}: {e}")

        logger.info(f"✅ Scan complete. Synced: {synced}, Skipped (unchanged): {skipped}")


# ── CLI Entry Point ───────────────────────────────────────────────────────────


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Athena Heartbeat — Auto-Indexing Daemon")
    parser.add_argument("--dry-run", action="store_true", help="Log only, don't sync")
    parser.add_argument("--once", action="store_true", help="Single scan then exit")
    args = parser.parse_args()

    hb = Heartbeat(dry_run=args.dry_run)

    if args.once:
        hb.scan_once()
    else:
        hb.run_forever()


if __name__ == "__main__":
    main()
