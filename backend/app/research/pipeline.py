"""The organisation. Modules run in order, each reading and writing ResearchState.

USER -> intake -> data -> desks -> evidence -> consensus -> critic -> thesis
     -> risk/uncertainty/confidence -> investor -> portfolio -> personalization
     -> action impact -> scenarios -> decision -> boundaries -> watch
     -> evolution -> memory -> performance -> degradation -> report
"""
from __future__ import annotations

from .schemas import ModuleResult, ResearchRequest, Status
from .state import Module, ResearchState
from .data_orchestrator import DataOrchestrator
from .decision import (
    BoundaryEngine, DecisionEngine, EvolutionEngine, ScenarioEngine, WatchEngine,
)
from .investor import (
    ActionImpactEngine, InvestorModule, PersonalizationEngine, PortfolioEngine,
)
from .consensus import ConsensusEngine, CriticEngine
from .evidence import EvidenceHub
from .thesis import (
    ConfidenceEngine, RiskEngine, ThesisEngine, UncertaintyEngine,
)
from .desks import ResearchHub
from .system import DegradationEngine, MemoryEngine, PerformanceEngine


class Intake(Module):
    name = "research_intake"
    critical = True

    def run(self, state: ResearchState) -> ModuleResult:
        asset = state.request.asset.strip().upper()
        if not asset or not asset.replace(".", "").replace("-", "").isalnum():
            return ModuleResult(module=self.name, status=Status.FAILED,
                                message=f"'{state.request.asset}' is not a usable ticker")
        state.request.asset = asset
        state.request.horizon_days = max(5, min(730, state.request.horizon_days))
        return ModuleResult(module=self.name, status=Status.SUCCESS,
                            message=f"researching {asset} over {state.request.horizon_days} days "
                                    f"for {state.request.investor_id}")


PIPELINE: list[Module] = [
    Intake(),
    DataOrchestrator(),
    ResearchHub(),
    EvidenceHub(),
    ConsensusEngine(),
    CriticEngine(),
    ThesisEngine(),
    RiskEngine(),
    UncertaintyEngine(),
    ConfidenceEngine(),
    InvestorModule(),
    PortfolioEngine(),
    PersonalizationEngine(),
    ActionImpactEngine(),
    ScenarioEngine(),
    DecisionEngine(),
    BoundaryEngine(),
    WatchEngine(),
    EvolutionEngine(),
    MemoryEngine(),
    PerformanceEngine(),
    DegradationEngine(),
]


def run_research(request: ResearchRequest) -> ResearchState:
    state = ResearchState(request=request)
    for module in PIPELINE:
        result = module(state)
        if result.status is Status.FAILED and module.critical:
            state.note_health("pipeline", Status.FAILED,
                              f"stopped at {module.name}: {result.message}")
            break
    return state
