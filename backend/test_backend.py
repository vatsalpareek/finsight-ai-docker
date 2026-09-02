import asyncio
from app.storage.database import DB
from app.agents.orchestrator import AgentOrchestrator

async def test_backend():
    print("Testing FinSight AI Backend Orchestrator...")
    profile = DB.get_profile("conservative")
    session, metric = await AgentOrchestrator.run_pipeline("RELIANCE", profile, simulate_data_failure=False)
    
    print(f"Session ID: {session.session_id}")
    print(f"Stock: {session.symbol}")
    print(f"Overall Signal: {session.synthesis.overall_signal} ({session.synthesis.overall_confidence}%)")
    print(f"Personalized Interpretation:\n{session.synthesis.personalized_interpretation}\n")
    print("Agent Latencies (ms):", metric.agent_latencies)
    print("Total Latency (ms):", metric.total_latency_ms)
    print("Citations Count:", len(session.synthesis.citations))
    if session.synthesis.citations:
        print("First Citation Title:", session.synthesis.citations[0].title)

if __name__ == "__main__":
    asyncio.run(test_backend())
