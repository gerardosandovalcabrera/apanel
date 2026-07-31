"""
📊 Sistema de Planes y Límites - DEMO (sin Redis)
Versión de demostración que funciona en memoria
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
    Versión de demo que usa almacenamiento en memoria en lugar de Redis
    Ideal para desarrollo y pruebas
    """
    
    def __init__(self):
        # No usamos Redis, usamos diccionarios en memoria
        self.plans = self.DEFAULT_PLANS.copy()
        self.usage_store: Dict[str, Dict] = {}
        
    def _get_usage_key(self, organization_id: str, limit_type: str) -> str:
        """Generar key para almacenamiento en memoria"""
        return f"{organization_id}:{limit_type}"
    
    def check_concurrent_limit(self, organization_id: str, plan_tier: PlanTier) -> tuple:
        """Verificar límite de concurrencia (en memoria)"""
        plan = self.get_plan(plan_tier)
        if not plan:
            return False, "Plan no encontrado"
        
        key = self._get_usage_key(organization_id, "concurrent_agents")
        
        # Inicializar si no existe
        if key not in self.usage_store:
            self.usage_store[key] = {"value": 0, "updated": datetime.now()}
        
        current = self.usage_store[key]["value"] + 1
        
        if current > plan.limits.concurrent_agents:
            return False, f"Límite de {plan.limits.concurrent_agents} agentes concurrentes excedido"
        
        self.usage_store[key]["value"] = current
        self.usage_store[key]["updated"] = datetime.now()
        
        return True, f"Agentes concurrentes: {current}/{plan.limits.concurrent_agents}"
    
    def release_concurrent_agent(self, organization_id: str):
        """Liberar un slot de agente concurrente (en memoria)"""
        key = self._get_usage_key(organization_id, "concurrent_agents")
        if key in self.usage_store and self.usage_store[key]["value"] > 0:
            self.usage_store[key]["value"] -= 1
    
    def check_monthly_token_limit(self, organization_id: str, plan_tier: PlanTier, tokens_to_add: int) -> tuple:
        """Verificar límite de tokens mensuales (en memoria)"""
        plan = self.get_plan(plan_tier)
        if not plan:
            return False, "Plan no encontrado"
        
        current_month = datetime.now().strftime("%Y-%m")
        key = self._get_usage_key(f"{organization_id}:{current_month}", "tokens")
        
        if key not in self.usage_store:
            self.usage_store[key] = {"value": 0, "updated": datetime.now()}
        
        current = self.usage_store[key]["value"]
        projected = current + tokens_to_add
        
        if projected > plan.limits.monthly_tokens:
            return False, f"Límite de {plan.limits.monthly_tokens:,} tokens/mes excedido"
        
        self.usage_store[key]["value"] = projected
        self.usage_store[key]["updated"] = datetime.now()
        
        return True, f"Tokens usados: {projected:,}/{plan.limits.monthly_tokens:,}"
    
    def check_daily_call_limit(self, organization_id: str, plan_tier: PlanTier) -> tuple:
        """Verificar límite de llamadas diarias (en memoria)"""
        plan = self.get_plan(plan_tier)
        if not plan:
            return False, "Plan no encontrado"
        
        today = datetime.now().strftime("%Y-%m-%d")
        key = self._get_usage_key(f"{organization_id}:{today}", "calls")
        
        if key not in self.usage_store:
            self.usage_store[key] = {"value": 0, "updated": datetime.now()}
        
        current = self.usage_store[key]["value"] + 1
        
        if current > plan.limits.daily_calls:
            return False, f"Límite de {plan.limits.daily_calls:,} llamadas/día excedido"
        
        self.usage_store[key]["value"] = current
        self.usage_store[key]["updated"] = datetime.now()
        
        return True, f"Llamadas hoy: {current:,}/{plan.limits.daily_calls:,}"
    
    def check_api_rate_limit(self, organization_id: str, plan_tier: PlanTier) -> tuple:
        """Verificar rate limiting de API (en memoria)"""
        plan = self.get_plan(plan_tier)
        if not plan:
            return False, "Plan no encontrado"
        
        key = self._get_usage_key(organization_id, "api_rate")
        
        if key not in self.usage_store:
            self.usage_store[key] = {"requests": [], "updated": datetime.now()}
        
        now = datetime.now()
        # Remover requests viejos (> 1 minuto)
        one_minute_ago = now - timedelta(minutes=1)
        self.usage_store[key]["requests"] = [
            req_time for req_time in self.usage_store[key]["requests"]
            if req_time > one_minute_ago
        ]
        
        count = len(self.usage_store[key]["requests"]) + 1
        
        if count > plan.limits.api_calls_per_minute:
            return False, f"Rate limit excedido: {count}/{plan.limits.api_calls_per_minute} requests/minuto"
        
        self.usage_store[key]["requests"].append(now)
        self.usage_store[key]["updated"] = now
        
        return True, f"API calls/minuto: {count}/{plan.limits.api_calls_per_minute}"
    
    def get_usage_stats(self, organization_id: str, plan_tier: PlanTier):
        """Obtener estadísticas de uso actuales (en memoria)"""
        plan = self.get_plan(plan_tier)
        
        # Agentes concurrentes
        concurrent_key = self._get_usage_key(organization_id, "concurrent_agents")
        current_concurrent = self.usage_store.get(concurrent_key, {}).get("value", 0)
        
        # Tokens mensuales
        current_month = datetime.now().strftime("%Y-%m")
        tokens_key = self._get_usage_key(f"{organization_id}:{current_month}", "tokens")
        monthly_tokens = self.usage_store.get(tokens_key, {}).get("value", 0)
        
        # Llamadas diarias
        today = datetime.now().strftime("%Y-%m-%d")
        calls_key = self._get_usage_key(f"{organization_id}:{today}", "calls")
        daily_calls = self.usage_store.get(calls_key, {}).get("value", 0)
        
        # API rate
        api_key = self._get_usage_key(organization_id, "api_rate")
        api_count = len(self.usage_store.get(api_key, {}).get("requests", []))
        
        return {
            "current_concurrent_agents": current_concurrent,
            "monthly_tokens_used": monthly_tokens,
            "daily_calls": daily_calls,
            "api_calls_last_minute": api_count,
            "storage_days_used": plan.limits.storage_days
        }


