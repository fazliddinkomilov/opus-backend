from .services import expire_master_offer, expire_stale_master_offers, match_open_orders


def expire_offer(offer_id: int) -> bool:
    return expire_master_offer(offer_id, continue_matching=True)


def sweep_offer_expirations(limit: int = 20) -> dict[str, int]:
    expired_count = expire_stale_master_offers(continue_matching=True)
    matched_count = match_open_orders(limit=limit)
    return {"expired_count": expired_count, "matched_count": matched_count}
