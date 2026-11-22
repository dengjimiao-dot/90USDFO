"""C1/022E normal account cargo transport for the Seria prize stone."""
from functools import lru_cache
import re
import struct

from game.character.inventory_item_view import InventoryItemView
from game.character.item_metadata import resolve_item_metadata
from game.character.payloads import build_account_cargo_item_list, build_item_list_mode0
from game.town_cera_rooms import get_cera_room_for_town
from pvf import pvf_runtime


OPCODE = 0x022E
REQUEST = struct.Struct("<HHBI")
ACK = struct.Struct("<BHHHHB")
STONE_ACTION = "[cargo transport stone]"
RULE_ID = 4028
ITEM_FIELDS = (
    "item_template_id", "item_kind", "stack_count", "instance_value", "durability",
    "seal_flag", "option_value", "expire_time", "marker_16", "extra_json",
)


@lru_cache(maxsize=1)
def _stone_rule():
    text = pvf_runtime.read_text("etc/cargotransportstone.etc")
    blocks = re.findall(r"(?ms)^\[stone type\]\s*\n(.*?)^\[/stone type\]", text)
    block = next((block for block in blocks if block.split()[0] == str(RULE_ID)), "")
    fields = {
        name: tuple(value.replace("`", "").splitlines())
        for name, value in re.findall(r"(?ms)^\[([^/\]\n]+)\]\s*\n(.*?)^\[/\1\]", block)
    }
    # The prize's normal mode has no additional costs or item-ID overrides.
    if set(fields) != {
        "cargo transport stone grade", "cargo transport stone rarity weight",
        "cargo transport stone enable equip type", "cargo transport stone except index",
        "cargo transport stone include index", "cargo transport stone except etc", "ui index",
    } or fields["cargo transport stone except index"] or fields["cargo transport stone include index"]:
        raise ValueError("unexpected cargo transport rule fields")
    if fields["cargo transport stone except etc"] != ("growthType", "periodEquipment"):
        raise ValueError("unexpected cargo transport exceptions")
    grades = tuple(map(int, fields["cargo transport stone grade"]))
    bands = tuple(zip(grades[::3], grades[1::3], grades[2::3]))
    if len(grades) != len(bands) * 3 or any(cost != 1 for _, _, cost in bands):
        raise ValueError("unsupported cargo transport grade cost")
    rarity, weight = map(int, fields["cargo transport stone rarity weight"])
    if weight != 1:
        raise ValueError("unsupported cargo transport rarity weight")
    return bands, rarity, frozenset(fields["cargo transport stone enable equip type"])


def _eligible_equipment(row):
    meta = resolve_item_metadata(row["item_template_id"])
    bands, rarity, equip_types = _stone_rule()
    if (not meta.is_equipment or meta.is_avatar or meta.rarity != rarity
            or f"[{meta.equipment_type.strip('[]')}]" not in equip_types
            or not any(low <= meta.grade <= high for low, high, _ in bands)
            or row["item_kind"] != "equipment" or row["stack_count"] != 1
            or row["equipment_lock_id"] or row["sort_lock_flag"] or row["pet_serial_or_handle"]
            or row["expire_time"] or meta.usable_period_days or meta.expiration_timestamp
            or meta.daily_delete):
        return False
    # Refuse growth templates that carry progression outside the cargo item row.
    script = pvf_runtime.read_text(meta.source_path).lower()
    return bool(script) and not re.search(
        r"(?m)^\[(?:grow(?:th)?(?: type| equipment| level)?|growtype|growthtype)\]", script
    )


