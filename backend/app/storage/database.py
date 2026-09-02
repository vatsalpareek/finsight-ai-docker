import os
from typing import List
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session
from dotenv import load_dotenv

from app.models.schemas import UserProfile, PortfolioHolding, RiskTolerance, InvestmentHorizon, AnalysisSession, PerformanceMetric
from app.storage.models import Base, DBUser, DBPortfolioHolding, DBSessionAnalysis, DBPerformanceMetric

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./finsight.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

class DB:
    @staticmethod
    def get_session() -> Session:
        return SessionLocal()

    @staticmethod
    def initialize_demo_profiles():
        db = DB.get_session()
        try:
            # Check if conservative profile exists
            if not db.query(DBUser).filter_by(user_id="conservative").first():
                cons = DBUser(
                    user_id="conservative",
                    name="Arjun Sharma",
                    risk_tolerance=RiskTolerance.CONSERVATIVE.value,
                    investment_horizon=InvestmentHorizon.LONG_TERM.value,
                    total_portfolio_value=1240000.0,
                    risk_score=42,
                    watchlist=["RELIANCE", "TCS", "INFY", "HDFCBANK", "SBIN"],
                    previous_decisions_count=14
                )
                db.add(cons)
                db.commit()

            if not db.query(DBUser).filter_by(user_id="aggressive").first():
                agg = DBUser(
                    user_id="aggressive",
                    name="Priya Patel",
                    risk_tolerance=RiskTolerance.AGGRESSIVE.value,
                    investment_horizon=InvestmentHorizon.SHORT_TERM.value,
                    total_portfolio_value=1850000.0,
                    risk_score=78,
                    watchlist=["RELIANCE", "TCS", "INFY", "SBIN"],
                    previous_decisions_count=29
                )
                db.add(agg)
                db.commit()
                
            # Note: For prototype simplicity, we assume holdings are populated or we could populate them here.
            # Real application would let user add/remove holdings.
        finally:
            db.close()

    @staticmethod
    def get_profile(profile_id: str) -> UserProfile:
        db = DB.get_session()
        try:
            db_user = db.query(DBUser).filter_by(user_id=profile_id.lower()).first()
            if not db_user:
                # Fallback to in-memory defaults if not found
                return DB._get_fallback_profile(profile_id)
            
            holdings = []
            for h in db_user.holdings:
                holdings.append(PortfolioHolding(
                    symbol=h.symbol,
                    company_name=h.company_name,
                    shares=h.shares,
                    avg_cost=h.avg_cost,
                    current_price=h.current_price,
                    value=h.value,
                    sector=h.sector,
                    allocation_pct=h.allocation_pct,
                    profit_loss=h.profit_loss,
                    profit_loss_pct=h.profit_loss_pct
                ))

            return UserProfile(
                user_id=db_user.user_id,
                name=db_user.name,
                risk_tolerance=RiskTolerance(db_user.risk_tolerance),
                investment_horizon=InvestmentHorizon(db_user.investment_horizon),
                total_portfolio_value=db_user.total_portfolio_value,
                risk_score=db_user.risk_score,
                watchlist=db_user.watchlist,
                previous_decisions_count=db_user.previous_decisions_count,
                portfolio_holdings=holdings
            )
        finally:
            db.close()

    @staticmethod
    def _get_fallback_profile(profile_id: str) -> UserProfile:
        # Just return basic if completely missing
        return UserProfile(
            user_id=profile_id,
            name="Fallback Profile",
            risk_tolerance=RiskTolerance.MODERATE,
            investment_horizon=InvestmentHorizon.MEDIUM_TERM,
            total_portfolio_value=100000.0,
            risk_score=50,
            watchlist=[],
            portfolio_holdings=[]
        )

    @staticmethod
    def save_session(session: AnalysisSession, metric: PerformanceMetric):
        db = DB.get_session()
        try:
            db_session = DBSessionAnalysis(
                session_id=session.session_id,
                timestamp=session.timestamp,
                symbol=session.symbol,
                profile_id=session.user_profile.user_id,
                technical_signal=session.technical_output.signal if session.technical_output else None,
                fundamental_signal=session.fundamental_output.signal if session.fundamental_output else None,
                sentiment_signal=session.sentiment_output.signal if session.sentiment_output else None,
                overall_signal=session.synthesis.overall_signal,
                is_degraded=session.is_degraded,
                full_payload=session.model_dump(mode="json")
            )
            db.add(db_session)
            
            db_metric = DBPerformanceMetric(
                session_id=metric.session_id,
                timestamp=metric.timestamp,
                symbol=metric.symbol,
                total_latency_ms=metric.total_latency_ms,
                agent_latencies=metric.agent_latencies,
                signal_accuracy_pct=metric.signal_accuracy_pct,
                portfolio_risk_concentration_score=metric.portfolio_risk_concentration_score
            )
            db.add(db_metric)
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"Failed to save session to DB: {e}")
        finally:
            db.close()

    @staticmethod
    def get_sessions(limit: int = 20) -> List[AnalysisSession]:
        db = DB.get_session()
        try:
            records = db.query(DBSessionAnalysis).order_by(DBSessionAnalysis.timestamp.desc()).limit(limit).all()
            sessions = []
            for r in records:
                try:
                    sessions.append(AnalysisSession(**r.full_payload))
                except Exception:
                    pass
            return sessions
        finally:
            db.close()

    @staticmethod
    def get_metrics(limit: int = 20) -> List[PerformanceMetric]:
        db = DB.get_session()
        try:
            records = db.query(DBPerformanceMetric).order_by(DBPerformanceMetric.timestamp.desc()).limit(limit).all()
            metrics = []
            for r in records:
                metrics.append(PerformanceMetric(
                    session_id=r.session_id,
                    timestamp=r.timestamp,
                    symbol=r.symbol,
                    total_latency_ms=r.total_latency_ms,
                    agent_latencies=r.agent_latencies,
                    signal_accuracy_pct=r.signal_accuracy_pct,
                    portfolio_risk_concentration_score=r.portfolio_risk_concentration_score
                ))
            return metrics
        finally:
            db.close()

# Initialize tables
DB.initialize_demo_profiles()
