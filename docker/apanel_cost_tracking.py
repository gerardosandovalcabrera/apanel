"""
💰 Cost Tracking Module - APanel
Based on Helicone architecture

This module implements:
1. Model Registry with O(1) lookups
2. Cost Calculation Engine
3. Multi-provider support (OpenAI, Anthropic, etc.)
4. Token counting by type
5. Automatic price updates
6. Detailed cost breakdown

Author: Hermes Agent System
Based on: Helicone (Apache 2.0)
"""

from dataclasses import dataclass, asdict
from typing import Dict, Optional, Tuple
from enum import Enum
import json
from datetime import datetime
from decimal import Decimal


class ProviderName(Enum):
    """Supported provider names"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    COHERE = "cohere"
    MISTRAL = "mistral"
    AZURE = "azure"


class TokenType(Enum):
    """Token types with different prices"""
    PROMPT = "prompt"                    # Input tokens
    COMPLETION = "completion"            # Output tokens
    PROMPT_CACHE_WRITE = "prompt_cache_write"  # Cache write (new)
    PROMPT_CACHE_READ = "prompt_cache_read"    # Cache read
    IMAGE = "image"                      # Images (DALL-E)
    AUDIO_INPUT = "audio_input"          # Whisper
    AUDIO_OUTPUT = "audio_output"        # TTS


@dataclass
class ModelPricing:
    """Prices for a model by token type"""
    prompt_price_per_1k: Decimal        # Price per 1000 prompt tokens
    completion_price_per_1k: Decimal    # Price per 1000 completion tokens
    prompt_cache_write_price_per_1k: Optional[Decimal] = None  # Cache write
    prompt_cache_read_price_per_1k: Optional[Decimal] = None   # Cache read
    image_price_per_1k: Optional[Decimal] = None
    audio_input_price_per_1k: Optional[Decimal] = None
    audio_output_price_per_1k: Optional[Decimal] = None
    per_call_price: Optional[Decimal] = None  # Fixed price per call
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ModelConfig:
    """Complete configuration for a model"""
    provider_model_id: str          # "openai/gpt-4"
    provider: ProviderName          # "openai"
    display_name: str               # "GPT-4"
    pricing: ModelPricing
    context_length: int             # 128000 (maximum context tokens)
    max_completion_tokens: int      # 4096 (maximum response tokens)
    supports_function_calling: bool = False
    supports_vision: bool = False
    supports_audio: bool = False
    supports_cache: bool = False
    deprecated: bool = False
    version: str = "v1"
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['provider'] = self.provider.value
        data['pricing'] = self.pricing.to_dict()
        return data


@dataclass
class CostBreakdown:
    """Desglose detallado de costos"""
    total_cost: Decimal
    prompt_cost: Decimal
    completion_cost: Decimal
    prompt_cache_write_cost: Decimal = Decimal('0')
    prompt_cache_read_cost: Decimal = Decimal('0')
    image_cost: Decimal = Decimal('0')
    audio_input_cost: Decimal = Decimal('0')
    audio_output_cost: Decimal = Decimal('0')
    per_call_cost: Decimal = Decimal('0')
    total_tokens: int = 0
    currency: str = "USD"
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ModelUsage:
    """Uso de un modelo para cálculo de costos"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    prompt_cache_write_tokens: int = 0
    prompt_cache_read_tokens: int = 0
    image_count: int = 0
    audio_input_tokens: int = 0
    audio_output_tokens: int = 0
    per_call_count: int = 0
    
    def total_tokens(self) -> int:
        """Calcular total de tokens"""
        return (self.prompt_tokens + self.completion_tokens + 
                self.prompt_cache_write_tokens + self.prompt_cache_read_tokens +
                self.audio_input_tokens + self.audio_output_tokens)
    
    def to_dict(self) -> Dict:
        return asdict(self)


