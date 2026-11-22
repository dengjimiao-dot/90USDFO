"""Send the native silent CERA balance notice on the owning Game connection."""
import sqlite3
import struct
import time
from game.raid.runtime import RaidError


def pump_balance(server, session, client, *, now=None):
    stamp = time.monotonic() if now is None else now
    if stamp < getattr(session, 'cera_next_poll', 0):
        return
    session.cera_next_poll = stamp + 1.0
    directory = getattr(server, 'native_game_connections', None)
    try:
        owner = directory.chat_selection(session, sender=True) if directory else None
    except RaidError:
        owner = None
    if not owner:
        session.cera_sent_balance = None
        return
    try:
        amount = server._repo().get_account_cera(owner[2])
    except sqlite3.OperationalError:
        return
    # The native balance reader clamps a signed int32 below zero to zero.
    amount = min(0x7fffffff, max(0, int(amount)))
    key = (owner[2], owner[4], amount)
    if key == getattr(session, 'cera_sent_balance', None):
        return
    try:
        if directory.chat_selection(session, sender=True) != owner:
            return
    except RaidError:
        return
    client.sendall(server._codec_response(0, 0x35, struct.pack('<BI', 1, amount)))
    session.cera_sent_balance = key
