"""Compare independent two-leg scenarios using full book depth."""
from mathutil import BPS, D, fixed, level_fill, settings

SCHEMA = {
    "size": ("Order size", "0.25", "0.000001", "100"),
    "minimum": ("Minimum net edge", "3", "0", "10000"),
    "age": ("Maximum quote age", "1500", "0", "60000"),
}


def levels(venue, side):
    return sorted(((D(price), D(size)) for price, size in venue[side]), reverse=side == "bids")


def compare(snapshot, buy, sell, config):
    route = f'{buy["name"]} → {sell["name"]}'
    bids, asks = levels(sell, "bids"), levels(buy, "asks")
    age = max(snapshot["as_of"] - buy["at"], snapshot["as_of"] - sell["at"])
    top_edge = (bids[0][0] / asks[0][0] - 1) * BPS
    prefix = [snapshot["label"], route, fixed(top_edge, 1), str(age)]
    if buy["at"] > snapshot["as_of"] or sell["at"] > snapshot["as_of"]:
        return prefix + ["—", "—", "Skip: future quote"], None
    if age > config["age"]:
        return prefix + ["—", "—", "Skip: stale quote"], None
    requested = config["size"]
    bought, gross_buy, _ = level_fill(asks, requested)
    sold, gross_sell, _ = level_fill(bids, requested)
    if min(bought, sold) < requested:
        reason = f"Skip: only {fixed(min(bought, sold), 6)} BTC available on both legs"
        return prefix + ["—", "—", reason], None
    spend = gross_buy * (1 + D(buy["fee_bps"]) / BPS)
    receive = gross_sell * (1 - D(sell["fee_bps"]) / BPS)
    net = receive - spend
    edge = net / spend * BPS
    decision = "Would simulate both legs" if edge >= config["minimum"] else "Skip: below minimum net edge"
    return prefix + [fixed(net), fixed(edge, 1), decision], edge


def run(fixture, params):
    config = settings(params, SCHEMA)
    rows = []
    evaluated_edges = []
    for snapshot in fixture["snapshots"]:
        first, second = snapshot["venues"]
        for buy, sell in ((first, second), (second, first)):
            row, edge = compare(snapshot, buy, sell, config)
            rows.append(row)
            if edge is not None:
                evaluated_edges.append(edge)
    eligible = sum(edge >= config["minimum"] for edge in evaluated_edges)
    best = fixed(max(evaluated_edges), 1) if evaluated_edges else "—"
    return {
        "metrics": [
            ["Eligible routes", f"{eligible} / {len(rows)}"],
            ["Best evaluated edge (bp)", best],
            ["Requested size (BTC)", fixed(config["size"], 6)],
        ],
        "columns": ["Snapshot", "Buy → sell", "Top edge (bp)", "Age (ms)", "Net P&L ($)", "Net edge (bp)", "Decision"],
        "rows": rows,
        "note": "Synthetic BTC/USD books. Fees: Cedar 6 bp, Flint 8 bp. Routes are independent estimates, not executions.",
    }