class ModelRegistry:
    """
    Registro de modelos con O(1) lookups
    
    Basado en la arquitectura de Helicone:
    - Indexado por provider_model_id para acceso rápido
    - Soporta múltiples providers
    - Type-safe con dataclasses
    - Actualizable dinámicamente
    """
    
    def __init__(self):
        # Index principal: provider_model_id -> ModelConfig
        self._models: Dict[str, ModelConfig] = {}
        
        # Index por provider: provider -> [ModelConfig]
        self._provider_index: Dict[ProviderName, Dict[str, ModelConfig]] = {}
        
        # Inicializar con modelos populares
        self._initialize_models()
    
    def _initialize_models(self):
        """Inicializar el registro con modelos populares"""
        
        # === OPENAI MODELS ===
        self._register_model(ModelConfig(
            provider_model_id="openai/gpt-4",
            provider=ProviderName.OPENAI,
            display_name="GPT-4",
            pricing=ModelPricing(
                prompt_price_per_1k=Decimal('30.00'),
                completion_price_per_1k=Decimal('60.00'),
                per_call_price=Decimal('0.03')
            ),
            context_length=8192,
            max_completion_tokens=4096,
            supports_function_calling=True
        ))
        
        self._register_model(ModelConfig(
            provider_model_id="openai/gpt-4-turbo",
            provider=ProviderName.OPENAI,
            display_name="GPT-4 Turbo",
            pricing=ModelPricing(
                prompt_price_per_1k=Decimal('10.00'),
                completion_price_per_1k=Decimal('30.00'),
                prompt_cache_write_price_per_1k=Decimal('10.00'),
                prompt_cache_read_price_per_1k=Decimal('0.60')
            ),
            context_length=128000,
            max_completion_tokens=4096,
            supports_function_calling=True,
            supports_vision=True,
            supports_cache=True
        ))
        
        self._register_model(ModelConfig(
            provider_model_id="openai/gpt-3.5-turbo",
            provider=ProviderName.OPENAI,
            display_name="GPT-3.5 Turbo",
            pricing=ModelPricing(
                prompt_price_per_1k=Decimal('0.50'),
                completion_price_per_1k=Decimal('1.50'),
                prompt_cache_write_price_per_1k=Decimal('0.50'),
                prompt_cache_read_price_per_1k=Decimal('0.30')
            ),
            context_length=16385,
            max_completion_tokens=4096,
            supports_function_calling=True,
            supports_cache=True
        ))
        
        self._register_model(ModelConfig(
            provider_model_id="openai/gpt-4o",
            provider=ProviderName.OPENAI,
            display_name="GPT-4o",
            pricing=ModelPricing(
                prompt_price_per_1k=Decimal('5.00'),
                completion_price_per_1k=Decimal('15.00'),
                prompt_cache_write_price_per_1k=Decimal('5.00'),
                prompt_cache_read_price_per_1k=Decimal('0.30')
            ),
            context_length=128000,
            max_completion_tokens=4096,
            supports_function_calling=True,
            supports_vision=True,
            supports_audio=True,
            supports_cache=True
        ))
        
        self._register_model(ModelConfig(
            provider_model_id="openai/gpt-4o-mini",
            provider=ProviderName.OPENAI,
            display_name="GPT-4o Mini",
            pricing=ModelPricing(
                prompt_price_per_1k=Decimal('0.15'),
                completion_price_per_1k=Decimal('0.60'),
                prompt_cache_write_price_per_1k=Decimal('0.15'),
                prompt_cache_read_price_per_1k=Decimal('0.030')
            ),
            context_length=128000,
            max_completion_tokens=16384,
            supports_function_calling=True,
            supports_vision=True,
            supports_cache=True
        ))
        
        # === ANTHROPIC MODELS ===
        self._register_model(ModelConfig(
            provider_model_id="anthropic/claude-3.5-sonnet",
            provider=ProviderName.ANTHROPIC,
            display_name="Claude 3.5 Sonnet",
            pricing=ModelPricing(
                prompt_price_per_1k=Decimal('3.00'),
                completion_price_per_1k=Decimal('15.00'),
                prompt_cache_write_price_per_1k=Decimal('3.75'),
                prompt_cache_read_price_per_1k=Decimal('0.30')
            ),
            context_length=200000,
            max_completion_tokens=8192,
            supports_function_calling=True,
            supports_cache=True
        ))
        
        self._register_model(ModelConfig(
            provider_model_id="anthropic/claude-3-opus",
            provider=ProviderName.ANTHROPIC,
            display_name="Claude 3 Opus",
            pricing=ModelPricing(
                prompt_price_per_1k=Decimal('15.00'),
                completion_price_per_1k=Decimal('75.00'),
                prompt_cache_write_price_per_1k=Decimal('18.75'),
                prompt_cache_read_price_per_1k=Decimal('1.50')
            ),
            context_length=200000,
            max_completion_tokens=4096,
            supports_function_calling=True,
            supports_vision=True,
            supports_cache=True
        ))
        
        self._register_model(ModelConfig(
            provider_model_id="anthropic/claude-3-haiku",
            provider=ProviderName.ANTHROPIC,
            display_name="Claude 3 Haiku",
            pricing=ModelPricing(
                prompt_price_per_1k=Decimal('0.25'),
                completion_price_per_1k=Decimal('1.25'),
                prompt_cache_write_price_per_1k=Decimal('0.3125'),
                prompt_cache_read_price_per_1k=Decimal('0.025')
            ),
            context_length=200000,
            max_completion_tokens=4096,
            supports_cache=True
        ))
        
        # === GOOGLE MODELS ===
        self._register_model(ModelConfig(
            provider_model_id="google/gemini-1.5-pro",
            provider=ProviderName.GOOGLE,
            display_name="Gemini 1.5 Pro",
            pricing=ModelPricing(
                prompt_price_per_1k=Decimal('3.50'),
                completion_price_per_1k=Decimal('10.50')
            ),
            context_length=2800000,
            max_completion_tokens=8192,
            supports_function_calling=True,
            supports_vision=True
        ))
        
        # === MISTRAL MODELS ===
        self._register_model(ModelConfig(
            provider_model_id="mistral/mistral-large",
            provider=ProviderName.MISTRAL,
            display_name="Mistral Large",
            pricing=ModelPricing(
                prompt_price_per_1k=Decimal('4.00'),
                completion_price_per_1k=Decimal('12.00')
            ),
            context_length=128000,
            max_completion_tokens=4096,
            supports_function_calling=True
        ))
    
    def _register_model(self, config: ModelConfig):
        """Registrar un modelo en el índice"""
        self._models[config.provider_model_id] = config
        
        # Index por provider
        if config.provider not in self._provider_index:
            self._provider_index[config.provider] = {}
        self._provider_index[config.provider][config.provider_model_id] = config
    
    def get_model(self, provider_model_id: str) -> Optional[ModelConfig]:
        """
        Obtener configuración de modelo por ID (O(1) lookup)
        
        Args:
            provider_model_id: ID del modelo (ej: "openai/gpt-4")
            
        Returns:
            ModelConfig o None si no existe
        """
        return self._models.get(provider_model_id)
    
    def get_models_by_provider(self, provider: ProviderName) -> list[ModelConfig]:
        """Obtener todos los modelos de un provider"""
        provider_models = self._provider_index.get(provider, {})
        return list(provider_models.values())
    
    def list_all_models(self) -> list[ModelConfig]:
        """Listar todos los modelos registrados"""
        return list(self._models.values())
    
    def search_models(self, query: str) -> list[ModelConfig]:
        """Buscar modelos por nombre o provider"""
        query_lower = query.lower()
        results = []
        
        for config in self._models.values():
            if (query_lower in config.provider_model_id.lower() or
                query_lower in config.display_name.lower()):
                results.append(config)
        
        return results


