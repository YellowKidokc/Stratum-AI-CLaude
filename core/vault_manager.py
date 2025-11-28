from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
import json


@dataclass
class VaultItem:
    id: str
    label: str
    type: str          # "prompt", "api_key", "note", "snippet", ...
    value: str
    pinned: bool = False
    hotkey: str = ""
    hotstring: str = ""


@dataclass
class VaultZone:
    id: str
    name: str
    items: List[VaultItem]


class VaultManager:
    def __init__(self, vault_path: Path) -> None:
        self._path = Path(vault_path)
        self.zones: Dict[str, VaultZone] = {}

    def load(self) -> None:
        if not self._path.exists():
            self._create_default()

        raw = self._path.read_text(encoding="utf-8").strip() or '{"zones": []}'
        data = json.loads(raw)
        self.zones.clear()

        for z in data.get("zones", []):
            items = [
                VaultItem(
                    id=i["id"],
                    label=i.get("label", i["id"]),
                    type=i.get("type", "note"),
                    value=i.get("value", ""),
                    pinned=i.get("pinned", False),
                    hotkey=i.get("hotkey", ""),
                    hotstring=i.get("hotstring", ""),
                )
                for i in z.get("items", [])
            ]
            zone = VaultZone(
                id=z["id"],
                name=z.get("name", z["id"]),
                items=items,
            )
            self.zones[zone.id] = zone

    def _create_default(self) -> None:
        data = {
            "zones": [
                {"id": f"zone{i}", "name": name, "items": []}
                for i, name in enumerate(
                    ["Prompts", "API Keys", "Passwords", "Notes", "Snippets", "Other"],
                    start=1,
                )
            ]
        }
        self._path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def save(self) -> None:
        data = {
            "zones": []

        }
        for zone in self.zones.values():
            data["zones"].append({
                "id": zone.id,
                "name": zone.name,
                "items": [i.__dict__ for i in zone.items],
            })
        self._path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def get_lane_items(self, lane: str, include_pinned: bool = True) -> List[VaultItem]:
        """Get all items in a specific lane."""
        # Map common lane names to zone IDs
        zone_mapping = {
            "prompts": "zone1",
            "api_keys": "zone2",
            "passwords": "zone3",
            "notes": "zone4",
            "snippets": "zone5",
            "other": "zone6"
        }

        zone_id = zone_mapping.get(lane, lane)
        zone = self.zones.get(zone_id)
        if not zone:
            return []

        items = zone.items
        if include_pinned:
            # Sort pinned items first, then by label
            items.sort(key=lambda x: (not x.pinned, x.label.lower()))
        return items

    def find_item(self, item_id: str) -> Optional[VaultItem]:
        for zone in self.zones.values():
            for item in zone.items:
                if item.id == item_id:
                    return item
        return None
