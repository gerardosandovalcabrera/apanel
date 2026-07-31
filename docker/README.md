# 🐳 Hermes Multi-Agent Docker System

Sistema completo de administración multi-agente de Hermes basado en Docker para despliegue en múltiples ubicaciones.

## 🏛️ Arquitectura

```
🌐 Dashboard Central (Tu servidor principal)
├── Docker Container: hermes-dashboard
│   ├── Dashboard Web Flask (puerto 5000)
│   ├── Redis para caché (puerto 6379)
│   └── Nginx Reverse Proxy (puerto 80/443)
│
🔗 Agentes Remotos (Otros servidores con Hermes)
├── Docker Container: hermes-connector (en cada servidor)
│   ├── API de health check (puerto 8081)
│   ├── Telemetría en tiempo real
│   ├── Comandos remotos
│   └── Autenticación con API Key
│
🌐 Network Docker
├── Comunicación segura entre dashboard y conectores
└── Soporte para múltiples redes remotas
```

## 📋 Requisitos

### **Para el Dashboard Central:**
- Docker 20.10+
- Docker Compose 2.0+
- 2 GB RAM mínimo
- 10 GB disco mínimo
- Puertos disponibles: 80, 443, 5000, 6379

### **Para Agentes Remotos:**
- Docker 20.10+
- Docker Compose 2.0+
- 512 MB RAM mínimo
- 2 GB disco mínimo
- Hermes Agent instalado en el host
- Puerto 8081 disponible
- Acceso SSH desde el dashboard

## 🚀 Instalación Rápida

### **Paso 1: Clonar y configurar el Dashboard Central**

```bash
# Copiar los archivos Docker al servidor central
scp -r docker/* user@dashboard-server:/opt/hermes-docker/

# Conectarte al servidor central
ssh user@dashboard-server

# Ir al directorio de Docker
cd /opt/hermes-docker

# Inicializar el sistema
chmod +x deploy-hermes-docker.sh
./deploy-hermes-docker.sh init

# Iniciar el Dashboard
./deploy-hermes-docker.sh start
```

### **Paso 2: Desplegar Conectores Remotos**

```bash
# Desde el servidor central, desplegar conectores en otros servidores
./deploy-hermes-docker.sh connector remote-server.com user

# El script automáticamente:
# 1. Copia los archivos necesarios al servidor remoto
# 2. Configura la conexión al dashboard central
# 3. Construye e inicia el connector Docker
# 4. Registra el agente en el dashboard
```

### **Paso 3: Acceder al Dashboard**

```
http://dashboard-server:5000
```

## 📖 Comandos del Sistema

### **Gestión del Dashboard Central:**

```bash
# Inicializar sistema (primera vez)
./deploy-hermes-docker.sh init

# Iniciar Dashboard
./deploy-hermes-docker.sh start

# Detener Dashboard
./deploy-hermes-docker.sh stop

# Reiniciar Dashboard
./deploy-hermes-docker.sh restart

# Ver estado
./deploy-hermes-docker.sh status

# Ver logs en tiempo real
./deploy-hermes-docker.sh logs
```

### **Gestión de Conectores Remotos:**

```bash
# Desplegar connector en servidor remoto
./deploy-hermes-docker.sh connector <host> <user>

# Ejemplo:
./deploy-hermes-docker.sh connector production-server.com admin
./deploy-hermes-docker.sh connector 192.168.1.100 user

# El connector se registra automáticamente en el dashboard
```

## 🔧 Configuración

### **Variables de Entorno del Dashboard:**

Archivo: `config/dashboard.env`

```bash
# Configuración Flask
FLASK_ENV=production
DASHBOARD_SECRET_KEY=<secreto-aleatorio-generado>

# Redis
REDIS_URL=redis://redis:6379/0

# Seguridad
CONNECTOR_API_KEY=<api-key-generada>
ALLOWED_ORIGINS=*
```

### **Variables de Entorno del Connector:**

Archivo: `~/hermes-connector/.env` (en servidor remoto)

```bash
# Conexión al Dashboard
DASHBOARD_URL=http://dashboard-server:5000
CONNECTOR_API_KEY=<misma-api-key-del-dashboard>

# Información del Agente
AGENT_NAME=agent-production-server
AGENT_HOST=production-server.com
HERMES_PORT=8080
AGENT_TYPE=remote
```

## 🌐 Arquitectura de Redes

### **Comunicación Dashboard ↔ Connector:**

```
Dashboard Central (192.168.1.10)
├── Puerto 5000: Dashboard Web
├── Puerto 8081: No usado (solo conectores)
└── Docker Network: 172.20.0.0/16

Connector Remoto 1 (192.168.1.20)
├── Puerto 8081: API del Connector
├── Monta ~/.hermes del host
└── Se conecta a Dashboard:5000

Connector Remoto 2 (192.168.1.30)
├── Puerto 8081: API del Connector
├── Monta ~/.hermes del host
└── Se conecta a Dashboard:5000
```

### **Flujo de Registro:**

1. **Connector inicia** → Se conecta al Dashboard
2. **Envía registro** → Con su información y API key
3. **Dashboard valida** → Verifica API key
4. **Dashboard acepta** → Agente aparece en el dashboard
5. **Heartbeat periódico** → Cada 60 segundos

## 🔒 Seguridad

### **Autenticación:**
- **API Key** generada aleatoriamente
- **Header `X-API-Key`** en todas las requests
- **Validación en cada endpoint**

