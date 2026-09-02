from sqlalchemy import Column, Integer, String, Float, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class DBUser(Base):
    __tablename__ = "users"
    
    user_id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    risk_tolerance = Column(String, nullable=False)
    investment_horizon = Column(String, nullable=False)
    total_portfolio_value = Column(Float, nullable=False)
    risk_score = Column(Integer, nullable=False)
    watchlist = Column(JSON, nullable=False)
    previous_decisions_count = Column(Integer, default=0)
    
    holdings = relationship("DBPortfolioHolding", back_populates="user", cascade="all, delete-orphan")

class DBPortfolioHolding(Base):
    __tablename__ = "portfolio_holdings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    symbol = Column(String, nullable=False)
    company_name = Column(String, nullable=False)
    shares = Column(Integer, nullable=False)
    avg_cost = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    value = Column(Float, nullable=False)
    sector = Column(String, nullable=False)
    allocation_pct = Column(Float, nullable=False)
    profit_loss = Column(Float, nullable=False)
    profit_loss_pct = Column(Float, nullable=False)
    
    user = relationship("DBUser", back_populates="holdings")

class DBSessionAnalysis(Base):
    __tablename__ = "sessions"
    
    session_id = Column(String, primary_key=True, index=True)
    timestamp = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    profile_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    technical_signal = Column(String)
    fundamental_signal = Column(String)
    sentiment_signal = Column(String)
    overall_signal = Column(String)
    is_degraded = Column(Boolean, default=False)
    
    # Store full JSON payload for ease of use in prototype
    full_payload = Column(JSON, nullable=False)

class DBPerformanceMetric(Base):
    __tablename__ = "performance_metrics"
    
    session_id = Column(String, primary_key=True, index=True)
    timestamp = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    total_latency_ms = Column(Float, nullable=False)
    agent_latencies = Column(JSON, nullable=False)
    signal_accuracy_pct = Column(Float, nullable=False)
    portfolio_risk_concentration_score = Column(Integer, nullable=False)
