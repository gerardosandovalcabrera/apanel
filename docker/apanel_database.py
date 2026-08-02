"""
💾 APanel Database Module - PostgreSQL Persistence
Complete database schema and models for APanel

This module provides persistent storage for:
- Billing records
- Cost tracking history
- Budget alerts
- Token usage statistics
- Agent metrics
- User organizations
- Plans and limits

Database: PostgreSQL with SQLAlchemy ORM
"""

import os
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    Decimal as SQLDecimal,
    Float,
    Boolean,
    Text,
    ForeignKey,
    Index,
    JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

# Database URL from environment or default
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://apanel:apanel_password@localhost:5432/apanel_db'
)

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ==========================================
# ORGANIZATION MODEL
# ==========================================
class Organization(Base):
    """Organization (tenant) model"""
    __tablename__ = "organizations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    plan_tier = Column(String(50), nullable=False, default="free")  # free, pro, team, enterprise
    api_key = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    budgets = relationship("Budget", back_populates="organization", cascade="all, delete-orphan")
    billing_records = relationship("BillingRecord", back_populates="organization", cascade="all, delete-orphan")
    cost_metrics = relationship("CostMetric", back_populates="organization", cascade="all, delete-orphan")
    token_usage = relationship("TokenUsage", back_populates="organization", cascade="all, delete-orphan")
    alerts = relationship("BudgetAlert", back_populates="organization", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "plan_tier": self.plan_tier,
            "api_key": self.api_key,
            "email": self.email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_active": self.is_active
        }


# ==========================================
# BUDGET MODEL
# ==========================================
class Budget(Base):
    """Budget configuration model"""
    __tablename__ = "budgets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id'), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    monthly_budget = Column(SQLDecimal(10, 2), nullable=False)
    currency = Column(String(10), default="USD")
    alert_thresholds = Column(JSON)  # [50, 80, 100] for 50%, 80%, 100%
    alert_enabled = Column(Boolean, default=True)
    email_alerts = Column(Boolean, default=True)
    webhook_url = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    organization = relationship("Organization", back_populates="budgets")
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "organization_id": str(self.organization_id),
            "name": self.name,
            "monthly_budget": float(self.monthly_budget),
            "currency": self.currency,
            "alert_thresholds": self.alert_thresholds,
            "alert_enabled": self.alert_enabled,
            "email_alerts": self.email_alerts,
            "webhook_url": self.webhook_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


# ==========================================
# BILLING RECORD MODEL
# ==========================================
class BillingRecord(Base):
    """Individual API call billing record"""
    __tablename__ = "billing_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id'), nullable=False, index=True)
    provider_model_id = Column(String(255), nullable=False, index=True)
    prompt_tokens = Column(Integer, nullable=False)
    completion_tokens = Column(Integer, nullable=False)
    total_tokens = Column(Integer, nullable=False)
    prompt_cost = Column(SQLDecimal(10, 6), nullable=False)
    completion_cost = Column(SQLDecimal(10, 6), nullable=False)
    total_cost = Column(SQLDecimal(10, 6), nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    request_id = Column(String(255), index=True)
    metadata = Column(JSON)  # Additional request metadata
    
    # Relationship
    organization = relationship("Organization", back_populates="billing_records")
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_billing_org_timestamp', 'organization_id', 'timestamp'),
        Index('idx_billing_model_timestamp', 'provider_model_id', 'timestamp'),
    )
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "organization_id": str(self.organization_id),
            "provider_model_id": self.provider_model_id,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "prompt_cost": float(self.prompt_cost),
            "completion_cost": float(self.completion_cost),
            "total_cost": float(self.total_cost),
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "request_id": self.request_id,
            "metadata": self.metadata
        }


# ==========================================
# COST METRIC MODEL
# ==========================================
class CostMetric(Base):
    """Aggregated cost metrics for analytics"""
    __tablename__ = "cost_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id'), nullable=False, index=True)
    metric_type = Column(String(50), nullable=False)  # hourly, daily, weekly, monthly
    period_start = Column(DateTime, nullable=False, index=True)
    period_end = Column(DateTime, nullable=False)
    total_cost = Column(SQLDecimal(10, 6), nullable=False)
    total_tokens = Column(Integer, nullable=False)
    total_calls = Column(Integer, nullable=False)
    average_cost_per_call = Column(SQLDecimal(10, 6))
    average_tokens_per_call = Column(Float)
    model_breakdown = Column(JSON)  # Cost breakdown by model
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    organization = relationship("Organization", back_populates="cost_metrics")
    
    # Indexes
    __table_args__ = (
        Index('idx_metrics_org_period', 'organization_id', 'metric_type', 'period_start'),
    )
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "organization_id": str(self.organization_id),
            "metric_type": self.metric_type,
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
            "total_cost": float(self.total_cost),
            "total_tokens": self.total_tokens,
            "total_calls": self.total_calls,
            "average_cost_per_call": float(self.average_cost_per_call) if self.average_cost_per_call else None,
            "average_tokens_per_call": self.average_tokens_per_call,
            "model_breakdown": self.model_breakdown,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


