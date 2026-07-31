"""
📊 Plans & Limits Module - Sistema de Planes y Límites para APanel

Este módulo implementa:
1. Gestión de planes (Free, Pro, Team, Enterprise)
2. Límites de concurrencia (agentes simultáneos)
3. Límites de tokens (consumo mensual)
4. Rate limiting por plan
5. Alertas de límites cercanos
6. Sugerencias de upgrade automático
7. Integración con billing
8. Enforcement activo de límites

Autor: Hermes Agent System
Fecha: 2025-07-31
"""

import redis
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import time


class PlanTier(Enum):
    """Niveles de planes disponibles"""
    FREE = "free"
    PRO = "pro"
    TEAM = "team"
    ENTERPRISE = "enterprise"


class LimitType(Enum):
    """Tipos de límites"""
    CONCURRENT_AGENTS = "concurrent_agents"      # Agentes simultáneos
    MONTHLY_TOKENS = "monthly_tokens"             # Tokens mensuales
    DAILY_CALLS = "daily_calls"                   # Llamadas diarias
    API_CALLS_PER_MINUTE = "api_calls_per_minute" # Rate limiting
    STORAGE_DAYS = "storage_days"                 # Retención de datos


@dataclass
class PlanLimits:
    """Límites de un plan específico"""
    concurrent_agents: int
    monthly_tokens: int
    daily_calls: int
    api_calls_per_minute: int
    storage_days: int
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class Plan:
    """Definición completa de un plan"""
    id: str
    name: str
    tier: PlanTier
    price_monthly: Optional[float]
    price_yearly: Optional[float]
    limits: PlanLimits
    features: List[str]
    is_active: bool
    created_at: datetime
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "tier": self.tier.value,
            "price_monthly": self.price_monthly,
            "price_yearly": self.price_yearly,
            "limits": self.limits.to_dict(),
            "features": self.features,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class UsageStats:
    """Estadísticas de uso de un cliente"""
    current_concurrent_agents: int
    monthly_tokens_used: int
    daily_calls: int
    api_calls_last_minute: int
    storage_days_used: int
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class LimitStatus:
    """Estado de límites de un cliente"""
    plan_id: str
    plan_name: str
    tier: PlanTier
    limits: PlanLimits
    usage: UsageStats
    is_over_limit: bool
    limits_exceeded: List[str]
    warnings: List[str]
    suggestions: List[str]
    next_billing_date: Optional[datetime]
    
    def to_dict(self) -> Dict:
        return {
            "plan_id": self.plan_id,
            "plan_name": self.plan_name,
            "tier": self.tier.value,
            "limits": self.limits.to_dict(),
            "usage": self.usage.to_dict(),
            "is_over_limit": self.is_over_limit,
            "limits_exceeded": self.limits_exceeded,
            "warnings": self.warnings,
            "suggestions": self.suggestions,
            "next_billing_date": self.next_billing_date.isoformat() if self.next_billing_date else None
        }


