# 🚀 **INICIO ULTRA SIMPLE - APanel en Docker**

## 🎯 **Tienes 3 opciones para iniciar APanel, elige la que prefieras:**

---

## 🔥 **OPCIÓN 1: UN SOLO COMANDO (MÁS FÁCIL)**

### **Si quieres tener TODO funcionando con UN solo comando:**

```bash
# Clonar el repo
git clone git@github.com:gerardosandovalcabrera/apanel.git
cd apanel

# EJECUTAR UN SOLO COMANDO:
chmod +x docker/start.sh
./docker/start.sh
```

**Este script hace TODO automáticamente:**
- ✅ Verifica si Docker está instalado
- ✅ Si no está, lo instala automáticamente
- ✅ Descarga APanel si no lo tienes
- ✅ Configura todo automáticamente
- ✅ Inicia el sistema completo
- ✅ Te muestra cómo acceder

**Tiempo total:** 5-10 minutos (depende de tu conexión)

---

## 🛠️ **OPCIÓN 2: Auto-Installer (RECOMENDADO para servidores nuevos)**

### **Si tienes un servidor nuevo sin Docker:**

```bash
# Clonar el repo
git clone git@github.com:gerardosandovalcabrera/apanel.git
cd apanel/docker

# EJECUTAR:
chmod +x auto-install.sh
./auto-install.sh
```

**Este script hace:**
- ✅ Detecta tu sistema operativo automáticamente
- ✅ Instala Docker si no está
- ✅ Instala Docker Compose
- ✅ Clona APanel si no lo tienes
- ✅ Ejecuta la configuración automática
- ✅ Inicia el sistema

**Sistemas soportados:**
- ✅ Ubuntu 18.04+
- ✅ Debian 10+
- ✅ CentOS 7+
- ✅ RHEL 8+
- ✅ Fedora 30+

**Tiempo total:** 10-15 minutos

---

## ⚡ **OPCIÓN 3: Quick Start (SI ya tienes Docker)**

### **Si ya tienes Docker y Docker Compose instalados:**

```bash
# Clonar el repo
git clone git@github.com:gerardosandovalcabrera/apanel.git
cd apanel/docker

# EJECUTAR:
chmod +x quick-start.sh
./quick-start.sh
```

**Este script hace:**
- ✅ Verifica que Docker funcione
- ✅ Genera configuración automáticamente
- ✅ Crea secrets aleatorios
- ✅ Construye imágenes Docker
- ✅ Inicia todos los contenedores
- ✅ Te muestra cómo acceder

**Tiempo total:** 3-5 minutos

---

## 🎯 **Recomendación: ¿Cuál opción elegir?**

### **Sistema nuevo sin Docker:**
```
OPCIÓN 2: auto-install.sh
```
- Instala Docker automáticamente
- Detecta tu sistema operativo
- Todo en un solo proceso

### **Sistema con Docker instalado:**
```
OPCIÓN 1: start.sh
```
- Un solo comando para todo
- Automático e inteligente
- La opción más fácil

### **Desarrollo local:**
```
OPCIÓN 3: quick-start.sh
```
- Asumes que Docker está instalado
- Más control sobre el proceso
- Ideal para desarrolladores

---

## 📊 **Comparación de las 3 opciones:**

| Característica | Opción 1 (start.sh) | Opción 2 (auto-install.sh) | Opción 3 (quick-start.sh) |
|---------------|---------------------|----------------------------|---------------------------|
| **Facilidad** | ⭐⭐⭐⭐⭐ Más fácil | ⭐⭐⭐⭐ Muy fácil | ⭐⭐⭐ Fácil |
| **Instala Docker** | ✅ Automático | ✅ Automático | ❌ Asumido |
| **Detecta SO** | ✅ Automático | ✅ Automático | ❌ No necesario |
| **Tiempo total** | 5-10 min | 10-15 min | 3-5 min |
| **Ideal para** | Cualquier caso | Servidores nuevos | Desarrollo |
| **Requisitos** | Solo SSH | Solo SSH | Docker + Compose |

---

## 🚀 **EJEMPLO COMPLETO - Desde cero hasta funcionando:**

### **En un servidor nuevo (Ubuntu 20.04):**

```bash
# 1. Conectarte al servidor
ssh usuario@tu-servidor.com

# 2. UN SOLO COMANDO:
git clone git@github.com:gerardosandovalcabrera/apanel.git && cd apanel && chmod +x docker/start.sh && ./docker/start.sh

# 3. ¡LISTO! APanel está funcionando en http://tu-servidor.com:5000
```

### **En tu máquina local (con Docker):**

```bash
# 1. Clonar
git clone git@github.com:gerardosandovalcabrera/apanel.git
cd apanel

# 2. UN COMANDO:
chmod +x docker/start.sh && ./docker/start.sh

# 3. ¡LISTO! http://localhost:5000
```

---

## 🎁 **Lo que hacen automáticamente estos scripts:**

### **✅ No necesitas hacer:**
- ❌ Instalar Docker manualmente
- ❌ Configurar variables de entorno
- ❌ Generar secrets
- ❌ Crear directorios
- ❌ Construir imágenes
- ❌ Iniciar contenedores manualmente
- ❌ Configurar redes Docker
- ❌ Verificar que todo funcione

### **🎯 Solo necesitas:**
- ✅ Acceso al servidor (SSH)
- ✅ Permisos de sudo (para instalar Docker)
- ✅ Conexión a internet

---

## 🔧 **Después del inicio automático:**

### **El sistema estará disponible en:**

```
📊 Dashboard Web:     http://localhost:5000/ (o http://tu-servidor:5000/)
🤖 MCP Server:       http://localhost:5000/mcp/
🔐 Auth Providers:    http://localhost:5000/auth/providers
📚 Documentación:     http://localhost:5000/docs
```

### **Comandos útiles:**

```bash
# Ver logs
docker-compose logs -f

# Ver estado
docker-compose ps

# Reiniciar
docker-compose restart

# Detener
docker-compose down

# Actualizar
git pull && docker-compose up -d --build
```

---

## 🎉 **¡En cuestión de minutos tendrás APanel funcionando!**

Elige la opción que mejor se adapte a tu situación y ejecuta un solo comando.

**¿Prefieres la opción 1, 2 o 3?**

---

**P.D.: Si algo falla, los scripts tienen mensajes de error claros que te indicarán qué hacer.**
