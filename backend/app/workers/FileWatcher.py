import asyncio
import json
import re
from pathlib import Path

import asyncpg

from app.config import get_settings


class FileWatcher:
    def __init__(self, conn: asyncpg.Connection) -> None:
        self.conn = conn
        self.root = Path(get_settings().fileWatcherRoot)
        self.processed = self.root / "processed"
        self.processed.mkdir(parents=True, exist_ok=True)

    async def scanAndWatch(self) -> None:
        await self._scan()
        await self._watch()

    async def _scan(self) -> None:
        for file in self.root.glob("*.json"):
            await self._processFile(file)
        for file in self.processed.glob("*.json"):
            await self._processFile(file)

    async def _watch(self) -> None:
        seen = set(self.root.glob("*.json"))
        while True:
            await asyncio.sleep(2)
            current = set(self.root.glob("*.json"))
            new = current - seen
            for file in new:
                await self._processFile(file)
            seen = current

    async def _processFile(self, file: Path) -> None:
        context = self._parseFilename(file.name)
        if context is None:
            print(f"✗ Skipping {file.name} — filename must be entry_type__source__created_by.json")
            return
        try:
            entries = json.loads(file.read_text())
            if not isinstance(entries, list):
                print(f"✗ Skipping {file.name} — must be a JSON list")
                return
            await self._insertEntries(entries, context)
            file.rename(self.processed / file.name)
            print(f"✓ Processed {file.name} — {len(entries)} entries")
        except Exception as e:
            print(f"✗ Failed {file.name} — {e}")

    def _parseFilename(self, filename: str) -> dict | None:
        pattern = r"^(?P<entry_type>[^_]+)__(?P<source>[^_]+)__(?P<created_by>[^_]+)\.json$"
        match = re.match(pattern, filename)
        if not match:
            return None
        return match.groupdict()

    async def _insertEntries(self, entries: list[dict], context: dict) -> None:
        async with self.conn.transaction():
            for entry in entries:
                metadata = self._cleanMetadata(entry)
                await self.conn.execute("""
                    INSERT INTO entries (entry_type, source, created_by, metadata, metadata_sources)
                    VALUES ($1, $2, $3, $4, $5)
                """,
                    context["entry_type"],
                    context["source"],
                    context["created_by"],
                    json.dumps(metadata),
                    json.dumps({k: context["source"] for k in metadata})
                )
                await self._registerFields(context["entry_type"], context["source"], metadata)

    def _cleanMetadata(self, entry: dict) -> dict:
        drop = {"uuid", "created_at", "updated_at", "last_edited_at", "entity_id"}
        return {k: v for k, v in entry.items() if k not in drop}

    async def _registerFields(self, entryType: str, source: str, metadata: dict) -> None:
        for key, value in metadata.items():
            valueType = type(value).__name__
            await self.conn.execute("""
                INSERT INTO field_registry (entry_type, key, value_type, source)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT DO NOTHING
            """, entryType, key, valueType, source)