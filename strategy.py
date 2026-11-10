"""GC cash-settlement gap fade: overnight displacement from prior 15:00 CT cash close
mean-reverts after Comex liquidity arrives. Each day's gap uses only prior completed session."""
import numpy as np

FAMILY = "metals-cash-gap-reversion"
PARAMS = {"gap_dollars": 8.0, "entry_ct_sec": 30600, "exit_ct_sec": 37800, "stop_dollars": 250}
BASKET = ("GC",)

def entry_risk(panel):
    return {s: np.full(len(df), PARAMS["stop_dollars"], dtype=float) for s, df in panel.items()}

def signals(panel):
    targets = {}
    for symbol, df in panel.items():
        out = np.zeros(len(df), dtype=np.int64)
        if symbol in BASKET:
            session = df.session.astype(str).to_numpy()
            sec = df.ct_sec.to_numpy()
            close = df.close.to_numpy()
            prior_cash = {}
            for day in np.unique(session):
                idx = np.flatnonzero(session == day)
                past = idx[sec[idx] < PARAMS["entry_ct_sec"]]
                if len(past):
                    prev = past[-1]
                    # cash reference is final completed 15:00 CT bar from preceding session.
                    old = np.flatnonzero(sec[:idx[0]] < PARAMS["exit_ct_sec"])
                    if len(old):
                        prior_cash[day] = close[old[-1]]
            for day, ref in prior_cash.items():
                idx = np.flatnonzero((session == day) & (sec >= PARAMS["entry_ct_sec"]) & (sec < PARAMS["exit_ct_sec"]))
                if len(idx):
                    gap = close[idx[0]] - ref
                    if abs(gap) >= PARAMS["gap_dollars"]:
                        out[idx] = -int(np.sign(gap))
        targets[symbol] = out
    return targets