class CostCalculator:
    """
    Calculadora de costos basada en la arquitectura de Helicone
    
    Features:
    - Cálculo de costos por tipo de token
    - Multi-provider support
    - Cache token pricing
    - Audio/image pricing
    - Detailed cost breakdown
    """
    
    def __init__(self, registry: Optional[ModelRegistry] = None):
        self.registry = registry or ModelRegistry()
    
    def calculate_cost(
        self,
        provider_model_id: str,
        usage: ModelUsage,
        request_count: int = 1
    ) -> Optional[CostBreakdown]:
        """
        Calcular costo de una llamada a modelo
        
        Args:
            provider_model_id: ID del modelo (ej: "openai/gpt-4")
            usage: Uso del modelo
            request_count: Número de requests (para batch)
            
        Returns:
            CostBreakdown o None si el modelo no existe
        """
        model = self.registry.get_model(provider_model_id)
        if not model:
            return None
        
        pricing = model.pricing
        
        # Calcular costos por tipo de token
        prompt_cost = (Decimal(usage.prompt_tokens) / Decimal('1000')) * pricing.prompt_price_per_1k
        
        completion_cost = (Decimal(usage.completion_tokens) / Decimal('1000')) * pricing.completion_price_per_1k
        
        prompt_cache_write_cost = Decimal('0')
        if pricing.prompt_cache_write_price_per_1k and usage.prompt_cache_write_tokens > 0:
            prompt_cache_write_cost = (Decimal(usage.prompt_cache_write_tokens) / Decimal('1000')) * pricing.prompt_cache_write_price_per_1k
        
        prompt_cache_read_cost = Decimal('0')
        if pricing.prompt_cache_read_price_per_1k and usage.prompt_cache_read_tokens > 0:
            prompt_cache_read_cost = (Decimal(usage.prompt_cache_read_tokens) / Decimal('1000')) * pricing.prompt_cache_read_price_per_1k
        
        # Costos adicionales
        image_cost = Decimal('0')
        if pricing.image_price_per_1k and usage.image_count > 0:
            image_cost = (Decimal(usage.image_count) / Decimal('1000')) * pricing.image_price_per_1k
        
        audio_input_cost = Decimal('0')
        if pricing.audio_input_price_per_1k and usage.audio_input_tokens > 0:
            audio_input_cost = (Decimal(usage.audio_input_tokens) / Decimal('1000')) * pricing.audio_input_price_per_1k
        
        audio_output_cost = Decimal('0')
        if pricing.audio_output_price_per_1k and usage.audio_output_tokens > 0:
            audio_output_cost = (Decimal(usage.audio_output_tokens) / Decimal('1000')) * pricing.audio_output_price_per_1k
        
        per_call_cost = Decimal('0')
        if pricing.per_call_price:
            per_call_cost = Decimal(pricing.per_call_price) * Decimal(request_count)
        
        # Calcular total
        total_cost = (prompt_cost + completion_cost + prompt_cache_write_cost + 
                     prompt_cache_read_cost + image_cost + audio_input_cost + 
                     audio_output_cost + per_call_cost)
        
        return CostBreakdown(
            total_cost=total_cost,
            prompt_cost=prompt_cost,
            completion_cost=completion_cost,
            prompt_cache_write_cost=prompt_cache_write_cost,
            prompt_cache_read_cost=prompt_cache_read_cost,
            image_cost=image_cost,
            audio_input_cost=audio_input_cost,
            audio_output_cost=audio_output_cost,
            per_call_cost=per_call_cost,
            total_tokens=usage.total_tokens(),
            currency="USD"
        )
    
    def estimate_cost(
        self,
        provider_model_id: str,
        estimated_prompt_tokens: int,
        estimated_completion_tokens: int = 0
    ) -> Optional[Dict]:
        """
        Estimar costo antes de hacer la llamada
        
        Útil para budget checks y previews
        """
        usage = ModelUsage(
            prompt_tokens=estimated_prompt_tokens,
            completion_tokens=estimated_completion_tokens
        )
        
        breakdown = self.calculate_cost(provider_model_id, usage)
        if not breakdown:
            return None
        
        return {
            "estimated_cost": float(breakdown.total_cost),
            "prompt_cost": float(breakdown.prompt_cost),
            "completion_cost": float(breakdown.completion_cost),
            "estimated_tokens": breakdown.total_tokens,
            "currency": breakdown.currency
        }
    
    def compare_models(
        self,
        provider_model_ids: list[str],
        prompt_tokens: int,
        completion_tokens: int = 0
    ) -> list[Dict]:
        """
        Comparar costos entre múltiples modelos
        
        Returns:
            Lista ordenada por costo (más barato primero)
        """
        comparisons = []
        
        for model_id in provider_model_ids:
            breakdown = self.calculate_cost(
                model_id,
                ModelUsage(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens)
            )
            
            if breakdown:
                model = self.registry.get_model(model_id)
                cost_per_1k = float(breakdown.total_cost) / (breakdown.total_tokens / 1000) if breakdown.total_tokens > 0 else 0
                comparisons.append({
                    "model_id": model_id,
                    "display_name": model.display_name if model else model_id,
                    "total_cost": float(breakdown.total_cost),
                    "total_tokens": breakdown.total_tokens,
                    "cost_per_1k_tokens": cost_per_1k,
                    "breakdown": breakdown.to_dict()
                })
        
        # Ordenar por costo (más barato primero)
        comparisons.sort(key=lambda x: x["total_cost"])
        
        return comparisons


