"""
💰 Billing Integration Demo - APanel (No Redis)
Demo of complete integration using in-memory storage
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from decimal import Decimal
import json

from apanel_cost_tracking import (
    CostCalculator,
    ModelUsage,
    CostBreakdown,
    get_calculator
)
from apanel_plans_limits import (
    PlanTier,
    UsageStats
)

@dataclass
class BudgetAlert:
    """Budget alert"""
    alert_id: str
    alert_type: str  # 'warning', 'critical', 'exceeded'
    budget_id: str
    current_spent: Decimal
    budget_limit: Decimal
    percentage_used: float
    message: str
    timestamp: datetime
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class CostMetric:
    """Real-time cost metric"""
    timestamp: datetime
    organization_id: str
    provider_model_id: str
    cost: Decimal
    tokens: int
    cost_per_1k_tokens: float
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class BudgetConfig:
    """Budget configuration"""
    budget_id: str
    organization_id: str
    name: str
    monthly_budget: Decimal
    alert_thresholds: List[float]  # [0.5, 0.8, 1.0] = 50%, 80%, 100%
    currency: str = "USD"
    alert_enabled: bool = True
    email_alerts: bool = True
    webhook_url: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


class BillingIntegrationDemo:
    """Demo implementation of billing integration (in-memory)"""
    
    def __init__(self):
        self.cost_calculator = get_calculator()
        self.budgets: Dict[str, BudgetConfig] = {}
        self.alerts: List[BudgetAlert] = []
        self.cost_records: List[Dict] = []
        self.optimizations: List[Dict] = []
        
    def create_budget(
        self,
        organization_id: str,
        name: str,
        monthly_budget: float,
        alert_thresholds: List[float] = [0.5, 0.8, 1.0],
        currency: str = "USD"
    ) -> BudgetConfig:
        """Create a new budget for an organization"""
        budget_id = f"{organization_id}-{name.lower().replace(' ', '-')}-{datetime.now().strftime('%Y%m')}"
        
        budget = BudgetConfig(
            budget_id=budget_id,
            organization_id=organization_id,
            name=name,
            monthly_budget=Decimal(str(monthly_budget)),
            alert_thresholds=alert_thresholds,
            currency=currency,
            alert_enabled=True,
            email_alerts=True
        )
        
        self.budgets[budget_id] = budget
        return budget
    
    def record_api_call(
        self,
        organization_id: str,
        provider_model_id: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> Dict:
        """Record an API call and return cost information"""
        usage = ModelUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens
        )
        
        cost_breakdown = self.cost_calculator.calculate_cost(provider_model_id, usage)
        
        if not cost_breakdown:
            return {
                'cost': Decimal('0'),
                'tokens': prompt_tokens + completion_tokens,
                'provider_model_id': provider_model_id
            }
        
        record = {
            'organization_id': organization_id,
            'provider_model_id': provider_model_id,
            'prompt_tokens': prompt_tokens,
            'completion_tokens': completion_tokens,
            'total_tokens': prompt_tokens + completion_tokens,
            'cost': cost_breakdown.total_cost,
            'timestamp': datetime.now()
        }
        
        self.cost_records.append(record)
        
        return {
            'cost': cost_breakdown.total_cost,
            'tokens': prompt_tokens + completion_tokens,
            'provider_model_id': provider_model_id,
            'prompt_cost': cost_breakdown.prompt_cost,
            'completion_cost': cost_breakdown.completion_cost
        }
    
    def get_billing_summary(self, organization_id: str) -> Dict:
        """Get complete billing summary for an organization"""
        org_records = [r for r in self.cost_records if r['organization_id'] == organization_id]
        
        total_cost = sum(r['cost'] for r in org_records)
        total_tokens = sum(r['total_tokens'] for r in org_records)
        total_prompt_tokens = sum(r['prompt_tokens'] for r in org_records)
        total_completion_tokens = sum(r['completion_tokens'] for r in org_records)
        
        model_stats = {}
        for record in org_records:
            model_id = record['provider_model_id']
            if model_id not in model_stats:
                model_stats[model_id] = {'cost': Decimal('0'), 'tokens': 0, 'calls': 0}
            model_stats[model_id]['cost'] += record['cost']
            model_stats[model_id]['tokens'] += record['total_tokens']
            model_stats[model_id]['calls'] += 1
        
        budget_status = None
        budget = next((b for b in self.budgets.values() if b.organization_id == organization_id), None)
        
        if budget:
            alerts = self.check_budget_alerts(organization_id, total_cost)
            budget_status = {
                'budget_name': budget.name,
                'monthly_budget': float(budget.monthly_budget),
                'current_spent': float(total_cost),
                'percentage_used': float(total_cost / budget.monthly_budget * 100) if budget.monthly_budget > 0 else 0,
                'remaining': float(budget.monthly_budget - total_cost),
                'alerts': [a.to_dict() for a in alerts]
            }
        
        model_usage = {k: v['tokens'] for k, v in model_stats.items()}
        suggestions = self.get_cost_optimization_suggestions(organization_id, model_usage)
        
        return {
            'organization_id': organization_id,
            'cost_summary': {
                'total_cost': float(total_cost),
                'total_tokens': total_tokens,
                'total_prompt_tokens': total_prompt_tokens,
                'total_completion_tokens': total_completion_tokens,
                'calls_count': len(org_records),
                'average_cost_per_call': float(total_cost / len(org_records)) if org_records else 0,
                'average_tokens_per_call': total_tokens / len(org_records) if org_records else 0
            },
            'model_breakdown': model_stats,
            'budget_status': budget_status,
            'alerts': [a.to_dict() for a in self.alerts[-5:]],
            'optimizations': suggestions,
            'generated_at': datetime.now().isoformat()
        }
    
    def check_budget_alerts(self, organization_id: str, current_monthly_cost: Decimal) -> List[BudgetAlert]:
        """Check if budget alerts should be triggered"""
        alerts = []
        
        for budget in self.budgets.values():
            if budget.organization_id != organization_id:
                continue
            
            percentage = float(current_monthly_cost / budget.monthly_budget * 100) if budget.monthly_budget > 0 else 0
            
            for threshold in budget.alert_thresholds:
                threshold_percentage = float(threshold * 100)
                
                if percentage >= threshold_percentage:
                    alert_type = 'exceeded' if percentage >= 100 else 'warning' if percentage >= 80 else 'warning'
                    
                    alert = BudgetAlert(
                        alert_id=f"alert-{datetime.now().timestamp()}",
                        alert_type=alert_type,
                        budget_id=budget.budget_id,
                        current_spent=current_monthly_cost,
                        budget_limit=budget.monthly_budget,
                        percentage_used=percentage,
                        message=f"Budget alert: {percentage:.1f}% of ${budget.monthly_budget} used",
                        timestamp=datetime.now()
                    )
                    
                    alerts.append(alert)
        
        self.alerts.extend(alerts)
        return alerts
    
    def get_cost_optimization_suggestions(self, organization_id: str, model_usage: Dict[str, int]) -> List[Dict]:
        """Generate cost optimization suggestions based on usage"""
        suggestions = []
        
        model_costs = {}
        for model_id, tokens in model_usage.items():
            usage = ModelUsage(prompt_tokens=tokens // 2, completion_tokens=tokens // 2)
            cost_breakdown = self.cost_calculator.calculate_cost(model_id, usage)
            if cost_breakdown:
                model_costs[model_id] = {
                    'cost': cost_breakdown.total_cost,
                    'tokens': tokens
                }
        
        expensive_models = sorted(model_costs.items(), key=lambda x: float(x[1]['cost']), reverse=True)
        
        if expensive_models:
            most_expensive = expensive_models[0]
            suggestions.append({
                'type': 'model_switch',
                'priority': 'high',
                'message': f"Consider switching from {most_expensive[0]} to a cheaper model",
                'potential_savings': f"${float(most_expensive[1]['cost'] * 0.5):.2f}",
                'current_cost': f"${float(most_expensive[1]['cost']):.2f}"
            })
        
        return suggestions


# Test the demo
if __name__ == "__main__":
    print("🧪 Billing Integration Demo Test")
    print("=" * 60)
    
    billing = BillingIntegrationDemo()
    
    # Create budget
    print("\n1. Creating budget...")
    billing.create_budget(
        organization_id="demo-org",
        name="Monthly Budget",
        monthly_budget=100.00,
        alert_thresholds=[0.5, 0.8, 1.0]
    )
    print("   ✅ Budget created")
    
    # Record API calls
    print("\n2. Recording API calls...")
    billing.record_api_call("demo-org", "openai/gpt-4o", 1500, 500)
    billing.record_api_call("demo-org", "anthropic/claude-3.5-sonnet", 2000, 400)
    billing.record_api_call("demo-org", "openai/gpt-4o-mini", 5000, 2000)
    print("   ✅ 3 API calls recorded")
    
    # Get billing summary
    print("\n3. Getting billing summary...")
    summary = billing.get_billing_summary("demo-org")
    
    cost_summary = summary['cost_summary']
    print(f"   💰 Total cost: ${cost_summary['total_cost']:.6f}")
    print(f"   🪙 Total tokens: {cost_summary['total_tokens']:,}")
    print(f"   📞 Total calls: {cost_summary['calls_count']}")
    
    # Budget status
    if summary['budget_status']:
        budget = summary['budget_status']
        print(f"\n4. Budget status:")
        print(f"   💵 Budget: {budget['budget_name']}")
        print(f"   💵 Spent: ${budget['current_spent']:.6f} / ${budget['monthly_budget']:.2f}")
        print(f"   💵 Percentage: {budget['percentage_used']:.1f}%")
        
        if budget['alerts']:
            print(f"\n   ⚠️  Alerts ({len(budget['alerts'])}):")
            for alert in budget['alerts']:
                print(f"      • {alert['message']}")
    
    # Optimizations
    if summary['optimizations']:
        print(f"\n5. Optimization suggestions:")
        for suggestion in summary['optimizations']:
            print(f"   • [{suggestion['priority'].upper()}] {suggestion['message']}")
            print(f"     Potential savings: {suggestion.get('potential_savings', 'N/A')}")
    
    print("\n✅ Billing integration demo test completed successfully!")