def handle_cargo_transport(server, body, session):
    def reject(reason, code=0x07):
        return [server._codec_response(1, OPCODE, bytes((0, code)))], f"cargo_transport reject={reason}"

    if len(body) < REQUEST.size or any(body[REQUEST.size:]):
        return reject("layout")
    stone_slot, equip_slot, mode, key = REQUEST.unpack_from(body)
    if mode != 0 or not stone_slot or not equip_slot or stone_slot == equip_slot:
        return reject("mode_or_slots")
    cid = getattr(session, "selected_character_id", None)
    aid = getattr(session, "account_id", None)
    town = getattr(session, "cur_town_id", None)
    if (not cid or not aid or town is None or not getattr(session, "enter_seria_settled", False)
            or getattr(session, "enter_seria_in_progress", False)
            or getattr(session, "in_dungeon_select", False) or getattr(session, "in_dungeon_run", False)):
        return reject("session")
    room = get_cera_room_for_town(town)
    if room.source != "pvf-gate" or getattr(session, "cur_area_id", None) != room.area_id:
        return reject("seria_room")

    repo = server._repo()
    with repo.inventory_transaction_scope() as conn:
        character = conn.execute(
            "SELECT level FROM characters WHERE character_id=? AND account_id=? AND delete_flag=0",
            (cid, aid),
        ).fetchone()
        cargo = conn.execute(
            "SELECT selection_key,value32 FROM account_cargo_state WHERE account_id=?", (aid,),
        ).fetchone()
        if (character is None or not repo.character_can_open_account_cargo(character[0])
                or cargo is None or not 0 < key <= 0xFFFF or cargo[0] != key):
            return reject("cargo_state")

        rows = {row["slot_index"]: row for row in conn.execute(
            "SELECT * FROM character_items WHERE character_id=? AND list_type=0 AND slot_index IN (?,?)",
            (cid, stone_slot, equip_slot),
        )}
        stone, equipment = rows.get(stone_slot), rows.get(equip_slot)
        if stone is None or equipment is None:
            return reject("empty_slot")
        meta = resolve_item_metadata(stone["item_template_id"])
        remaining = int(stone["stack_count"] or 0) - 1
        if (meta.action_type != STONE_ACTION or meta.action_values != (RULE_ID,)
                or not meta.is_stackable or stone["item_kind"] != "stackable"
                or stone["expire_time"] or stone["sort_lock_flag"] or stone["equipment_lock_id"]
                or not 0 <= remaining <= 0xFFFF or character[0] < meta.minimum_level):
            return reject("stone")
        try:
            eligible = _eligible_equipment(equipment)
        except (KeyError, ValueError):
            return reject("rule")
        if not eligible:
            return reject("equipment")

        cargo_rows = conn.execute(
            "SELECT * FROM account_cargo_items WHERE account_id=? ORDER BY slot_index", (aid,),
        ).fetchall()
        occupied = {row["slot_index"] for row in cargo_rows}
        dest = next((slot for slot in range(key) if slot not in occupied), None)
        if dest is None:
            return reject("full", 0x04)

        item = {name: equipment[name] for name in ITEM_FIELDS}
        repo._insert_account_cargo_item_tx(conn, aid, dest, **item)
        conn.execute("DELETE FROM character_items WHERE item_uid=?", (equipment["item_uid"],))
        if remaining:
            conn.execute(
                "UPDATE character_items SET stack_count=?,instance_value=?,updated_at=CURRENT_TIMESTAMP "
                "WHERE item_uid=?", (remaining, remaining, stone["item_uid"]),
            )
        else:
            conn.execute("DELETE FROM character_items WHERE item_uid=?", (stone["item_uid"],))
        repo._refresh_account_cargo_item_count_tx(conn, aid)
        bag, capacity = repo.load_main_inventory_snapshot(cid)
        cargo_items = [InventoryItemView(dict(row)) for row in cargo_rows]
        cargo_items.append(InventoryItemView(dict(item, slot_index=dest)))
        cargo_items.sort(key=lambda row: row.slot_index)
        packets = [
            server._codec_response(1, OPCODE, ACK.pack(1, stone_slot, equip_slot, remaining, dest, mode)),
            server._codec_response(0, 0x000D, build_item_list_mode0(
                [InventoryItemView(row) for row in bag], list_param16=capacity,
            )),
            server._codec_response(0, 0x000D, build_account_cargo_item_list(
                cargo_items, selection_key=key, cargo_gold=cargo[1],
            )),
        ]
    return packets, f"cargo_transport ok cid={cid} stone={meta.item_id} equip={item['item_template_id']} dst={dest}"
