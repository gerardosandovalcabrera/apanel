"""
💾 Database Integration for APanel
Integration with PostgreSQL for persistent storage

This module provides database operations for:
- Recording API calls with cost tracking
- Budget monitoring and alerts
- Token usage analytics
- Cost metrics aggregation
- Historical data queries
"""

import os
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Dict
import logging

from apanel_database import (
    DatabaseManager,
    Organization,
    Budget,
    BillingRecord,
    CostMetric,
    TokenUsage,
    BudgetAlert,
    get_database_manager
)
from apanel_cost_tracking import CostCalculator, ModelUsage, CostBreakdown, get_calculator

logger = logging.getLogger(__name__)


class DatabaseBillingIntegration:
    """
    Database-backed billing integration system
    
    Replaces in-memory storage with PostgreSQL persistence:
    - All API calls are saved to database
    - Historical data is preserved
    - Budget alerts are logged
    - Token usage is tracked over time
    - Cost metrics are aggregated
    """
    
    def __init__(self, database_url: str = None):
        """Initialize database billing integration"""
        self.db_manager = get_database_manager()
        self.cost_calculator = get_calculator()
    
    def record_api_call(
        self,
        organization_id: str,
        provider_model_id: str,
        prompt_tokens: int,
        completion_tokens: int,
        request_id: str = None,
        metadata: Dict = None
    ) -> Dict:
        """
        Record an API call to the database
        
        This creates a persistent record of the API call with:
        - Token usage
        - Cost calculation
        - Timestamp
        - Request metadata
        """
        session = self.db_manager.get_session()
        
        try:
            # Calculate cost
            usage = ModelUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens
            )
            cost_breakdown = self.cost_calculator.calculate_cost(provider_model_id, usage)
            
            if not cost_breakdown:
                cost_breakdown = CostBreakdown(
                    total_cost=Decimal('0'),
                    prompt_cost=Decimal('0'),
                    completion_cost=Decimal('0'),
                    cost_per_1k_tokens=Decimal('0')
                )
            
            # Create billing record
            record = BillingRecord(
                organization_id=organization_id,
                provider_model_id=provider_model_id,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                prompt_cost=cost_breakdown.prompt_cost,
                completion_cost=cost_breakdown.completion_cost,
                total_cost=cost_breakdown.total_cost,
                timestamp=datetime.utcnow(),
                request_id=request_id,
                metadata=metadata or {}
            )
            
            session.add(record)
            session.commit()
            session.refresh(record)
            
            # Update token usage
            self._update_token_usage(
                session,
                organization_id,
                provider_model_id,
                prompt_tokens,
                completion_tokens,
                cost_breakdown.total_cost
            )
            
            # Check budget alerts
            self._check_budget_alerts(session, organization_id, provider_model_id)
            
            return {
                'cost': float(record.total_cost),
                'tokens': record.total_tokens,
                'provider_model_id': provider_model_id,
                'prompt_cost': float(record.prompt_cost),
                'completion_cost': float(record.completion_cost),
                'record_id': str(record.id)
            }
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error recording API call: {e}")
            raise
        finally:
            session.close()
    
    def _update_token_usage(
        self,
        session,
        organization_id: str,
        provider_model_id: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost: Decimal
    ):
        """Update monthly token usage"""
        month = datetime.utcnow().strftime("%Y-%m")
        
        # Try to find existing record
        usage = session.query(TokenUsage).filter(
            TokenUsage.organization_id == organization_id,
            TokenUsage.month == month,
            TokenUsage.provider_model_id == provider_model_id
        ).first()
        
        if usage:
            # Update existing
            usage.prompt_tokens += prompt_tokens
            usage.completion_tokens += completion_tokens
            usage.total_tokens += (prompt_tokens + completion_tokens)
            usage.cost += cost
            usage.updated_at = datetime.utcnow()
        else:
            # Create new
            usage = TokenUsage(
                organization_id=organization_id,
                month=month,
                provider_model_id=provider_model_id,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                cost=cost
            )
            session.add(usage)
        
        session.commit()
    
    def _check_budget_alerts(
        self,
        session,
        organization_id: str,
        provider_model_id: str
    ):
        """Check if budget alerts should be triggered"""
        # Get current month's total spend
        current_month = datetime.utcnow().strftime("%Y-%m")
        
        total_spent = session.query(BillingRecord).filter(
            BillingRecord.organization_id == organization_id,
            BillingRecord.timestamp >= datetime.utcnow().replace(day=1)
        ).with_entities(
            session.query(BillingRecord.total_cost)
        ).all()
        
        current_monthly_cost = sum(record[0] for record in total_spent) if total_spent else Decimal('0')
        
        # Get budgets for organization
        budgets = session.query(Budget).filter(
            Budget.organization_id == organization_id,
            Budget.alert_enabled == True
        ).all()
        
        for budget in budgets:
            percentage = float(current_monthly_cost / budget.monthly_budget * 100) if budget.monthly_budget > 0 else 0
            
            for threshold in budget.alert_thresholds or []:
                threshold_percentage = float(threshold * 100)
                
                if percentage >= threshold_percentage:
                    # Check if we already sent an alert for this threshold
                    existing_alert = session.query(BudgetAlert).filter(
                        BudgetAlert.organization_id == organization_id,
                        BudgetAlert.budget_id == budget.id,
                        BudgetAlert.percentage_used >= threshold_percentage - 5,
                        BudgetAlert.percentage_used <= threshold_percentage + 5,
                        BudgetAlert.created_at >= datetime.utcnow() - timedelta(hours=24)
                    ).first()
                    
                    if not existing_alert:
                        # Create new alert
                        alert = BudgetAlert(
                            organization_id=organization_id,
                            budget_id=budget.id,
                            alert_type='exceeded' if percentage >= 100 else 'warning' if percentage >= 80 else 'warning',
                            current_spent=current_monthly_cost,
                            budget_limit=budget.monthly_budget,
                            percentage_used=percentage,
                            message=f"Budget alert: {percentage:.1f}% of ${budget.monthly_budget:.2f} used"
                        )
                        session.add(alert)
                        session.commit()
    
    def get_billing_summary(self, organization_id: str, days: int = 30) -> Dict:
        """Get billing summary for an organization"""
        session = self.db_manager.get_session()
        
        try:
            # Calculate date range
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get records
            records = session.query(BillingRecord).filter(
                BillingRecord.organization_id == organization_id,
                BillingRecord.timestamp >= start_date
            ).all()
            
            if not records:
                return {
                    'organization_id': organization_id,
                    'cost_summary': {
                        'total_cost': 0.0,
                        'total_tokens': 0,
                        'calls_count': 0,
                        'average_cost_per_call': 0.0,
                        'average_tokens_per_call': 0.0
                    },
                    'model_breakdown': {},
                    'alerts': [],
                    'generated_at': datetime.utcnow().isoformat()
                }
            
            # Calculate totals
            total_cost = sum(r.total_cost for r in records)
            total_tokens = sum(r.total_tokens for r in records)
            calls_count = len(records)
            
            # Model breakdown
            model_stats = {}
            for record in records:
                model_id = record.provider_model_id
                if model_id not in model_stats:
                    model_stats[model_id] = {'cost': Decimal('0'), 'tokens': 0, 'calls': 0}
                model_stats[model_id]['cost'] += record.total_cost
                model_stats[model_id]['tokens'] += record.total_tokens
                model_stats[model_id]['calls'] += 1
            
            # Get recent alerts
            alerts = session.query(BudgetAlert).filter(
                BudgetAlert.organization_id == organization_id,
                BudgetAlert.created_at >= start_date
            ).order_by(BudgetAlert.created_at.desc()).limit(10).all()
            
            return {
                'organization_id': organization_id,
                'cost_summary': {
                    'total_cost': float(total_cost),
                    'total_tokens': total_tokens,
                    'calls_count': calls_count,
                    'average_cost_per_call': float(total_cost / calls_count) if calls_count > 0 else 0,
                    'average_tokens_per_call': total_tokens / calls_count if calls_count > 0 else 0
                },
                'model_breakdown': {
                    k: {'cost': float(v['cost']), 'tokens': v['tokens'], 'calls': v['calls']}
                    for k, v in model_stats.items()
                },
                'alerts': [alert.to_dict() for alert in alerts],
                'generated_at': datetime.utcnow().isoformat()
            }
            
        finally:
            session.close()
    
    def get_historical_data(
        self,
        organization_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict]:
        """Get historical billing data for a date range"""
        session = self.db_manager.get_session()
        
        try:
            records = session.query(BillingRecord).filter(
                BillingRecord.organization_id == organization_id,
                BillingRecord.timestamp >= start_date,
                BillingRecord.timestamp <= end_date
            ).order_by(BillingRecord.timestamp.desc()).all()
            
            return [record.to_dict() for record in records]
            
        finally:
            session.close()


# Initialize database billing integration
def get_database_billing_integration() -> DatabaseBillingIntegration:
    """Get database billing integration instance"""
    return DatabaseBillingIntegration()


if __name__ == "__main__":
    # Test database billing integration
    print("🧪 Testing Database Billing Integration...")
    
    # Initialize database
    from apanel_database import init_database
    db_manager = init_database()
    
    # Create test organization
    org = db_manager.create_organization("Test Org", "pro")
    
    # Test billing integration
    billing = get_database_billing_integration()
    
    print("\n1. Recording API calls...")
    result = billing.record_api_call(
        organization_id=str(org.id),
        provider_model_id="openai/gpt-4",
        prompt_tokens=1000,
        completion_tokens=500
    )
    print(f"   ✅ Recorded: Cost ${result['cost']:.6f}, Tokens {result['tokens']}")
    
    print("\n2. Getting billing summary...")
    summary = billing.get_billing_summary(str(org.id))
    print(f"   ✅ Total cost: ${summary['cost_summary']['total_cost']:.6f}")
    print(f"   ✅ Total calls: {summary['cost_summary']['calls_count']}")
    
    print("\n✅ Database billing integration test completed!")
