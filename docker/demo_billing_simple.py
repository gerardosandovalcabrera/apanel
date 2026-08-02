"""
💰 Simplified Billing Integration Demo - APanel
Functional demo of billing integration
"""

from typing import Dict, List
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from decimal import Decimal

from apanel_cost_tracking import CostCalculator, ModelUsage, get_calculator


@dataclass
class BudgetAlert:
    """Budget alert"""
    alert_type: str
    current_spent: Decimal
    budget_limit: Decimal
    percentage_used: float
    message: str
    timestamp: datetime


@dataclass
class BudgetConfig:
    """Budget configuration"""
    name: str
    monthly_budget: Decimal
    alert_thresholds: List[float]


class BillingIntegrationDemo:
    """Billing integration demo (simplified)"""
    
    def __init__(self):
        self.cost_calculator = get_calculator()
        self.api_calls: List[Dict] = []
        self.budgets: Dict[str, BudgetConfig] = {}
        self.alerts: List[BudgetAlert] = []
    
    def record_api_call(
        self,
        organization_id: str,
        provider_model_id: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> Dict:
        """Record an API call"""
        usage = ModelUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens
        )
        
        cost_breakdown = self.cost_calculator.calculate_cost(provider_model_id, usage)
        
        if not cost_breakdown:
            cost_breakdown = CostBreakdown(
                total_cost=Decimal('0'),
                prompt_cost=Decimal('0'),
