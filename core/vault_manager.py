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

    def add_item(self, title: str, content: str, lane: str = "snippets",
                 tags: Optional[List[str]] = None, item_type: str = "snippet") -> str:
        """Add a new item to a lane.

        Args:
            title: Display name for the item
            content: The actual content/value
            lane: Which lane to add to (prompts, api_keys, passwords, notes, snippets, other)
            tags: Optional list of tags
            item_type: Type of item (prompt, api_key, password, note, snippet)

        Returns:
            The ID of the newly created item
        """
        # Map common lane names to zone IDs
        zone_mapping = {
            "prompts": "zone1",
            "api_keys": "zone2",
            "passwords": "zone3",
            "notes": "zone4",
            "snippets": "zone5",
            "other": "zone6"
        }

        zone_id = zone_mapping.get(lane.lower(), "zone5")
        zone = self.zones.get(zone_id)
        if not zone:
            return ""

        # Generate unique ID
        item_id = title.lower().replace(" ", "_")
        existing_ids = {item.id for z in self.zones.values() for item in z.items}
        counter = 1
        original_id = item_id
        while item_id in existing_ids:
            item_id = f"{original_id}_{counter}"
            counter += 1

        new_item = VaultItem(
            id=item_id,
            label=title,
            type=item_type,
            value=content,
            pinned=False,
            hotkey="",
            hotstring=""
        )
        zone.items.append(new_item)
        self.save()
        return item_id

    def delete_item(self, item_id: str) -> bool:
        """Delete an item from the vault.

        Args:
            item_id: ID of the item to delete

        Returns:
            True if item was found and deleted, False otherwise
        """
        for zone in self.zones.values():
            for i, item in enumerate(zone.items):
                if item.id == item_id:
                    zone.items.pop(i)
                    self.save()
                    return True
        return False

    def update_item(self, item_id: str, **kwargs) -> bool:
        """Update an existing item.

        Args:
            item_id: ID of the item to update
            **kwargs: Fields to update (label, value, type, pinned, hotkey, hotstring)

        Returns:
            True if item was found and updated, False otherwise
        """
        item = self.find_item(item_id)
        if not item:
            return False

        for key, value in kwargs.items():
            if hasattr(item, key):
                setattr(item, key, value)

        self.save()
        return True
