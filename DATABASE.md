# 💾 APanel Database System - PostgreSQL Persistence

## 📊 Overview

APanel now includes a complete PostgreSQL database system for persistent storage. This ensures that **ALL historical data is saved** and can be queried later.

---

## 🗄️ Database Architecture

### **Database: PostgreSQL 15**
```
Host: postgres (Docker container)
Port: 5432
Database: apanel_db
User: apanel
Password: apanel_password
```

### **Data Tables:**

#### **1. Organizations** 🏢
- Multi-tenant support
- Plan tiers (free, pro, team, enterprise)
- API keys
- User information

#### **2. Billing Records** 💰
- Every API call is recorded
- Token usage (prompt/completion)
- Cost calculation
- Timestamps
- Request metadata

#### **3. Budgets** 📋
- Monthly budgets per organization
- Alert thresholds (50%, 80%, 100%)
- Currency configuration
- Webhook integration

#### **4. Cost Metrics** 📊
- Aggregated metrics (hourly/daily/weekly/monthly)
- Total costs and tokens
- Average costs per call
- Model breakdown

#### **5. Token Usage** 🪙
- Monthly token usage per model
- Prompt vs completion tokens
- Cost tracking per model
- Historical data

#### **6. Budget Alerts** 🔔
- Alert notifications
- Warning/critical/exceeded levels
- Read/unread status
- Email notification tracking

---

## 🚀 Quick Start

### **1. Start the Database:**
```bash
cd docker
docker-compose up -d postgres
```

### **2. Initialize Database:**
```bash
chmod +x init-database.sh
./init-database.sh
```

### **3. Use Database Billing:**
```python
from apanel_database_billing import get_database_billing_integration

billing = get_database_billing_integration()

# Record an API call (automatically saved to PostgreSQL)
result = billing.record_api_call(
    organization_id="org-uuid",
    provider_model_id="openai/gpt-4",
    prompt_tokens=1000,
    completion_tokens=500
)

# Get billing summary with historical data
summary = billing.get_billing_summary("org-uuid", days=30)
print(f"Total cost: ${summary['cost_summary']['total_cost']}")
print(f"Total calls: {summary['cost_summary']['calls_count']}")
```

---

## 📋 Configuration

### **Environment Variables:**
```bash
# Database
DATABASE_URL=postgresql://apanel:apanel_password@postgres:5432/apanel_db
DATABASE_HOST=postgres
DATABASE_PORT=5432
DATABASE_NAME=apanel_db
DATABASE_USER=apanel
DATABASE_PASSWORD=apanel_password

# Redis (for cache)
REDIS_URL=redis://redis:6379/0
```

### **Docker Compose Services:**
```yaml
postgres:
  image: postgres:15-alpine
  ports:
    - "5432:5432"
  volumes:
    - postgres-data:/var/lib/postgresql/data
```

---

## 🔍 Database Queries

### **Connect to Database:**
```bash
docker exec -it hermes-postgres psql -U apanel -d apanel_db
```

### **View Tables:**
```sql
\dt
```

### **Example Queries:**

#### **See all API calls:**
```sql
SELECT 
    provider_model_id,
    total_tokens,
    total_cost,
    timestamp
FROM billing_records 
WHERE organization_id = 'your-org-id'
ORDER BY timestamp DESC 
LIMIT 100;
```

#### **Monthly costs:**
```sql
SELECT 
    DATE_TRUNC('month', timestamp) as month,
    SUM(total_cost) as total_cost,
    SUM(total_tokens) as total_tokens,
    COUNT(*) as calls_count
FROM billing_records
GROUP BY month
ORDER BY month DESC;
```

#### **Budget alerts:**
```sql
SELECT 
    alert_type,
    percentage_used,
    message,
    created_at
FROM budget_alerts
WHERE organization_id = 'your-org-id'
ORDER BY created_at DESC
LIMIT 20;
```

---

## 💡 Benefits of PostgreSQL Persistence

### **✅ Data Persistence:**
- **No more lost data** on restart
- Historical records saved permanently
- Complete audit trail

### **✅ Query Capabilities:**
- SQL queries for complex analytics
- JOINs across tables
- Aggregations and reports

### **✅ Scalability:**
- Handles millions of records
- Indexed queries for speed
- Connection pooling

### **✅ Reliability:**
- ACID transactions
- Data integrity
- Backup and restore

### **✅ Analytics:**
- Historical trends
- Cost analysis
- Usage patterns
- Model comparison

---

## 🔄 Migration from In-Memory

### **Before (In-Memory):**
```python
# Data lost on restart
self.api_calls: List[Dict] = []
self.budgets: Dict[str, BudgetConfig] = {}
```

### **After (PostgreSQL):**
```python
# Data persists permanently
billing = get_database_billing_integration()
result = billing.record_api_call(...)  # Saved to database
summary = billing.get_billing_summary(...)  # Retrieved from database
```

---

## 📊 Database Schema

```
organizations
├── id (UUID, primary key)
├── name (VARCHAR)
├── plan_tier (VARCHAR)
├── api_key (VARCHAR, unique)
└── ...

budgets
├── id (UUID, primary key)
├── organization_id (FK to organizations)
├── monthly_budget (DECIMAL)
├── alert_thresholds (JSON)
└── ...

billing_records
├── id (UUID, primary key)
├── organization_id (FK to organizations)
├── provider_model_id (VARCHAR, indexed)
├── total_tokens (INT)
├── total_cost (DECIMAL)
├── timestamp (DATETIME, indexed)
└── ...

cost_metrics
├── id (UUID, primary key)
├── organization_id (FK to organizations)
├── metric_type (VARCHAR)
├── period_start (DATETIME, indexed)
├── total_cost (DECIMAL)
└── ...

token_usage
├── id (UUID, primary key)
├── organization_id (FK to organizations)
├── month (VARCHAR, indexed)
├── provider_model_id (VARCHAR, indexed)
├── total_tokens (INT)
└── ...

budget_alerts
├── id (UUID, primary key)
├── organization_id (FK to organizations)
├── budget_id (FK to budgets)
├── alert_type (VARCHAR)
├── percentage_used (FLOAT)
├── created_at (DATETIME, indexed)
└── ...
```

---

## 🔧 Maintenance

### **Backup Database:**
```bash
docker exec hermes-postgres pg_dump -U apanel apanel_db > backup.sql
```

### **Restore Database:**
```bash
cat backup.sql | docker exec -i hermes-postgres psql -U apanel apanel_db
```

### **Clear Old Data:**
```sql
DELETE FROM billing_records 
WHERE timestamp < NOW() - INTERVAL '90 days';
```

---

## 📝 Summary

**APanel ahora tiene persistencia completa con PostgreSQL:**

```
✅ Todo el historial de llamadas API guardado
✅ Uso de tokens por mes y modelo
✅ Métricas de costo agregadas
✅ Alertas de presupuesto permanentes
✅ Datos recuperables y consultables
✅ Soporte multi-tenant completo
✅ Escalable para millones de registros
✅ Backups y restauración

🎯 Resultado: Ya no se pierde ningún dato
```

---

## 🚀 Next Steps

- [ ] Implement automatic daily backups
- [ ] Add data retention policies
- [ ] Create analytics dashboard
- [ ] Add export to CSV functionality
- [ ] Implement data archiving for old records
