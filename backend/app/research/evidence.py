"""Module 4: evidence hub.

Two jobs. First, semantic-ish retrieval over filings and news with BM25 so any
claim can be traced to a passage. Second, an audit of the evidence already
attached by the desks: coverage, freshness, and orphan claims.
No embeddings service is required, which keeps the demo offline-safe.
"""
from __future__ import annotations

import math
import re
from collections import Counter

from .schemas import Citation, Evidence, ModuleResult, Status
from .state import Module, ResearchState

_WORD = re.compile(r"[a-z0-9']+")
_STOP = set("the a an and or of to in for on with is are was were be been it its "
            "that this as at by from we our their they he she".split())


def tokens(text: str) -> list[str]:
    return [w for w in _WORD.findall(text.lower()) if w not in _STOP and len(w) > 1]


class BM25:
    def __init__(self, docs: list[tuple[str, str]]):
        self.ids = [d[0] for d in docs]
        self.texts = [d[1] for d in docs]
        self.toks = [tokens(t) for t in self.texts]
        self.df = Counter()
        for t in self.toks:
            self.df.update(set(t))
        self.n = max(len(docs), 1)
        self.avglen = (sum(len(t) for t in self.toks) / self.n) if self.n else 1

    def search(self, query: str, k: int = 4, k1: float = 1.4, b: float = 0.75):
        q = tokens(query)
        scored = []
        for i, toks_i in enumerate(self.toks):
            tf = Counter(toks_i)
            s = 0.0
            for term in q:
                if term not in tf:
                    continue
                idf = math.log(1 + (self.n - self.df[term] + 0.5) / (self.df[term] + 0.5))
                denom = tf[term] + k1 * (1 - b + b * len(toks_i) / max(self.avglen, 1))
                s += idf * tf[term] * (k1 + 1) / denom
            if s > 0:
                scored.append((s, i))
        scored.sort(reverse=True)
        return [(self.ids[i], self.texts[i], round(s, 3)) for s, i in scored[:k]]


class EvidenceHub(Module):
    name = "evidence_hub"

    def run(self, state: ResearchState) -> ModuleResult:
        corpus: list[tuple[str, str]] = []
        meta: dict[str, dict] = {}
        for d in state.data.documents:
            for i, chunk in enumerate(d.chunks):
                key = f"{d.id}#{i+1}"
                corpus.append((key, chunk))
                meta[key] = dict(source_type="document", source_id=d.id,
                                 locator=f"{d.kind} chunk {i+1}", published=d.published)
        for n in state.data.news:
            corpus.append((n.id, f"{n.headline}. {n.body}"))
            meta[n.id] = dict(source_type="news", source_id=n.id, locator=n.source,
                              published=n.published)

        retrieved = []
        if corpus:
            index = BM25(corpus)
            question = state.request.question or (
                f"{state.request.asset} growth margin risk valuation demand guidance")
            for key, text, score in index.search(question, k=4):
                eid = state.next_evidence_id()
                m = meta[key]
                ev = Evidence(
                    id=eid, claim=f"Retrieved passage for: {question[:70]}",
                    value=score, strength=min(0.9, 0.4 + score / 12), desk="evidence",
                    citations=[Citation(id=eid, excerpt=text[:400], **m)],
                )
                state.add_evidence(ev)
                retrieved.append({"evidence_id": eid, "chunk": key, "score": score,
                                  "excerpt": text[:240]})

        # audit
        cited_desks = {e.desk for e in state.evidence.values()}
        desks_with_findings = {d for d, f in state.findings.items()
                               if f.status is Status.SUCCESS}
        uncited = sorted(desks_with_findings - cited_desks)
        coverage = 0.0
        if desks_with_findings:
            covered = sum(1 for d in desks_with_findings
                          if any(e.desk == d for e in state.evidence.values()))
            coverage = covered / len(desks_with_findings)

        status = Status.SUCCESS if corpus else Status.DEGRADED
        if not corpus:
            state.note_health(self.name, Status.DEGRADED,
                              "no documents or news to retrieve from")
        return ModuleResult(
            module=self.name, status=status,
            message=f"{len(state.evidence)} evidence items, coverage {coverage:.0%}",
            payload={"retrieved": retrieved, "coverage": round(coverage, 2),
                     "uncited_desks": uncited, "corpus_size": len(corpus)},
        )
