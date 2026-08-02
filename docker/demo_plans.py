"""
📊 Plans and Limits System - DEMO (no Redis)
Demo version that works in-memory
"""

from apanel_plans_limits import (
    PlanTier,
    Plan,
    PlanLimits,
    PlansManager,
    get_plans_manager
)
from typing import Dict
from datetime import datetime, timedelta

class InMemoryPlansManager(PlansManager):
    """
    Demo version that uses in-memory storage instead of Redis
    Ideal for development and testing
    """
    
    def __init__(self):
        # We don't use Redis, we use in-memory dictionaries
        self.plans = self.DEFAULT_PLANS.copy()
        self.usage_store: Dict[str, Dict] = {}
        
    def _get_usage_key(self, organization_id: str, limit_type: str) -> str:
        """Generate key for in-memory storage"""
        return f"{organization_id}:{limit_type}"
    
    def check_concurrent_limit(self, organization_id: str, plan_tier: PlanTier) -> tuple:
        """Check concurrent agent limit (in-memory)"""
        plan = self.get_plan(plan_tier)
        if not plan:
            return False, "Plan not found"
        
        key = self._get_usage_key(organization_id, "concurrent_agents")
        
        # Initialize if doesn't exist
        if key not in self.usage_store:
            self.usage_store[key] = {"value": 0, "updated": datetime.now()}
        
        current = self.usage_store[key]["value"] + 1
        
        if current > plan.limits.concurrent_agents:
            return False, f"Concurrent agent limit of {plan.limits.concurrent_agents} exceeded"
        
        self.usage_store[key]["value"] = current
        self.usage_store[key]["updated"] = datetime.now()
        
        return True, f"Concurrent agents: {current}/{plan.limits.concurrent_agents}"
    
    def release_concurrent_agent(self, organization_id: str):
        """Release a concurrent agent slot (in-memory)"""
        key = self._get_usage_key(organization_id, "concurrent_agents")
        if key in self.usage_store and self.usage_store[key]["value"] > 0:
            self.usage_store[key]["value"] -= 1
    
    def check_monthly_token_limit(self, organization_id: str, plan_tier: PlanTier, tokens_to_add: int) -> tuple:
        """Check monthly token limit (in-memory)"""
        plan = self.get_plan(plan_tier)
        if not plan:
            return False, "Plan not found"
        
        # Unlimited plan
        if plan.limits.monthly_tokens == -1:
            return True, "Unlimited monthly tokens"
        
        key = self._get_usage_key(organization_id, "monthly_tokens")
        
        # Initialize if doesn't exist
        if key not in self.usage_store:
            self.usage_store[key] = {
                "value": 0,
                "month": datetime.now().strftime("%Y-%m"),
                "updated": datetime.now()
            }
        
        # Reset if new month
        current_month = datetime.now().strftime("%Y-%m")
        if self.usage_store[key]["month"] != current_month:
            self.usage_store[key]["value"] = 0
            self.usage_store[key]["month"] = current_month
        
        current = self.usage_store[key]["value"]
        new_total = current + tokens_to_add
        
        if new_total > plan.limits.monthly_tokens:
            remaining = plan.limits.monthly_tokens - current
            return False, f"Monthly token limit exceeded: {remaining} tokens remaining"
        
        self.usage_store[key]["value"] = new_total
        self.usage_store[key]["updated"] = datetime.now()
        
        return True, f"Monthly tokens: {new_total:,}/{plan.limits.monthly_tokens:,}"
    
    def get_usage_stats(self, organization_id: str, plan_tier: PlanTier) -> Dict:
        """Get usage statistics for an organization (in-memory)"""
        plan = self.get_plan(plan_tier)
        if not plan:
            return {}
        
        concurrent_key = self._get_usage_key(organization_id, "concurrent_agents")
        tokens_key = self._get_usage_key(organization_id, "monthly_tokens")
        
        concurrent_current = self.usage_store.get(concurrent_key, {}).get("value", 0)
        tokens_current = self.usage_store.get(tokens_key, {}).get("value", 0)
        
        return {
            "concurrent_agents": {
                "current": concurrent_current,
                "limit": plan.limits.concurrent_agents,
                "percentage": (concurrent_current / plan.limits.concurrent_agents * 100) if plan.limits.concurrent_agents > 0 else 0
            },
            "monthly_tokens": {
                "current": tokens_current,
                "limit": plan.limits.monthly_tokens,
                "percentage": (tokens_current / plan.limits.monthly_tokens * 100) if plan.limits.monthly_tokens > 0 else 0
            },
            "updated_at": datetime.now().isoformat()
        }


# Test the demo
if __name__ == "__main__":
    print("🧪 Plans and Limits Demo Test")
    print("=" * 60)
    
    manager = InMemoryPlansManager()
    org_id = "demo-org"
    
    # Get plan
    print("\n1. Getting plan details...")
    plan = manager.get_plan(PlanTier.PRO)
    if plan:
        print(f"   ✅ Plan: {plan.name}")
        print(f"   ✅ Tier: {plan.tier}")
        print(f"   ✅ Price: ${plan.price_monthly}/month")
        print(f"   ✅ Concurrent agents: {plan.limits.concurrent_agents}")
        print(f"   ✅ Monthly tokens: {plan.limits.monthly_tokens:,}")
    
    # Check concurrent limit
    print("\n2. Checking concurrent agent limit...")
    for i in range(3):
        success, message = manager.check_concurrent_limit(org_id, PlanTier.PRO)
        print(f"   Attempt {i+1}: {message}")
    
    # Try to exceed limit
    print("\n3. Attempting to exceed concurrent limit...")
    success, message = manager.check_concurrent_limit(org_id, PlanTier.PRO)
    print(f"   Result: {message}")
    if not success:
        print("   ✅ Limit correctly enforced")
    
    # Release agent
    print("\n4. Releasing one agent...")
    manager.release_concurrent_agent(org_id)
    success, message = manager.check_concurrent_limit(org_id, PlanTier.PRO)
    print(f"   After release: {message}")
    
    # Check monthly token limit
    print("\n5. Checking monthly token limit...")
    success, message = manager.check_monthly_token_limit(org_id, PlanTier.PRO, 10000)
    print(f"   Adding 10,000 tokens: {message}")
    
    # Get usage stats
    print("\n6. Getting usage statistics...")
    stats = manager.get_usage_stats(org_id, PlanTier.PRO)
    print(f"   Concurrent agents: {stats['concurrent_agents']['current']}/{stats['concurrent_agents']['limit']} ({stats['concurrent_agents']['percentage']:.1f}%)")
    print(f"   Monthly tokens: {stats['monthly_tokens']['current']:,}/{stats['monthly_tokens']['limit']:,} ({stats['monthly_tokens']['percentage']:.1f}%)")
    
    # Check upgrade
    print("\n7. Checking upgrade options...")
    can_upgrade, options = manager.can_upgrade(org_id, PlanTier.FREE)
    print(f"   Can upgrade from FREE: {can_upgrade}")
    if can_upgrade:
        print(f"   Available upgrades: {', '.join(options)}")
    
    print("\n✅ Plans and limits demo test completed successfully!")