# Demo interactiva
def run_demo():
    """Ejecutar demo del sistema de planes"""
    print("🎯 DEMO - Sistema de Planes y Límites APanel")
    print("=" * 60)
    
    # Crear manager en memoria
    manager = InMemoryPlansManager()
    
    # Mostrar planes disponibles
    print("\n📋 Planes Disponibles:")
    print("-" * 60)
    for plan in manager.get_all_plans():
        print(f"\n{plan.name} (${plan.price_monthly or 0}/mes)")
        print(f"  🤖 Agentes: {plan.limits.concurrent_agents}")
        print(f"  🪙 Tokens: {plan.limits.monthly_tokens:,}")
        print(f"  📞 Llamadas/día: {plan.limits.daily_calls:,}")
        print(f"  ⚡ API/min: {plan.limits.api_calls_per_minute}")
    
    # Simular uso
    org_id = "demo-org-001"
    print(f"\n🧪 Simulando uso para: {org_id}")
    print("-" * 60)
    
    # Test 1: Verificar concurrencia
    print("\n1️⃣ Test Concurrencia de Agentes:")
    for i in range(5):
        allowed, msg = manager.check_concurrent_limit(org_id, PlanTier.PRO)
        status = "✅" if allowed else "❌"
        print(f"   {status} Agente {i+1}: {msg}")
    
    # Test 2: Verificar tokens
    print("\n2️⃣ Test Tokens Mensuales:")
    token_amounts = [1000, 5000, 10000, 20000]
    total_tokens = 0
    for tokens in token_amounts:
        allowed, msg = manager.check_monthly_token_limit(org_id, PlanTier.PRO, tokens)
        status = "✅" if allowed else "❌"
        total_tokens += tokens if allowed else 0
        print(f"   {status} +{tokens:,} tokens: {msg}")
    
    # Test 3: Verificar llamadas diarias
    print("\n3️⃣ Test Llamadas Diarias:")
    for i in range(3):
        allowed, msg = manager.check_daily_call_limit(org_id, PlanTier.PRO)
        status = "✅" if allowed else "❌"
        print(f"   {status} Llamada {i+1}: {msg}")
    
    # Test 4: Verificar rate limiting
    print("\n4️⃣ Test API Rate Limiting:")
    for i in range(15):
        allowed, msg = manager.check_api_rate_limit(org_id, PlanTier.PRO)
        status = "✅" if allowed else "❌"
        if not allowed:
            print(f"   {status} Request {i+1}: {msg}")
            break
        if i % 5 == 4:  # Mostrar cada 5
            print(f"   {status} Request {i+1}: {msg}")
    else:
        print(f"   ✅ Todos los requests permitidos (rate limit alto)")
    
    # Mostrar estadísticas finales
    print("\n📊 Estadísticas Finales:")
    print("-" * 60)
    usage = manager.get_usage_stats(org_id, PlanTier.PRO)
    plan = manager.get_plan(PlanTier.PRO)
    
    print(f"🤖 Agentes concurrentes: {usage['current_concurrent_agents']}/{plan.limits.concurrent_agents}")
    print(f"🪙 Tokens usados: {usage['monthly_tokens_used']:,}/{plan.limits.monthly_tokens:,}")
    print(f"📞 Llamadas hoy: {usage['daily_calls']:,}/{plan.limits.daily_calls:,}")
    print(f"⚡ API calls/min: {usage['api_calls_last_minute']}/{plan.limits.api_calls_per_minute}")
    
    # Calcular porcentajes
    tokens_pct = (usage['monthly_tokens_used'] / plan.limits.monthly_tokens) * 100
    calls_pct = (usage['daily_calls'] / plan.limits.daily_calls) * 100
    concurrent_pct = (usage['current_concurrent_agents'] / plan.limits.concurrent_agents) * 100
    
    print(f"\n📈 Porcentajes de Uso:")
    print(f"   Tokens: {tokens_pct:.1f}%")
    print(f"   Llamadas: {calls_pct:.1f}%")
    print(f"   Concurrencia: {concurrent_pct:.1f}%")
    
    # Sugerencias
    print("\n💡 Sugerencias del Sistema:")
    if tokens_pct > 80:
        print("   ⚠️ Estás cerca del límite de tokens mensuales")
        print("   💡 Considera hacer upgrade a Team Tier para 5M tokens/mes")
    if concurrent_pct > 80:
        print("   ⚠️ Tienes muchos agentes concurrentes activos")
        print("   💡 El plan Team permite hasta 100 agentes concurrentes")
    
    # Comparación de planes
    print("\n🔄 Comparación de Planes:")
    print("-" * 60)
    print(f"Plan Actual: PRO (${plan.price_monthly}/mes)")
    print(f"  - {plan.limits.concurrent_agents} agentes, {plan.limits.monthly_tokens:,} tokens")
    
    next_tier = manager._get_next_tier(PlanTier.PRO)
    if next_tier:
        next_plan = manager.get_plan(next_tier)
        print(f"\nSiguiente: {next_plan.name} (${next_plan.price_monthly}/mes)")
        print(f"  - {next_plan.limits.concurrent_agents} agentes, {next_plan.limits.monthly_tokens:,} tokens")
        print(f"  - ¡{next_plan.limits.monthly_tokens / plan.limits.monthly_tokens:.0f}x más tokens!")
        
        # Ahorro anual
        if next_plan.price_yearly:
            monthly_yearly = next_plan.price_yearly / 12
            savings_pct = (1 - monthly_yearly / next_plan.price_monthly) * 100
            print(f"  - Ahorra {savings_pct:.0f}% con plan anual (${next_plan.price_yearly}/año)")
    
    print("\n✅ Demo completada exitosamente!")


if __name__ == "__main__":
    run_demo()