# Singleton instance
_registry_instance = None
_calculator_instance = None

def get_registry() -> ModelRegistry:
    """Obtener instancia singleton del registro"""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = ModelRegistry()
    return _registry_instance

def get_calculator() -> CostCalculator:
    """Obtener instancia singleton de la calculadora"""
    global _calculator_instance
    if _calculator_instance is None:
        _calculator_instance = CostCalculator(get_registry())
    return _calculator_instance


if __name__ == "__main__":
    # Demo del sistema de costos
    print("💰 Cost Tracking Module - APanel (Basado en Helicone)")
    print("=" * 60)
    
    calculator = get_calculator()
    registry = get_registry()
    
    # Mostrar modelos disponibles
    print("\n📋 Modelos Disponibles:")
    print("-" * 60)
    for model in registry.list_all_models()[:10]:
        print(f"  • {model.display_name:25} | {model.provider_model_id}")
    
    # Calcular costo de una llamada
    print("\n💰 Ejemplo de Cálculo de Costos:")
    print("-" * 60)
    
    usage = ModelUsage(
        prompt_tokens=1000,
        completion_tokens=500,
        prompt_cache_write_tokens=200,
        prompt_cache_read_tokens=300
    )
    
    breakdown = calculator.calculate_cost("openai/gpt-4o", usage)
    
    if breakdown:
        print(f"\nModelo: GPT-4o")
        print(f"  Prompt tokens: {usage.prompt_tokens:,} → ${breakdown.prompt_cost:.6f}")
        print(f"  Completion tokens: {usage.completion_tokens:,} → ${breakdown.completion_cost:.6f}")
        print(f"  Cache write: {usage.prompt_cache_write_tokens:,} → ${breakdown.prompt_cache_write_cost:.6f}")
        print(f"  Cache read: {usage.prompt_cache_read_tokens:,} → ${breakdown.prompt_cache_read_cost:.6f}")
        print(f"  ────────────────────────────────────────")
        print(f"  TOTAL: ${breakdown.total_cost:.6f} ({breakdown.total_tokens:,} tokens)")
        cost_per_1k = float(breakdown.total_cost) / (breakdown.total_tokens / 1000) if breakdown.total_tokens > 0 else 0
        print(f"  Costo por 1K tokens: ${cost_per_1k:.6f}")
    
    # Comparar modelos
    print("\n🔄 Comparación de Modelos (1000 prompt + 500 completion tokens):")
    print("-" * 60)
    
    models_to_compare = [
        "openai/gpt-4o",
        "openai/gpt-4o-mini",
        "anthropic/claude-3.5-sonnet",
        "anthropic/claude-3-haiku"
    ]
    
    comparisons = calculator.compare_models(models_to_compare, 1000, 500)
    
    for i, comp in enumerate(comparisons, 1):
        print(f"\n  {i}. {comp['display_name']}")
        print(f"     Costo total: ${comp['total_cost']:.6f}")
        print(f"     Costo por 1K tokens: ${comp['cost_per_1k_tokens']:.6f}")
        print(f"     Ahorro vs más caro: {((comparisons[-1]['total_cost'] - comp['total_cost']) / comparisons[-1]['total_cost'] * 100):.1f}%")
    
    print(f"\n✅ El modelo más económico es: {comparisons[0]['display_name']} (${comparisons[0]['total_cost']:.6f})")