# ==========================================
# TOKEN USAGE MODEL
# ==========================================
class TokenUsage(Base):
    """Detailed token usage tracking"""
    __tablename__ = "token_usage"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id'), nullable=False, index=True)
    month = Column(String(7), nullable=False, index=True)  # YYYY-MM format
    provider_model_id = Column(String(255), nullable=False, index=True)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    cost = Column(SQLDecimal(10, 6), default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    organization = relationship("Organization", back_populates="token_usage")
    
    # Unique constraint
    __table_args__ = (
        Index('idx_token_usage_unique', 'organization_id', 'month', 'provider_model_id', unique=True),
    )
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "organization_id": str(self.organization_id),
            "month": self.month,
            "provider_model_id": self.provider_model_id,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "cost": float(self.cost),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


# ==========================================
# BUDGET ALERT MODEL
# ==========================================
class BudgetAlert(Base):
    """Budget alert notifications"""
    __tablename__ = "budget_alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id'), nullable=False, index=True)
    budget_id = Column(UUID(as_uuid=True), ForeignKey('budgets.id'), nullable=False)
    alert_type = Column(String(50), nullable=False)  # warning, critical, exceeded
    current_spent = Column(SQLDecimal(10, 2), nullable=False)
    budget_limit = Column(SQLDecimal(10, 2), nullable=False)
    percentage_used = Column(Float, nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    is_sent = Column(Boolean, default=False)  # Email/notification sent
    sent_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationship
    organization = relationship("Organization", back_populates="alerts")
    
    # Indexes
    __table_args__ = (
        Index('idx_alerts_org_created', 'organization_id', 'created_at'),
    )
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "organization_id": str(self.organization_id),
            "budget_id": str(self.budget_id),
            "alert_type": self.alert_type,
            "current_spent": float(self.current_spent),
            "budget_limit": float(self.budget_limit),
            "percentage_used": self.percentage_used,
            "message": self.message,
            "is_read": self.is_read,
            "is_sent": self.is_sent,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


# ==========================================
# DATABASE MANAGER
# ==========================================
class DatabaseManager:
    """Database operations manager"""
    
    def __init__(self, database_url: str = None):
        """Initialize database manager"""
        self.database_url = database_url or DATABASE_URL
        self.engine = create_engine(self.database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.Base = Base
    
    def create_tables(self):
        """Create all database tables"""
        Base.metadata.create_all(bind=self.engine)
        print("✅ Database tables created successfully")
    
    def drop_tables(self):
        """Drop all database tables (use with caution!)"""
        Base.metadata.drop_all(bind=self.engine)
        print("⚠️  Database tables dropped")
    
    def get_session(self):
        """Get a new database session"""
        return self.SessionLocal()
    
    def get_organization_by_api_key(self, api_key: str) -> Optional[Organization]:
        """Get organization by API key"""
        session = self.get_session()
        try:
            org = session.query(Organization).filter(
                Organization.api_key == api_key,
                Organization.is_active == True
            ).first()
            return org
        finally:
            session.close()
    
    def create_organization(self, name: str, plan_tier: str = "free", email: str = None) -> Organization:
        """Create a new organization"""
        session = self.get_session()
        try:
            api_key = f"apanel-{uuid.uuid4().hex[:32]}"
            org = Organization(
                name=name,
                plan_tier=plan_tier,
                api_key=api_key,
                email=email
            )
            session.add(org)
            session.commit()
            session.refresh(org)
            return org
        finally:
            session.close()


# ==========================================
# UTILITY FUNCTIONS
# ==========================================
def init_database(database_url: str = None):
    """Initialize database and create tables"""
    db_manager = DatabaseManager(database_url)
    db_manager.create_tables()
    return db_manager


def get_database_manager() -> DatabaseManager:
    """Get database manager instance"""
    return DatabaseManager(DATABASE_URL)


if __name__ == "__main__":
    # Test database initialization
    print("🗄️  Initializing APanel Database...")
    print(f"📊 Database URL: {DATABASE_URL}")
    
    # Initialize database
    db_manager = init_database()
    
    # Create test organization
    print("\n🧪 Creating test organization...")
    org = db_manager.create_organization(
        name="Test Organization",
        plan_tier="pro",
        email="test@example.com"
    )
    print(f"✅ Organization created: {org.name}")
    print(f"   ID: {org.id}")
    print(f"   API Key: {org.api_key}")
    print(f"   Plan: {org.plan_tier}")
    
    print("\n✅ Database initialization completed successfully!")
    print("\n📊 Tables created:")
    for table_name in Base.metadata.tables.keys():
        print(f"   • {table_name}")
