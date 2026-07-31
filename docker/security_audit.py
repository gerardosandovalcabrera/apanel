#!/usr/bin/env python3
"""
🔍 Security Audit Tool - APanel
Busca secrets, keys y credenciales en el código
"""

import os
import re
from pathlib import Path
from typing import List, Tuple
import json


class SecurityAuditor:
    """
    Auditor de seguridad para buscar secrets en código
    
    Busca:
    - API Keys
    - Tokens
    - Passwords
    - Secrets
    - Credenciales en texto plano
    """
    
    # Patterns para detectar secrets
    PATTERNS = {
        'api_key': [
            r'api[_-]?key\s*=\s*["\']([a-zA-Z0-9_\-]{20,})["\']',
            r'apikey\s*=\s*["\']([a-zA-Z0-9_\-]{20,})["\']',
            r'API[_-]?KEY\s*=\s*["\']([a-zA-Z0-9_\-]{20,})["\']',
        ],
        'token': [
            r'token\s*=\s*["\']([a-zA-Z0-9_\-]{20,})["\']',
            r'auth[_-]?token\s*=\s*["\']([a-zA-Z0-9_\-]{20,})["\']',
            r'access[_-]?token\s*=\s*["\']([a-zA-Z0-9_\-]{20,})["\']',
            r'jwt[_-]?secret\s*=\s*["\']([a-zA-Z0-9_\-]{20,})["\']',
        ],
        'password': [
            r'password\s*=\s*["\']([^"\']{4,})["\']',
            r'passwd\s*=\s*["\']([^"\']{4,})["\']',
            r'secret[_-]?key\s*=\s*["\']([a-zA-Z0-9_\-]{10,})["\']',
        ],
        'aws_key': [
            r'aws[_-]?access[_-]?key[_-]?id\s*=\s*["\'](AKIA[0-9A-Z]{16})["\']',
            r'aws[_-]?secret[_-]?access[_-]?key\s*=\s*["\']([a-zA-Z0-9/+=]{40})["\']',
        ],
        'github_token': [
            r'github[_-]?token\s*=\s*["\'](gh[pousr]_[a-zA-Z0-9_]{36,})["\']',
            r'gh[pousr]_[a-zA-Z0-9_]{36,}',
        ],
        'openai_key': [
            r'sk-[a-zA-Z0-9]{48}',
            r'openai[_-]?api[_-]?key\s*=\s*["\'](sk-[a-zA-Z0-9]{48})["\']',
        ],
        'database_url': [
            r'database[_-]?url\s*=\s*["\']([^"\']+://[^"\']+:[^"\']+@[^"\']+)["\']',
            r'db[_-]?url\s*=\s*["\']([^"\']+://[^"\']+:[^"\']+@[^"\']+)["\']',
            r'mongodb://[^"\']+:[^"\']+@',
            r'postgresql://[^"\']+:[^"\']+@',
            r'mysql://[^"\']+:[^"\']+@',
        ],
        'jwt': [
            r'eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+',
        ],
        'email': [
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        ],
        'ip_address': [
            r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
        ],
        'base64_long': [
            r'["\']([A-Za-z0-9+/]{100,}={0,2})["\']',
        ]
    }
    
    # Archivos y directorios a ignorar
    IGNORE_PATTERNS = [
        r'\.git/',
        r'node_modules/',
        r'__pycache__/',
        r'\.pyc$',
        r'\.pyo$',
        r'\.pyd$',
        r'\.so$',
        r'\.dll$',
        r'\.exe$',
        r'\.DS_Store',
        r'package-lock\.json',
        r'yarn\.lock',
        r'\.env\.',
        r'\.venv/',
        r'venv/',
        r'env/',
        r'\.pytest_cache/',
        r'\.mypy_cache/',
        r'\.coverage',
        r'htmlcov/',
        r'\.tox/',
        r'build/',
        r'dist/',
        r'\*\.egg-info/',
    ]
    
    # Extensiones seguras para revisar
    SAFE_EXTENSIONS = {
        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs',
        '.rb', '.php', '.cs', '.cpp', '.c', '.h', '.hpp',
        '.sh', '.bash', '.zsh', '.fish', '.ps1', '.bat',
        '.yml', '.yaml', '.json', '.xml', '.toml', '.ini', '.cfg',
        '.conf', '.config', '.env', '.txt', '.md', '.rst',
        '.sql', '.db', '.sqlite', '.sqlite3',
    }
    
    def __init__(self, directory: str):
        self.directory = Path(directory)
        self.issues: List[Tuple[str, int, str, str, str]] = []
    
    def should_ignore_file(self, file_path: Path) -> bool:
        """Verificar si el archivo debe ser ignorado"""
        # Verificar patrones de ignorar
        for pattern in self.IGNORE_PATTERNS:
            if re.search(pattern, str(file_path)):
                return True
        
        # Verificar extensión
        if file_path.suffix.lower() not in self.SAFE_EXTENSIONS:
            return True
        
        return False
    
    def scan_file(self, file_path: Path) -> List[Tuple[int, str, str, str]]:
        """Escanear un archivo buscando secrets"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
                
                for line_num, line in enumerate(lines, 1):
                    for secret_type, patterns in self.PATTERNS.items():
                        for pattern in patterns:
                            matches = re.finditer(pattern, line, re.IGNORECASE)
                            for match in matches:
                                # Extraer el valor del secret
                                secret_value = match.group(0) if len(match.groups()) == 0 else match.group(1)
                                
                                # Ignorar falsos positivos comunes
                                if self._is_false_positive(secret_value, line):
                                    continue
                                
                                issues.append((line_num, secret_type, secret_value, line.strip()))
        except Exception as e:
            print(f"  ❌ Error leyendo {file_path}: {e}")
        
        return issues
    
    def _is_false_positive(self, secret_value: str, line: str) -> bool:
        """Verificar si es un falso positivo"""
        # Ignorar ejemplos, comentarios, placeholders
        false_positives = [
            'your_api_key_here',
            'your_token_here',
            'your_secret_here',
            'replace_with_your_key',
            'example',
            'placeholder',
            'xxx',
            '***',
            '----',
            'your-password',
            'test',
            'demo',
            'sample',
            'localhost',
            '127.0.0.1',
            '0.0.0.0',
        ]
        
        secret_lower = secret_value.lower()
        
        # Verificar si es un falso positivo conocido
        for fp in false_positives:
            if fp in secret_lower:
                return True
        
        # Ignorar líneas que son claramente ejemplos
        if '#' in line or '//' in line or '/*' in line:
            line_lower = line.lower()
            if 'example' in line_lower or 'placeholder' in line_lower:
                return True
        
        # Ignorar valores muy cortos (probablemente no son secrets)
        if len(secret_value) < 10:
            return True
        
        # Ignorar valores alfanuméricos muy simples
        if secret_value.isalnum() and len(secret_value) < 20:
            return True
        
        return False
    
    def scan_directory(self) -> List[Tuple[str, int, str, str, str]]:
        """Escanear todo el directorio recursivamente"""
        print(f"🔍 Escaneando directorio: {self.directory}")
        print("=" * 60)
        
        files_scanned = 0
        files_with_issues = 0
        
        for file_path in self.directory.rglob('*'):
            if not file_path.is_file():
                continue
            
            if self.should_ignore_file(file_path):
                continue
            
            files_scanned += 1
            issues = self.scan_file(file_path)
            
            if issues:
                files_with_issues += 1
                for line_num, secret_type, secret_value, line in issues:
                    self.issues.append((
                        str(file_path),
                        line_num,
                        secret_type,
                        secret_value,
                        line
                    ))
        
        print(f"\n📊 Resumen:")
        print(f"  Archivos escaneados: {files_scanned}")
        print(f"  Archivos con issues: {files_with_issues}")
        print(f"  Issues encontrados: {len(self.issues)}")
        
        return self.issues
    
    def generate_report(self) -> str:
        """Generar reporte detallado"""
        report = []
        
        report.append("\n" + "=" * 60)
        report.append("🔒 SECURITY AUDIT REPORT - APanel")
        report.append("=" * 60 + "\n")
        
        if not self.issues:
            report.append("✅ NO SE ENCONTRARON SECRETS EXPLICÍTOS")
            report.append("El código parece seguro para hacer público.")
        else:
            report.append(f"⚠️ SE ENCONTRARON {len(self.issues)} POSIBLES SECRETS:\n")
            
            # Agrupar por tipo de secreto
            issues_by_type = {}
            for file_path, line_num, secret_type, secret_value, line in self.issues:
                if secret_type not in issues_by_type:
                    issues_by_type[secret_type] = []
                issues_by_type[secret_type].append((file_path, line_num, secret_value, line))
            
            # Mostrar por tipo
            for secret_type, issues in issues_by_type.items():
                report.append(f"\n🔴 {secret_type.upper()} ({len(issues)} encontrados):")
                report.append("-" * 60)
                
                for file_path, line_num, secret_value, line in issues[:5]:  # Mostrar max 5 por tipo
                    # Ocultar el secret parcialmente
                    masked_value = self._mask_secret(secret_value)
                    report.append(f"\n  📄 {file_path}:{line_num}")
                    report.append(f"  🔑 {masked_value}")
                    report.append(f"  📝 {line[:80]}")
                
                if len(issues) > 5:
                    report.append(f"\n  ... y {len(issues) - 5} más")
        
        report.append("\n" + "=" * 60)
        report.append("✨ FIN DEL REPORT")
        report.append("=" * 60 + "\n")
        
        return "\n".join(report)
    
    def _mask_secret(self, secret: str, visible_chars: int = 4) -> str:
        """Ocultar parte del secret en el reporte"""
        if len(secret) <= visible_chars:
            return "****"
        return secret[:visible_chars] + "****" + secret[-visible_chars:]


def main():
    """Función principal"""
    # Directorio a auditar
    audit_dir = "/home/hermeswebui/hermes-backup/docker"
    
    print("🔒 SECURITY AUDIT - APanel")
    print("=" * 60)
    
    auditor = SecurityAuditor(audit_dir)
    issues = auditor.scan_directory()
    
    # Generar reporte
    report = auditor.generate_report()
    print(report)
    
    # Guardar reporte en archivo
    report_path = "/home/hermeswebui/hermes-backup/docker/SECURITY_AUDIT_REPORT.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"📄 Reporte guardado en: {report_path}")
    
    # Verificar .gitignore
    print("\n📋 Verificando .gitignore...")
    gitignore_path = Path(audit_dir) / ".gitignore"
    
    if not gitignore_path.exists():
        print("  ⚠️ No existe .gitignore")
    else:
        with open(gitignore_path, 'r') as f:
            gitignore_content = f.read()
        
        essential_patterns = [
            '.env',
            '.env.local',
            '*.key',
            '*.pem',
            'secrets/',
            'credentials/',
            '*.db',
            '*.sqlite',
            'secrets.txt',
            'api_keys.txt',
            'auth.json'
        ]
        
        missing_patterns = []
        for pattern in essential_patterns:
            if pattern not in gitignore_content:
                missing_patterns.append(pattern)
        
        if missing_patterns:
            print(f"  ⚠️ Patrones faltantes en .gitignore:")
            for pattern in missing_patterns:
                print(f"    - {pattern}")
        else:
            print("  ✅ .gitignore contiene patrones esenciales")
    
    print("\n🎯 Recomendaciones:")
    if issues:
        print("  ⚠️ Se encontraron posibles secrets. Revisa el reporte.")
        print("  📝 Remueve o reemplaza los secrets con variables de entorno.")
        print("  🔄 Usa git filter-branch para remover secrets del historial si es necesario.")
    else:
        print("  ✅ El código parece seguro para hacer público.")
        print("  🚀 Puedes hacer el repo público sin riesgos evidentes.")
    
    return 0 if not issues else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