class PlansManager:
    """
    Gestor de planes y límites
    
    Este manager:
    - Define y gestiona planes de precios
    - Hace enforcement activo de límites
    - Rastrea uso en tiempo real
    - Genera alertas y sugerencias
    - Se integra con sistemas de billing
    """
    
    # Definición de planes por defecto
    DEFAULT_PLANS = {
        PlanTier.FREE: Plan(
            id="plan-free",
            name="Free Tier",
            tier=PlanTier.FREE,
            price_monthly=0.0,
            price_yearly=0.0,
            limits=PlanLimits(
                concurrent_agents=3,
                monthly_tokens=100000,      # 100K tokens/mes
                daily_calls=1000,           # 1000 llamadas/día
                api_calls_per_minute=10,    # 10 llamadas/minuto
                storage_days=7              # 7 días de retención
            ),
            features=[
                "Hasta 3 agentes simultáneos",
                "100,000 tokens/mes",
                "Métricas básicas",
                "7 días de retención de datos",
                "Soporte por email"
            ],
            is_active=True,
            created_at=datetime.now()
        ),
        PlanTier.PRO: Plan(
            id="plan-pro",
            name="Pro Tier",
            tier=PlanTier.PRO,
            price_monthly=49.0,
            price_yearly=490.0,  # 2 meses gratis
            limits=PlanLimits(
                concurrent_agents=20,
                monthly_tokens=500000,      # 500K tokens/mes
                daily_calls=50000,          # 50K llamadas/día
                api_calls_per_minute=100,   # 100 llamadas/minuto
                storage_days=30             # 30 días de retención
            ),
            features=[
                "Hasta 20 agentes simultáneos",
                "500,000 tokens/mes",
                "Métricas avanzadas",
                "30 días de retención de datos",
                "Cost tracking",
                "Basic tracing",
                "Email alerts",
                "Soporte prioritario"
            ],
            is_active=True,
            created_at=datetime.now()
        ),
        PlanTier.TEAM: Plan(
            id="plan-team",
            name="Team Tier",
            tier=PlanTier.TEAM,
            price_monthly=249.0,
            price_yearly=2490.0,  # 2 meses gratis
            limits=PlanLimits(
                concurrent_agents=100,
                monthly_tokens=5000000,     # 5M tokens/mes
                daily_calls=500000,         # 500K llamadas/día
                api_calls_per_minute=500,   # 500 llamadas/minuto
                storage_days=90             # 90 días de retención
            ),
            features=[
                "Agentes ilimitados (hasta 100 concurrentes)",
                "5,000,000 tokens/mes",
                "Todas las métricas",
                "90 días de retención de datos",
                "Advanced tracing",
                "A/B testing",
                "Custom dashboards",
                "Slack/Teams integrations",
                "SSO básico",
                "Soporte dedicado"
            ],
            is_active=True,
            created_at=datetime.now()
        ),
        PlanTier.ENTERPRISE: Plan(
            id="plan-enterprise",
            name="Enterprise Tier",
            tier=PlanTier.ENTERPRISE,
            price_monthly=None,  # Custom pricing
            price_yearly=None,
            limits=PlanLimits(
                concurrent_agents=999999,   # Ilimitado
                monthly_tokens=999999999,   # Ilimitado
                daily_calls=9999999,        # Ilimitado
                api_calls_per_minute=10000, # Muy alto
                storage_days=365            # 1 año de retención
            ),
            features=[
                "Todo ilimitado",
                "Enterprise security",
                "Data residency",
                "Compliance certifications (SOC 2, HIPAA, GDPR)",
                "Dedicated support",
                "Custom SLA",
                "On-premise deployment",
                "White-label solution",
                "Custom integrations",
                "Account manager"
            ],
            is_active=True,
            created_at=datetime.now()
        )
    }
    
    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379):
        """
        Inicializar el gestor de planes
        
        Args:
            redis_host: Host de Redis para tracking
            redis_port: Puerto de Redis
        """
        self.redis = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        self.plans: Dict[PlanTier, Plan] = self.DEFAULT_PLANS.copy()
        
        # Keys de Redis
        self.USAGE_PREFIX = "apanel:usage:"
        self.LIMITS_PREFIX = "apanel:limits:"
        self.ALERTS_PREFIX = "apanel:alerts:"
    
    def get_plan(self, tier: PlanTier) -> Plan:
        """Obtener un plan por su tier"""
        return self.plans.get(tier)
    
    def get_all_plans(self) -> List[Plan]:
        """Obtener todos los planes activos"""
        return [plan for plan in self.plans.values() if plan.is_active]
    
    def get_plan_by_id(self, plan_id: str) -> Optional[Plan]:
        """Obtener un plan por su ID"""
        for plan in self.plans.values():
            if plan.id == plan_id:
                return plan
        return None
    
    def check_concurrent_limit(self, organization_id: str, plan_tier: PlanTier) -> Tuple[bool, str]:
        """
        Verificar límite de concurrencia de agentes
        
        Args:
            organization_id: ID de la organización
            plan_tier: Tier del plan de la organización
            
        Returns:
            (permitido, mensaje)
        """
        plan = self.get_plan(plan_tier)
        if not plan:
            return False, "Plan no encontrado"
        
        key = f"{self.USAGE_PREFIX}{organization_id}:concurrent_agents"
        current = self.redis.incr(key)
        
        # Expira la key en 1 hora (asumiendo que se decremente cuando el agente termine)
        self.redis.expire(key, 3600)
        
        if current > plan.limits.concurrent_agents:
            self.redis.decr(key)  # Decrementar porque excedió
            return False, f"Límite de {plan.limits.concurrent_agents} agentes concurrentes excedido"
        
        return True, f"Agentes concurrentes: {current}/{plan.limits.concurrent_agents}"
    
    def release_concurrent_agent(self, organization_id: str):
        """Liberar un slot de agente concurrente"""
        key = f"{self.USAGE_PREFIX}{organization_id}:concurrent_agents"
        self.redis.decr(key)
    
    def check_monthly_token_limit(self, organization_id: str, plan_tier: PlanTier, tokens_to_add: int) -> Tuple[bool, str]:
        """
        Verificar límite de tokens mensuales
        
        Args:
            organization_id: ID de la organización
            plan_tier: Tier del plan
            tokens_to_add: Tokens a agregar al uso actual
            
        Returns:
            (permitido, mensaje)
        """
        plan = self.get_plan(plan_tier)
        if not plan:
            return False, "Plan no encontrado"
        
        # Key con el mes actual para reset automático
        current_month = datetime.now().strftime("%Y-%m")
        key = f"{self.USAGE_PREFIX}{organization_id}:tokens:{current_month}"
        
        current = int(self.redis.get(key) or 0)
        projected = current + tokens_to_add
        
        if projected > plan.limits.monthly_tokens:
            return False, f"Límite de {plan.limits.monthly_tokens:,} tokens/mes excedido (actual: {current:,}, intento: {tokens_to_add:,})"
        
        # Actualizar uso
        self.redis.set(key, projected, ex=2592000)  # 30 días TTL
        
        return True, f"Tokens usados: {projected:,}/{plan.limits.monthly_tokens:,}"
    
    def check_daily_call_limit(self, organization_id: str, plan_tier: PlanTier) -> Tuple[bool, str]:
        """Verificar límite de llamadas diarias"""
        plan = self.get_plan(plan_tier)
        if not plan:
            return False, "Plan no encontrado"
        
        today = datetime.now().strftime("%Y-%m-%d")
        key = f"{self.USAGE_PREFIX}{organization_id}:calls:{today}"
        
        current = self.redis.incr(key)
        self.redis.expire(key, 86400)  # 1 día TTL
        
        if current > plan.limits.daily_calls:
            self.redis.decr(key)
            return False, f"Límite de {plan.limits.daily_calls:,} llamadas/día excedido"
        
        return True, f"Llamadas hoy: {current:,}/{plan.limits.daily_calls:,}"
    
    def check_api_rate_limit(self, organization_id: str, plan_tier: PlanTier) -> Tuple[bool, str]:
        """Verificar rate limiting de API"""
        plan = self.get_plan(plan_tier)
        if not plan:
            return False, "Plan no encontrado"
        
        # Sliding window rate limiting
        key = f"{self.USAGE_PREFIX}{organization_id}:api_rate"
        
        # Agregar timestamp actual
        now = time.time()
        self.redis.zadd(key, {str(now): now})
        
        # Remover timestamps viejos (> 1 minuto)
        one_minute_ago = now - 60
        self.redis.zremrangebyscore(key, 0, one_minute_ago)
        
        # Contar requests en el último minuto
        count = self.redis.zcard(key)
        self.redis.expire(key, 120)
        
        if count > plan.limits.api_calls_per_minute:
            return False, f"Rate limit excedido: {count}/{plan.limits.api_calls_per_minute} requests/minuto"
        
        return True, f"API calls/minuto: {count}/{plan.limits.api_calls_per_minute}"
    
    def get_usage_stats(self, organization_id: str, plan_tier: PlanTier) -> UsageStats:
        """Obtener estadísticas de uso actuales"""
        plan = self.get_plan(plan_tier)
        
        # Agentes concurrentes
        concurrent_key = f"{self.USAGE_PREFIX}{organization_id}:concurrent_agents"
        current_concurrent = int(self.redis.get(concurrent_key) or 0)
        
        # Tokens mensuales
        current_month = datetime.now().strftime("%Y-%m")
        tokens_key = f"{self.USAGE_PREFIX}{organization_id}:tokens:{current_month}"
        monthly_tokens = int(self.redis.get(tokens_key) or 0)
        
        # Llamadas diarias
        today = datetime.now().strftime("%Y-%m-%d")
        calls_key = f"{self.USAGE_PREFIX}{organization_id}:calls:{today}"
        daily_calls = int(self.redis.get(calls_key) or 0)
        
        # API rate
        api_key = f"{self.USAGE_PREFIX}{organization_id}:api_rate"
        api_count = self.redis.zcard(api_key)
        
        # Storage days (asumimos que usan el máximo de su plan)
        storage_days = plan.limits.storage_days
        
        return UsageStats(
            current_concurrent_agents=current_concurrent,
            monthly_tokens_used=monthly_tokens,
            daily_calls=daily_calls,
            api_calls_last_minute=api_count,
            storage_days_used=storage_days
        )
    
    def get_limit_status(self, organization_id: str, plan_tier: PlanTier, next_billing_date: Optional[datetime] = None) -> LimitStatus:
        """
        Obtener estado completo de límites con alertas y sugerencias
        
        Args:
            organization_id: ID de la organización
            plan_tier: Tier del plan actual
            next_billing_date: Fecha del próximo billing (opcional)
            
        Returns:
            LimitStatus con información completa
        """
        plan = self.get_plan(plan_tier)
        usage = self.get_usage_stats(organization_id, plan_tier)
        
        limits_exceeded = []
        warnings = []
        suggestions = []
        is_over_limit = False
        
        # Verificar concurrencia
        if usage.current_concurrent_agents >= plan.limits.concurrent_agents:
            limits_exceeded.append("concurrent_agents")
            is_over_limit = True
        elif usage.current_concurrent_agents >= plan.limits.concurrent_agents * 0.8:
            warnings.append(f"Concurrencia cerca del límite: {usage.current_concurrent_agents}/{plan.limits.concurrent_agents}")
        
        # Verificar tokens
        if usage.monthly_tokens_used >= plan.limits.monthly_tokens:
            limits_exceeded.append("monthly_tokens")
            is_over_limit = True
        elif usage.monthly_tokens_used >= plan.limits.monthly_tokens * 0.8:
            warnings.append(f"Tokens cerca del límite mensual: {usage.monthly_tokens_used:,}/{plan.limits.monthly_tokens:,}")
        
        # Verificar llamadas diarias
        if usage.daily_calls >= plan.limits.daily_calls:
            limits_exceeded.append("daily_calls")
            is_over_limit = True
        elif usage.daily_calls >= plan.limits.daily_calls * 0.8:
            warnings.append(f"Llamadas cerca del límite diario: {usage.daily_calls:,}/{plan.limits.daily_calls:,}")
        
        # Generar sugerencias de upgrade
        if is_over_limit or warnings:
            next_tier = self._get_next_tier(plan_tier)
            if next_tier:
                next_plan = self.get_plan(next_tier)
                suggestions.append(
                    f"Considera hacer upgrade a {next_plan.name} para tener "
                    f"hasta {next_plan.limits.concurrent_agents} agentes concurrentes y "
                    f"{next_plan.limits.monthly_tokens:,} tokens/mes"
                )
        
        # Sugerencia de plan anual (ahorro)
        if plan.price_yearly and plan.price_monthly:
            monthly_yearly = plan.price_yearly / 12
            if monthly_yearly < plan.price_monthly * 0.9:  # 10% de descuento o más
                suggestions.append(
                    f"Ahorra un {(1 - monthly_yearly/plan.price_monthly)*100:.0f}% "
                    f"con el plan anual (${plan.price_yearly}/año vs ${plan.price_monthly*12:.0f}/año mensual)"
                )
        
        return LimitStatus(
            plan_id=plan.id,
            plan_name=plan.name,
            tier=plan.tier,
            limits=plan.limits,
            usage=usage,
            is_over_limit=is_over_limit,
            limits_exceeded=limits_exceeded,
            warnings=warnings,
            suggestions=suggestions,
            next_billing_date=next_billing_date
        )
    
    def _get_next_tier(self, current_tier: PlanTier) -> Optional[PlanTier]:
        """Obtener el siguiente tier disponible"""
        tier_order = [PlanTier.FREE, PlanTier.PRO, PlanTier.TEAM, PlanTier.ENTERPRISE]
        try:
            current_index = tier_order.index(current_tier)
            if current_index < len(tier_order) - 1:
                return tier_order[current_index + 1]
        except ValueError:
            pass
        return None
    
    def record_token_usage(self, organization_id: str, plan_tier: PlanTier, tokens: int):
        """Registrar uso de tokens (llamado después de cada invocación)"""
        current_month = datetime.now().strftime("%Y-%m")
        key = f"{self.USAGE_PREFIX}{organization_id}:tokens:{current_month}"
        self.redis.incrby(key, tokens)
        self.redis.expire(key, 2592000)  # 30 días TTL
    
    def record_api_call(self, organization_id: str, plan_tier: PlanTier):
        """Registrar una llamada a la API"""
        today = datetime.now().strftime("%Y-%m-%d")
        key = f"{self.USAGE_PREFIX}{organization_id}:calls:{today}"
        self.redis.incr(key)
        self.redis.expire(key, 86400)  # 1 día TTL