### **Comunicación:**
- **HTTP** por defecto (puedes agregar HTTPS con Nginx)
- **Firewall recomendado:** Solo puertos necesarios
- **VPN recomendada** para redes públicas

### **Recursos del Host:**
- **Lectura de `~/.hermes`** (solo lectura)
- **Ejecución de comandos limitada**
- **Usuario no-root dentro del contenedor**

## 📊 API del Connector

El connector expone una API para que el Dashboard lo monitoree:

### **GET /health**
```bash
curl -H "X-API-Key: <api-key>" http://connector-host:8081/health
```

Respuesta:
```json
{
  "status": "healthy",
  "agent": {
    "name": "agent-production",
    "host": "production-server.com",
    "port": 8080,
    "type": "remote"
  },
  "hermes_health": {
    "health_score": 85,
    "resource_usage": {
      "cpu_percent": 45,
      "memory_percent": 60,
      "disk_percent": 30
    }
  }
}
```

### **POST /restart**
```bash
curl -X POST \
  -H "X-API-Key: <api-key>" \
  http://connector-host:8081/restart
```

### **GET /logs**
```bash
curl -H "X-API-Key: <api-key>" \
  "http://connector-host:8081/logs?lines=100"
```

## 🎯 Casos de Uso

### **Caso 1: Desarrollo Local + Servidor de Producción**

```bash
# Dashboard en tu máquina local (para testing)
./deploy-hermes-docker.sh init
./deploy-hermes-docker.sh start

# Connector en servidor de producción
./deploy-hermes-docker.sh connector production.com admin
```

### **Caso 2: Múltiples Servidores de Producción**

```bash
# Dashboard en servidor dedicado de monitoreo
ssh admin@monitoring-server.com
cd /opt/hermes-docker
./deploy-hermes-docker.sh init
./deploy-hermes-docker.sh start

# Conectores en múltiples servidores
./deploy-hermes-docker.sh connector server1.prod.com admin
./deploy-hermes-docker.sh connector server2.prod.com admin
./deploy-hermes-docker.sh connector server3.prod.com admin
```

### **Caso 3: Nube + On-Premise**

```bash
# Dashboard en nube (AWS, GCP, Azure)
./deploy-hermes-docker.sh init
./deploy-hermes-docker.sh start

# Connector en servidores on-premise
./deploy-hermes-docker.sh connector on-premise-1.local user
./deploy-hermes-docker.sh connector on-premise-2.local user
```

## 🐛 Troubleshooting

### **Problema: Connector no se registra**

```bash
# Ver logs del connector en el servidor remoto
ssh user@remote-server
docker logs -f hermes-connector

# Verificar que el Dashboard es accesible
curl http://dashboard-server:5000/api/metrics

# Verificar API key coincide
grep CONNECTOR_API_KEY ~/hermes-connector/.env
```

### **Problema: No se puede acceder al Dashboard**

```bash
# Verificar que el contenedor está corriendo
docker ps | grep hermes-dashboard

# Ver logs del Dashboard
docker logs hermes-dashboard

# Verificar puertos
netstat -tuln | grep 5000
```

### **Problema: Heartbeat falla**

```bash
# Verificar conectividad de red
ping dashboard-server
telnet dashboard-server 5000

# Verificar firewall
sudo ufw status
sudo firewall-cmd --list-all
```

## 📈 Monitoreo y Logs

### **Logs del Dashboard Central:**
```bash
# Ver logs en tiempo real
docker logs -f hermes-dashboard

# Ver logs de todos los servicios
docker-compose logs -f
```

### **Logs de Conectores Remotos:**
```bash
# En el servidor remoto
ssh user@remote-server
docker logs -f hermes-connector

# Ver logs específicos
docker logs hermes-connector | grep ERROR
docker logs hermes-connector | grep heartbeat
```

## 🚀 Actualización del Sistema

### **Actualizar Dashboard Central:**
```bash
# Parar servicios
./deploy-hermes-docker.sh stop

# Actualizar código
git pull  # o copiar nuevos archivos

# Reconstruir imágenes
./deploy-hermes-docker.sh init

# Iniciar servicios
./deploy-hermes-docker.sh start
```

### **Actualizar Conectores Remotos:**
```bash
# El script de deploy actualiza automáticamente
./deploy-hermes-docker.sh connector remote-server.com user
```

## 💡 Mejores Prácticas

### **Seguridad:**
1. ✅ Usar VPN para comunicación entre servidores
2. ✅ Cambiar API keys periódicamente
3. ✅ Usar HTTPS en producción (configurar Nginx)
4. ✅ Limitar acceso con firewall
5. ✅ Usar usuarios no-root para SSH

### **Monitoreo:**
1. ✅ Configurar alertas en el Dashboard
2. ✅ Revisar logs periódicamente
3. ✅ Monitorear recursos de los contenedores
4. ✅ Configurar backups automáticos

### **Escalabilidad:**
1. ✅ Usar Redis cluster para muchos agentes
2. ✅ Balancear carga con múltiples dashboards
3. ✅ Usar Nginx para HTTPS y caching
4. ✅ Configurar health checks agresivos

## 📞 Soporte

Si encuentras problemas:

1. Revisa los logs del contenedor
2. Verifica la conectividad de red
3. Confirma que los puertos están disponibles
4. Valida que las API keys coinciden

---

**🎉 Sistema creado específicamente para administración multi-agente de Hermes con Docker**
