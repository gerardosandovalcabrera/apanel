"""
💰 Billing Integration Module - APanel
Integración entre Cost Tracking y Plans & Limits

Basado en la arquitectura de Helicone:
- Real-time cost tracking
- Budget alerts
- Token usage monitoring
- Cost optimization suggestions

Autor: Hermes Agent System
Basado en: Helicone (Apache 2.0)
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
    PlansManager,
    PlanTier,
    UsageStats,
    LimitStatus,
    get_plans_manager
)


@dataclass
class BudgetAlert:
    """Alerta de presupuesto"""
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
    """Métrica de costo en tiempo real"""
    timestamp: datetime
    organization_id: str
    provider_model_id: str
    cost: Decimal
    tokens: int
    cost_per_1k_tokens: Decimal
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class BudgetConfig:
    """Configuración de presupuesto"""
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


class BillingIntegration:
    """
    Integración entre Cost Tracking y Plans & Limits
    
    Features:
    - Real-time cost tracking
    - Budget monitoring
    - Alert system
    - Cost optimization
    - Token usage analytics
    """
    
    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379):
        self.cost_calculator = get_calculator()
        self.plans_manager = PlansManager(redis_host, redis_port)
        
        # Almacenamiento en memoria (en producción usar Redis/DB)
        self.cost_metrics: Dict[str, List[CostMetric]] = {}
        self.budgets: Dict[str, BudgetConfig] = {}
        self.alerts: Dict[str, List[BudgetAlert]] = {}
    
    def record_api_call(
        self,
        organization_id: str,
        provider_model_id: str,
        prompt_tokens: int,
        completion_tokens: int,
        prompt_cache_write_tokens: int = 0,
        prompt_cache_read_tokens: int = 0,
        additional_usage: Optional[ModelUsage] = None
    ) -> Tuple[CostBreakdown, bool]:
        """
        Registrar una llamada a la API y verificar límites
        
        Returns:
            (cost_breakdown, within_limits)
        """
        # Calcular costo
        if additional_usage:
            usage = additional_usage
        else:
            usage = ModelUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                prompt_cache_write_tokens=prompt_cache_write_tokens,
                prompt_cache_read_tokens=prompt_cache_read_tokens
            )
        
        cost_breakdown = self.cost_calculator.calculate_cost(provider_model_id, usage)
        
        if not cost_breakdown:
            # Si no se puede calcular, asumir costo 0
            cost_breakdown = CostBreakdown(
                total_cost=Decimal('0'),
                prompt_cost=Decimal('0'),
                completion_cost=Decimal('0'),
                total_tokens=usage.total_tokens()
            )
        
        # Registrar métrica de costo
        metric = CostMetric(
            timestamp=datetime.now(),
            organization_id=organization_id,
            provider_model_id=provider_model_id,
            cost=cost_breakdown.total_cost,
            tokens=cost_breakdown.total_tokens,
            cost_per_1k_tokens=float(cost_breakdown.total_cost) / (cost_breakdown.total_tokens / 1000) 
                               if cost_breakdown.total_tokens > 0 else Decimal('0')
        )
        
        if organization_id not in self.cost_metrics:
            self.cost_metrics[organization_id] = []
        
        self.cost_metrics[organization_id].append(metric)
        
        # Verificar límites de tokens con el plans manager
        # (asumimos Pro tier para demo, en producción viene de DB)
        plan_tier = PlanTier.PRO
        
        # Verificar límite de tokens mensuales
        tokens_allowed, tokens_message = self.plans_manager.check_monthly_token_limit(
            organization_id,
            plan_tier,
            cost_breakdown.total_tokens
        )
        
        # Registrar uso de tokens en el plans manager
        self.plans_manager.record_token_usage(
            organization_id,
            plan_tier,
            cost_breakdown.total_tokens
        )
        
        # Verificar presupuesto
        if organization_id in self.budgets:
            self._check_budget_alerts(organization_id, cost_breakdown.total_cost)
        
        return cost_breakdown, tokens_allowed
    
    def get_cost_summary(
        self,
        organization_id: str,
        time_range: str = "month"  # "day", "week", "month", "year"
    ) -> Dict:
        """
        Obtener resumen de costos para una organización
        
        Args:
            organization_id: ID de la organización
            time_range: Rango de tiempo
            
        Returns:
            Diccionario con resumen de costos
        """
        if organization_id not in self.cost_metrics:
            return {
                "total_cost": 0.0,
                "total_tokens": 0,
                "calls_count": 0,
                "avg_cost_per_call": 0.0,
                "cost_by_model": {},
                "tokens_by_model": {},
                "time_range": time_range
            }
        
        # Filtrar métricas por rango de tiempo
        now = datetime.now()
        if time_range == "day":
            start_time = now - timedelta(days=1)
        elif time_range == "week":
            start_time = now - timedelta(weeks=1)
        elif time_range == "month":
            start_time = now - timedelta(days=30)
        elif time_range == "year":
            start_time = now - timedelta(days=365)
        else:
            start_time = datetime.min
        
        filtered_metrics = [
            m for m in self.cost_metrics[organization_id]
            if m.timestamp >= start_time
        ]
        
        if not filtered_metrics:
            return {
                "total_cost": 0.0,
                "total_tokens": 0,
                "calls_count": 0,
                "avg_cost_per_call": 0.0,
                "cost_by_model": {},
                "tokens_by_model": {},
                "time_range": time_range
            }
        
        # Calcular totales
        total_cost = sum(m.cost for m in filtered_metrics)
        total_tokens = sum(m.tokens for m in filtered_metrics)
        calls_count = len(filtered_metrics)
        avg_cost_per_call = total_cost / calls_count if calls_count > 0 else Decimal('0')
        
        # Agrupar por modelo
        cost_by_model: Dict[str, Decimal] = {}
        tokens_by_model: Dict[str, int] = {}
        
        for metric in filtered_metrics:
            model = metric.provider_model_id
            if model not in cost_by_model:
                cost_by_model[model] = Decimal('0')
                tokens_by_model[model] = 0
            
            cost_by_model[model] += metric.cost
            tokens_by_model[model] += metric.tokens
        
        # Ordenar por costo
        cost_by_model = dict(sorted(cost_by_model.items(), key=lambda x: x[1], reverse=True))
        tokens_by_model = dict(sorted(tokens_by_model.items(), key=lambda x: x[1], reverse=True))
        
        return {
            "total_cost": float(total_cost),
            "total_tokens": total_tokens,
            "calls_count": calls_count,
            "avg_cost_per_call": float(avg_cost_per_call),
            "cost_by_model": {k: float(v) for k, v in cost_by_model.items()},
            "tokens_by_model": tokens_by_model,
            "time_range": time_range,
            "start_date": start_time.isoformat(),
            "end_date": now.isoformat()
        }
    
    def create_budget(
        self,
        organization_id: str,
        name: str,
        monthly_budget: Decimal,
        alert_thresholds: Optional[List[float]] = None,
        currency: str = "USD"
    ) -> BudgetConfig:
        """Crear un presupuesto para una organización"""
        budget_id = f"{organization_id}_{name.lower().replace(' ', '_')}"
        
        if alert_thresholds is None:
            alert_thresholds = [0.5, 0.8, 1.0]  # 50%, 80%, 100%
        
        budget = BudgetConfig(
            budget_id=budget_id,
            organization_id=organization_id,
            name=name,
            monthly_budget=monthly_budget,
            alert_thresholds=alert_thresholds,
            currency=currency,
            alert_enabled=True,
            email_alerts=True
        )
        
        self.budgets[budget_id] = budget
        
        return budget
    
    def _check_budget_alerts(self, organization_id: str, additional_cost: Decimal):
        """Verificar si se deben generar alertas de presupuesto"""
        budget = self.budgets.get(organization_id)
        
        if not budget or not budget.alert_enabled:
            return
        
        # Calcular costo actual del mes
        cost_summary = self.get_cost_summary(organization_id, "month")
        current_spent = Decimal(str(cost_summary["total_cost"])) + additional_cost
        
        # Verificar cada threshold
        for threshold in budget.alert_thresholds:
            budget_limit = budget.monthly_budget * Decimal(str(threshold))
            
            if current_spent >= budget_limit:
                # Verificar si ya existe una alerta para este threshold
                alert_id = f"{budget.budget_id}_{threshold}"
                
                existing_alerts = self.alerts.get(budget.budget_id, [])
                if not any(a.alert_id == alert_id for a in existing_alerts):
                    # Crear nueva alerta
                    percentage = (current_spent / budget.monthly_budget) * 100
                    
                    if percentage >= 100:
                        alert_type = "exceeded"
                        message = f"❌ Presupuesto excedido: ${current_spent:.2f} / ${budget.monthly_budget:.2f} ({percentage:.1f}%)"
                    elif percentage >= 80:
                        alert_type = "critical"
                        message = f"⚠️ Crítico: Casi excedes el presupuesto: ${current_spent:.2f} / ${budget.monthly_budget:.2f} ({percentage:.1f}%)"
                    else:
                        alert_type = "warning"
                        message = f"ℹ️ Info: Has usado el {percentage:.1f}% de tu presupuesto: ${current_spent:.2f} / ${budget.monthly_budget:.2f}"
                    
                    alert = BudgetAlert(
                        alert_id=alert_id,
                        alert_type=alert_type,
                        budget_id=budget.budget_id,
                        current_spent=current_spent,
                        budget_limit=budget.monthly_budget,
                        percentage_used=percentage,
                        message=message,
                        timestamp=datetime.now()
                    )
                    
                    if budget.budget_id not in self.alerts:
                        self.alerts[budget.budget_id] = []
                    
                    self.alerts[budget.budget_id].append(alert)
                    
                    # Aquí se enviarían notificaciones (email, webhook, etc.)
                    print(f"\n🔔 ALERTA DE PRESUPUESTO: {message}")
    
    def get_budget_status(self, organization_id: str) -> Optional[Dict]:
        """Obtener estado del presupuesto de una organización"""
        budget = self.budgets.get(organization_id)
        
        if not budget:
            return None
        
        cost_summary = self.get_cost_summary(organization_id, "month")
        current_spent = Decimal(str(cost_summary["total_cost"]))
        
        percentage_used = (current_spent / budget.monthly_budget) * 100 if budget.monthly_budget > 0 else 0
        remaining = budget.monthly_budget - current_spent
        
        # Obtener alertas recientes
        recent_alerts = self.alerts.get(budget.budget_id, [])
        recent_alerts = [a for a in recent_alerts if a.timestamp > datetime.now() - timedelta(days=7)]
        
        return {
            "budget_id": budget.budget_id,
            "name": budget.name,
            "monthly_budget": float(budget.monthly_budget),
            "current_spent": float(current_spent),
            "remaining": float(remaining),
            "percentage_used": percentage_used,
            "currency": budget.currency,
            "alerts": [a.to_dict() for a in recent_alerts],
            "alert_enabled": budget.alert_enabled
        }
    
    def get_billing_summary(self, organization_id: str, plan_tier: PlanTier) -> Dict:
        """
        Obtener resumen completo de billing
        Combina cost tracking con plans & limits
        """
        # Obtener cost summary
        cost_summary = self.get_cost_summary(organization_id, "month")
        
        # Obtener limit status
        limit_status = self.plans_manager.get_limit_status(organization_id, plan_tier)
        
        # Obtener budget status
        budget_status = self.get_budget_status(organization_id)
        
        # Obtener optimizaciones
        optimizations = self._get_cost_optimizations(organization_id)
        
        return {
            "cost_summary": cost_summary,
            "limit_status": limit_status.to_dict() if limit_status else None,
            "budget_status": budget_status,
            "optimizations": optimizations,
            "generated_at": datetime.now().isoformat()
        }
    
    def _get_cost_optimizations(self, organization_id: str) -> List[Dict]:
        """Obtener sugerencias de optimización de costos"""
        if organization_id not in self.cost_metrics:
            return []
        
        cost_summary = self.get_cost_summary(organization_id, "month")
        cost_by_model = cost_summary["cost_by_model"]
        
        optimizations = []
        
        # Sugerir modelos más baratos
        if len(cost_by_model) > 1:
            # Encontrar el modelo más caro
            most_expensive_model = max(cost_by_model.items(), key=lambda x: x[1])
            
            # Encontrar el modelo más barato
            cheapest_model = min(cost_by_model.items(), key=lambda x: x[1])
            
            if most_expensive_model[1] > cheapest_model[1] * 2:
                savings = most_expensive_model[1] - cheapest_model[1]
                optimizations.append({
                    "type": "model_switch",
                    "priority": "high",
                    "suggestion": f"Considera cambiar de {most_expensive_model[0]} a {cheapest_model[0]}",
                    "potential_savings": savings,
                    "potential_savings_percentage": (savings / most_expensive_model[1]) * 100
                })
        
        # Sugerir caching si hay muchos tokens de prompt repetidos
        total_tokens = cost_summary["total_tokens"]
        if total_tokens > 100000:
            optimizations.append({
                "type": "enable_caching",
                "priority": "medium",
                "suggestion": "Habilita prompt caching para reducir costos de tokens repetidos",
                "potential_savings": total_tokens * 0.1,  # 10% de ahorro estimado
                "potential_savings_percentage": 10.0
            })
        
        return optimizations


# Singleton instance
_billing_integration_instance = None

def get_billing_integration(redis_host: str = "localhost", redis_port: int = 6379) -> BillingIntegration:
    """Obtener instancia singleton del BillingIntegration"""
    global _billing_integration_instance
    if _billing_integration_instance is None:
        _billing_integration_instance = BillingIntegration(redis_host, redis_port)
    return _billing_integration_instance


if __name__ == "__main__":
    # Demo de la integración
    print("💰 Billing Integration - APanel")
    print("=" * 60)
    
    billing = get_billing_integration()
    
    # Simular algunas llamadas a la API
    print("\n📞 Simulando llamadas a la API...")
    print("-" * 60)
    
    org_id = "demo-org-billing"
    models = ["openai/gpt-4o", "openai/gpt-4o-mini", "anthropic/claude-3.5-sonnet"]
    
    total_cost = Decimal('0')
    
    for i in range(5):
        model = models[i % len(models)]
        prompt_tokens = 1000 + (i * 200)
        completion_tokens = 500 + (i * 100)
        
        cost_breakdown, within_limits = billing.record_api_call(
            organization_id=org_id,
            provider_model_id=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens
        )
        
        total_cost += cost_breakdown.total_cost
        
        status = "✅" if within_limits else "❌"
        print(f"{status} Llamada {i+1}: {model}")
        print(f"   Tokens: {prompt_tokens} + {completion_tokens} = {cost_breakdown.total_tokens}")
        print(f"   Costo: ${cost_breakdown.total_cost:.6f}")
        print()
    
    print(f"\n💰 Costo total: ${total_cost:.6f}")
    
    # Crear presupuesto
    print("\n💵 Creando presupuesto...")
    print("-" * 60)
    
    budget = billing.create_budget(
        organization_id=org_id,
        name="Demo Budget",
        monthly_budget=Decimal('10.00'),  # $10/mes
        alert_thresholds=[0.5, 0.8, 1.0]
    )
    
    print(f"Presupuesto creado: {budget.name}")
    print(f"Límite mensual: ${budget.monthly_budget:.2f}")
    print(f"Alertas: {budget.alert_thresholds}")
    
    # Verificar estado del presupuesto
    print("\n📊 Estado del presupuesto:")
    print("-" * 60)
    
    budget_status = billing.get_budget_status(org_id)
    if budget_status:
        print(f"Presupuesto: ${budget_status['current_spent']:.2f} / ${budget_status['monthly_budget']:.2f}")
        print(f"Porcentaje usado: {budget_status['percentage_used']:.1f}%")
        print(f"Restante: ${budget_status['remaining']:.2f}")
        
        if budget_status['alerts']:
            print(f"\nAlertas: {len(budget_status['alerts'])}")
            for alert in budget_status['alerts']:
                print(f"  {alert['alert_type'].upper()}: {alert['message']}")
    
    # Obtener resumen de billing
    print("\n📋 Resumen completo de billing:")
    print("-" * 60)
    
    billing_summary = billing.get_billing_summary(org_id, PlanTier.PRO)
    
    cost_summary = billing_summary['cost_summary']
    print(f"\n💸 Costos del mes:")
    print(f"  Total: ${cost_summary['total_cost']:.6f}")
    print(f"  Tokens: {cost_summary['total_tokens']:,}")
    print(f"  Llamadas: {cost_summary['calls_count']}")
    print(f"  Promedio por llamada: ${cost_summary['avg_cost_per_call']:.6f}")
    
    if cost_summary['cost_by_model']:
        print(f"\n  Costos por modelo:")
        for model, cost in cost_summary['cost_by_model'].items():
            print(f"    {model}: ${cost:.6f}")
    
    # Optimizaciones
    if billing_summary['optimizations']:
        print(f"\n💡 Sugerencias de optimización:")
        for opt in billing_summary['optimizations']:
            print(f"  • {opt['suggestion']}")
            print(f"    Ahorro potencial: ${opt['potential_savings']:.6f} ({opt['potential_savings_percentage']:.1f}%)")
    
    print("\n✅ Demo completada exitosamente!")