# Singleton instance
_plans_manager_instance = None

def get_plans_manager(redis_host: str = "localhost", redis_port: int = 6379) -> PlansManager:
    """Obtener instancia singleton del PlansManager"""
    global _plans_manager_instance
    if _plans_manager_instance is None:
        _plans_manager_instance = PlansManager(redis_host, redis_port)
    return _plans_manager_instance


if __name__ == "__main__":
    # Test del sistema
    print("📊 Sistema de Planes y Límites - APanel")
    print("=" * 50)
    
    manager = PlansManager()
    
    # Mostrar planes
    print("\n📋 Planes disponibles:")
    for plan in manager.get_all_plans():
        print(f"\n{plan.name} (${plan.price_monthly}/mes)")
        print(f"  - Agentes: {plan.limits.concurrent_agents}")
        print(f"  - Tokens: {plan.limits.monthly_tokens:,}")
        print(f"  - Llamadas/día: {plan.limits.daily_calls:,}")
        print(f"  - Storage: {plan.limits.storage_days} días")
    
    # Test de límites
    org_id = "test-org-123"
    
    print(f"\n🧪 Test de límites para {org_id}:")
    
    # Test concurrencia
    allowed, msg = manager.check_concurrent_limit(org_id, PlanTier.PRO)
    print(f"  Concurrencia: {msg}")
    
    # Test tokens
    allowed, msg = manager.check_monthly_token_limit(org_id, PlanTier.PRO, 1000)
    print(f"  Tokens: {msg}")
    
    # Test rate limiting
    allowed, msg = manager.check_api_rate_limit(org_id, PlanTier.PRO)
    print(f"  API Rate: {msg}")
    
    # Estado completo
    status = manager.get_limit_status(org_id, PlanTier.PRO, next_billing_date=datetime.now() + timedelta(days=30))
    print(f"\n📊 Estado completo:")
    print(f"  Plan: {status.plan_name}")
    print(f"  Sobre límite: {status.is_over_limit}")
    print(f"  Alertas: {len(status.warnings)}")
    print(f"  Sugerencias: {len(status.suggestions)}")
    
    if status.suggestions:
        print(f"\n💡 Sugerencias:")
        for suggestion in status.suggestions:
            print(f"  - {suggestion}")
