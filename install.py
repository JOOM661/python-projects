# install.py - Script de instalação para Railway
import subprocess
import sys

print("🔧 INSTALANDO DEPENDÊNCIAS PARA RAILWAY")
print("=" * 50)

# Versões comprovadamente funcionais
packages = [
    "python-dotenv==1.0.0",
    "Flask==3.0.2",
    "pyTelegramBotAPI==4.18.0",
    "supabase==2.3.0",
    "httpx==0.25.2",
    "requests==2.31.0",
]

print("📦 Pacotes a instalar:")
for pkg in packages:
    print(f"  • {pkg}")

print("\n🚀 Iniciando instalação...")

try:
    # Instalar pacotes
    for pkg in packages:
        print(f"\n📥 Instalando {pkg}...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", pkg],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"✅ {pkg} instalado com sucesso!")
        else:
            print(f"⚠️  Problema com {pkg}:")
            print(result.stderr[:200])
    
    print("\n" + "=" * 50)
    print("✅ INSTALAÇÃO COMPLETA!")
    print("\n📊 Verificando versões instaladas...")
    
    # Verificar versões
    subprocess.run([sys.executable, "-m", "pip", "list", "--format=columns"])
    
except Exception as e:
    print(f"❌ Erro durante instalação: {e}")
