"""Module 2: pulls every feed, validates it, and records what is missing."""
from __future__ import annotations

from .schemas import DataBundle, ModuleResult, Status
from .state import Module, ResearchState
from .data_adapters import (
    DocumentAdapter, FeedError, FundamentalAdapter, MarketAdapter, NewsAdapter,
)


class DataOrchestrator(Module):
    name = "data_orchestrator"
    critical = True

    def __init__(self) -> None:
        self.market = MarketAdapter()
        self.fundamental = FundamentalAdapter()
        self.news = NewsAdapter()
        self.documents = DocumentAdapter()

    def run(self, state: ResearchState) -> ModuleResult:
        asset = state.request.asset.upper()
        kill = {k.lower() for k in state.request.kill_feeds}
        bundle = DataBundle()
        missing: list[str] = []

        for feed, adapter in (("market", self.market), ("fundamentals", self.fundamental),
                              ("news", self.news), ("documents", self.documents)):
            if feed in kill:
                missing.append(feed)
                state.note_health(f"feed:{feed}", Status.FAILED, "feed unavailable")
                continue
            try:
                value = adapter.fetch(asset)
                setattr(bundle, feed, value)
                state.note_health(f"feed:{feed}", Status.SUCCESS,
                                  f"{adapter.name} delivered")
            except FeedError as exc:
                missing.append(feed)
                state.note_health(f"feed:{feed}", Status.FAILED, str(exc))

        # validation: a market series that is too short is worse than useless
        if bundle.market and len(bundle.market.candles) < 60:
            missing.append("market")
            bundle.market = None
            state.note_health("feed:market", Status.DEGRADED, "series too short to analyse")

        state.data = bundle
        if "market" in missing and "fundamentals" in missing:
            return ModuleResult(module=self.name, status=Status.FAILED,
                                message="no market and no fundamental data: cannot research",
                                payload={"missing": missing})
        status = Status.DEGRADED if missing else Status.SUCCESS
        return ModuleResult(
            module=self.name, status=status,
            message="all feeds live" if not missing else f"missing: {', '.join(missing)}",
            payload={"missing": missing,
                     "candles": len(bundle.market.candles) if bundle.market else 0,
                     "news": len(bundle.news), "documents": len(bundle.documents)},
        )
