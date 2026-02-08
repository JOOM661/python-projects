import telebot
import os
import sys
import json
import time
import sqlite3
import hashlib
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from flask import Flask
from threading import Thread
from typing import Dict, List, Optional, Tuple
import traceback

# ==================== CONFIGURAÇÃO ====================
load_dotenv()

class PizzaSabor:
    """Sabores de pizza disponíveis"""
    SABORES = {
        "calabresa": {
            "nome": "Calabresa 🧅",
            "desc": "Calabresa fatiada com cebola",
            "preco": 40.00,
            "emoji": "🧅"
        },
        "portuguesa": {
            "nome": "Portuguesa 🇵🇹", 
            "desc": "Presunto, ovos, cebola e azeitonas",
            "preco": 45.00,
            "emoji": "🇵🇹"
        },
        "marguerita": {
            "nome": "Marguerita 🌿",
            "desc": "Muçarela, tomate e manjericão",
            "preco": 38.00,
            "emoji": "🌿"
        },
        "frango": {
            "nome": "Frango Catupiry 🐔",
            "desc": "Frango desfiado com catupiry",
            "preco": 42.00,
            "emoji": "🐔"
        },
        "quatroqueijos": {
            "nome": "4 Queijos 🧀",
            "desc": "Mussarela, provolone, parmesão e gorgonzola",
            "preco": 48.00,
            "emoji": "🧀"
        },
        "chocolate": {
            "nome": "Chocolate 🍫",
            "desc": "Chocolate ao leite cremoso",
            "preco": 35.00,
            "emoji": "🍫"
        },
        "romeuejulieta": {
            "nome": "Romeu & Julieta ❤️",
            "desc": "Goiabada com queijo mineiro",
            "preco": 35.00,
            "emoji": "❤️"
        }
    }

    TAMANHOS = {
        "pequena": {"nome": "Pequena", "multiplicador": 0.7, "diametro": "25cm"},
        "media": {"nome": "Média", "multiplicador": 0.85, "diametro": "30cm"},
        "grande": {"nome": "Grande", "multiplicador": 1.0, "diametro": "35cm"},
        "familia": {"nome": "Família", "multiplicador": 1.3, "diametro": "45cm"}
    }

    STATUS = {
        "pendente": {"nome": "Pendente", "emoji": "🟡"},
        "preparando": {"nome": "Em Preparação", "emoji": "🔵"},
        "saiu_entrega": {"nome": "Saiu para Entrega", "emoji": "🚚"},
        "entregue": {"nome": "Entregue", "emoji": "✅"},
        "cancelado": {"nome": "Cancelado", "emoji": "❌"}
    }

# ==================== FLASK PARA KEEP ALIVE ====================
app = Flask('')

@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>🍕 Pizzaria Romeo Bot</title>
        <style>
            body { 
                font-family: 'Arial', sans-serif; 
                text-align: center; 
                padding: 50px; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .container {
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                padding: 40px;
                border-radius: 20px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                max-width: 600px;
                margin: 0 auto;
            }
            h1 { 
                color: #FFD700; 
                font-size: 2.5em; 
                margin-bottom: 20px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }
            .status { 
                background: rgba(255, 255, 255, 0.2); 
                color: white; 
                padding: 25px; 
                border-radius: 15px; 
                margin: 25px 0;
                border: 1px solid rgba(255, 255, 255, 0.3);
            }
            .emoji { font-size: 3em; margin: 10px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="emoji">🤖🍕</div>
            <h1>Pizzaria Romeo Bot</h1>
            <div class="status">
                <h2>✅ SISTEMA ONLINE</h2>
                <p>🍕 Bot de delivery ativo e funcionando</p>
                <p>⏰ Hora do servidor: {}</p>
                <p>📊 Status: Operacional</p>
            </div>
            <p>© 2024 Pizzaria Romeo - Todos os direitos reservados</p>
        </div>
    </body>
    </html>
    """.format(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=False)

def keep_alive():
    """Inicia servidor web em thread separada"""
    t = Thread(target=run_web_server, daemon=True)
    t.start()

# ==================== CONFIGURAÇÃO BOT ====================
CHAVE_API = os.getenv("TELEGRAM_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
DONO_ID = int(os.getenv("DONO_ID", 0))

if not CHAVE_API:
    print("❌ ERRO: TELEGRAM_TOKEN não encontrado")
    sys.exit(1)

bot = telebot.TeleBot(CHAVE_API, parse_mode="Markdown")

# ==================== SISTEMA DE LOG ====================
class Logger:
    """Sistema de logging avançado"""
    def __init__(self):
        self.log_file = "bot_logs.json"
        self.max_logs = 1000
        self.setup_logs()

    def setup_logs(self):
        """Inicializa arquivo de logs"""
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump([], f)

    def log(self, nivel: str, mensagem: str, chat_id: str = None):
        """Registra um log"""
        timestamp = datetime.now(timezone.utc).isoformat()
        log_entry = {
            "timestamp": timestamp,
            "nivel": nivel,
            "mensagem": mensagem,
            "chat_id": str(chat_id) if chat_id else None
        }

        # Salvar em arquivo
        try:
            with open(self.log_file, 'r+', encoding='utf-8') as f:
                logs = json.load(f)
                logs.append(log_entry)
                if len(logs) > self.max_logs:
                    logs = logs[-self.max_logs:]
                f.seek(0)
                json.dump(logs, f, ensure_ascii=False, indent=2)
                f.truncate()
        except Exception as e:
            print(f"❌ Erro ao salvar log: {e}")

        # Imprimir no console com cores
        cores = {
            "info": "\033[94m",     # Azul
            "success": "\033[92m",  # Verde
            "warning": "\033[93m",  # Amarelo
            "error": "\033[91m",    # Vermelho
            "debug": "\033[95m"     # Magenta
        }
        reset = "\033[0m"

        cor = cores.get(nivel, "\033[97m")  # Branco como padrão
        hora = datetime.fromisoformat(timestamp).strftime("%H:%M:%S")
        print(f"{cor}[{nivel.upper():8}] {hora} - {mensagem}{reset}")

logger = Logger()

# ==================== GESTÃO DE BANCO DE DADOS ====================
class DatabaseManager:
    """Gerenciador de banco de dados híbrido (Supabase + SQLite)"""
    def __init__(self):
        self.supabase = None
        self.sqlite_conn = None
        self.modo_atual = None
        self.initialize_databases()

    def initialize_databases(self):
        """Inicializa ambos os bancos de dados"""
        logger.log("info", "🔄 Inicializando bancos de dados...")

        # Tentar conectar ao Supabase
        try:
            from supabase import create_client
            self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

            # Testar conexão
            self.supabase.table("pedidos").select("*").limit(1).execute()
            logger.log("success", "✅ Supabase conectado com sucesso")
            self.modo_atual = "supabase"

        except Exception as e:
            logger.log("warning", f"⚠️ Supabase não disponível: {str(e)[:80]}")
            self.supabase = None

        # Inicializar SQLite (sempre como fallback)
        try:
            self.sqlite_conn = sqlite3.connect('pizzaria_romeo.db', check_same_thread=False)
            self.sqlite_conn.row_factory = sqlite3.Row
            self.create_sqlite_tables()
            logger.log("success", "✅ SQLite configurado com sucesso")

            if not self.supabase:
                self.modo_atual = "sqlite"

        except Exception as e:
            logger.log("error", f"❌ Erro SQLite: {e}")
            self.sqlite_conn = None

        logger.log("info", f"📊 Modo de banco selecionado: {self.modo_atual}")

    def create_sqlite_tables(self):
        """Cria todas as tabelas no SQLite"""
        cursor = self.sqlite_conn.cursor()

        # Tabela pedidos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pedidos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_pedido TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL,
                nome TEXT NOT NULL,
                pizza TEXT NOT NULL,
                tamanho TEXT DEFAULT 'Grande',
                endereco TEXT NOT NULL,
                telefone TEXT,
                idade TEXT,
                pagamento TEXT NOT NULL,
                observacoes TEXT,
                created_at TEXT NOT NULL,
                status TEXT DEFAULT 'pendente',
                entregue_em TEXT,
                valor REAL DEFAULT 0.0,
                taxa_entrega REAL DEFAULT 5.0,
                fonte TEXT DEFAULT 'sqlite',
                updated_at TEXT
            )
        ''')

        # Tabela anuncios
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS anuncios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                mensagem TEXT NOT NULL,
                tipo TEXT DEFAULT 'geral',
                prioridade INTEGER DEFAULT 1,
                criado_em TEXT NOT NULL,
                expira_em TEXT,
                ativo INTEGER DEFAULT 1,
                visualizacoes INTEGER DEFAULT 0
            )
        ''')

        # Tabela usuarios
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                user_id TEXT PRIMARY KEY,
                username TEXT,
                primeiro_nome TEXT,
                ultimo_acesso TEXT,
                total_pedidos INTEGER DEFAULT 0,
                total_gasto REAL DEFAULT 0.0,
                created_at TEXT NOT NULL
            )
        ''')

        # Tabela configuracoes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS configuracoes (
                chave TEXT PRIMARY KEY,
                valor TEXT NOT NULL,
                atualizado_em TEXT NOT NULL
            )
        ''')

        # Configurações padrão
        defaults = [
            ('taxa_entrega', '5.00'),
            ('tempo_entrega', '45'),
            ('telefone_contato', '(11) 99999-9999'),
            ('horario_funcionamento', '18:00-23:00'),
            ('mensagem_boas_vindas', 'Bem-vindo à Pizzaria Romeo! 🍕'),
            ('valor_minimo_entrega', '30.00')
        ]

        for chave, valor in defaults:
            cursor.execute('''
                INSERT OR IGNORE INTO configuracoes (chave, valor, atualizado_em)
                VALUES (?, ?, ?)
            ''', (chave, valor, datetime.now(timezone.utc).isoformat()))

        self.sqlite_conn.commit()
        logger.log("debug", "✅ Tabelas SQLite criadas/verificadas")

    def salvar_pedido(self, pedido_data: Dict) -> Tuple[bool, str, str]:
        """Salva pedido em ambos os bancos se possível"""
        # Gerar código único para o pedido
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_hash = hashlib.md5(str(time.time()).encode()).hexdigest()[:6].upper()
        codigo = f"PED{timestamp}{random_hash}"
        pedido_data['codigo_pedido'] = codigo

        logger.log("info", f"💾 Salvando pedido {codigo}...")

        resultado_supabase = False
        resultado_sqlite = False

        # 1. Tentar Supabase
        if self.supabase:
            try:
                response = self.supabase.table("pedidos").insert(pedido_data).execute()
                resultado_supabase = bool(response.data)
                if resultado_supabase:
                    logger.log("success", f"✅ Pedido {codigo} salvo no Supabase")
            except Exception as e:
                logger.log("warning", f"⚠️ Falha no Supabase: {str(e)[:100]}")

        # 2. Sempre salvar no SQLite (backup obrigatório)
        if self.sqlite_conn:
            try:
                cursor = self.sqlite_conn.cursor()
                columns = ', '.join(pedido_data.keys())
                placeholders = ', '.join(['?' for _ in pedido_data])

                sql = f"INSERT OR REPLACE INTO pedidos ({columns}) VALUES ({placeholders})"
                cursor.execute(sql, list(pedido_data.values()))

                self.sqlite_conn.commit()
                resultado_sqlite = True
                logger.log("success", f"✅ Pedido {codigo} salvo no SQLite")

            except Exception as e:
                logger.log("error", f"❌ Erro SQLite: {e}")

        # Determinar fonte principal
        fonte_principal = "supabase" if resultado_supabase else "sqlite" if resultado_sqlite else None

        sucesso = resultado_supabase or resultado_sqlite
        if sucesso:
            logger.log("success", f"🎉 Pedido {codigo} salvo com sucesso (Fonte: {fonte_principal})")

        return sucesso, codigo, fonte_principal

    def buscar_pedidos(self, filtros: Dict = None, limite: int = 50) -> List[Dict]:
        """Busca pedidos com filtros"""
        pedidos = []

        if self.modo_atual == "supabase" and self.supabase:
            try:
                query = self.supabase.table("pedidos").select("*")

                if filtros:
                    for key, value in filtros.items():
                        if value:
                            query = query.eq(key, value)

                response = query.order("created_at", desc=True).limit(limite).execute()
                pedidos = [dict(p) for p in response.data]

            except Exception as e:
                logger.log("warning", f"⚠️ Erro ao buscar do Supabase: {e}")

        # Fallback para SQLite
        if not pedidos and self.sqlite_conn:
            try:
                cursor = self.sqlite_conn.cursor()
                sql = "SELECT * FROM pedidos WHERE 1=1"
                params = []

                if filtros:
                    for key, value in filtros.items():
                        if value:
                            sql += f" AND {key} = ?"
                            params.append(value)

                sql += " ORDER BY created_at DESC LIMIT ?"
                params.append(limite)

                cursor.execute(sql, params)
                pedidos = [dict(row) for row in cursor.fetchall()]

            except Exception as e:
                logger.log("error", f"❌ Erro ao buscar do SQLite: {e}")

        return pedidos

    def atualizar_status_pedido(self, pedido_id: str, novo_status: str, motivo: str = None) -> bool:
        """Atualiza status de um pedido"""
        sucesso = False

        logger.log("info", f"🔄 Atualizando pedido {pedido_id} para status: {novo_status}")

        update_data = {
            "status": novo_status,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }

        if motivo:
            update_data["observacoes"] = f"{datetime.now().strftime('%H:%M')} - Status alterado: {motivo}"

        # Atualizar no Supabase
        if self.supabase:
            try:
                response = self.supabase.table("pedidos").update(update_data).eq("codigo_pedido", pedido_id).execute()
                sucesso = bool(response.data)
            except Exception as e:
                logger.log("warning", f"⚠️ Erro ao atualizar no Supabase: {e}")

        # Atualizar no SQLite
        if self.sqlite_conn:
            try:
                cursor = self.sqlite_conn.cursor()

                # Buscar observações atuais
                cursor.execute("SELECT observacoes FROM pedidos WHERE codigo_pedido = ?", (pedido_id,))
                resultado = cursor.fetchone()
                observacoes_atuais = dict(resultado)['observacoes'] if resultado else ""

                # Adicionar nova observação
                nova_observacao = f"\n{update_data['observacoes']}" if 'observacoes' in update_data else ""
                observacoes_final = observacoes_atuais + nova_observacao if observacoes_atuais else nova_observacao.lstrip()

                cursor.execute('''
                    UPDATE pedidos 
                    SET status = ?, observacoes = ?, updated_at = ?
                    WHERE codigo_pedido = ?
                ''', (novo_status, observacoes_final.strip(), update_data['updated_at'], pedido_id))

                self.sqlite_conn.commit()
                sucesso = cursor.rowcount > 0 or sucesso

            except Exception as e:
                logger.log("error", f"❌ Erro ao atualizar no SQLite: {e}")

        if sucesso:
            logger.log("success", f"✅ Status do pedido {pedido_id} atualizado para {novo_status}")
        else:
            logger.log("error", f"❌ Falha ao atualizar pedido {pedido_id}")

        return sucesso

    def salvar_anuncio(self, anuncio_data: Dict) -> bool:
        """Salva um novo anúncio"""
        sucesso = False

        logger.log("info", "📢 Salvando novo anúncio...")

        # Salvar no Supabase
        if self.supabase:
            try:
                response = self.supabase.table("anuncios").insert(anuncio_data).execute()
                sucesso = bool(response.data)
            except Exception as e:
                logger.log("warning", f"⚠️ Erro ao salvar anúncio no Supabase: {e}")

        # Sempre salvar no SQLite
        if self.sqlite_conn:
            try:
                cursor = self.sqlite_conn.cursor()
                columns = ', '.join(anuncio_data.keys())
                placeholders = ', '.join(['?' for _ in anuncio_data])

                cursor.execute(f'''
                    INSERT INTO anuncios ({columns})
                    VALUES ({placeholders})
                ''', list(anuncio_data.values()))

                self.sqlite_conn.commit()
                sucesso = True

            except Exception as e:
                logger.log("error", f"❌ Erro ao salvar anúncio no SQLite: {e}")

        if sucesso:
            logger.log("success", f"✅ Anúncio salvo: {anuncio_data.get('titulo', 'Sem título')}")
        else:
            logger.log("error", "❌ Falha ao salvar anúncio")

        return sucesso

    def buscar_anuncios_ativos(self, tipo: str = None) -> List[Dict]:
        """Busca anúncios ativos"""
        anuncios = []

        if self.modo_atual == "supabase" and self.supabase:
            try:
                query = self.supabase.table("anuncios").select("*").eq("ativo", True)
                if tipo:
                    query = query.eq("tipo", tipo)

                response = query.order("prioridade", desc=True).order("criado_em", desc=True).execute()
                anuncios = [dict(a) for a in response.data]

            except Exception as e:
                logger.log("warning", f"⚠️ Erro ao buscar anúncios do Supabase: {e}")

        # Fallback para SQLite
        if self.sqlite_conn:
            try:
                cursor = self.sqlite_conn.cursor()
                sql = "SELECT * FROM anuncios WHERE ativo = 1"
                params = []

                if tipo:
                    sql += " AND tipo = ?"
                    params.append(tipo)

                sql += " ORDER BY prioridade DESC, criado_em DESC"
                cursor.execute(sql, params)
                anuncios = [dict(row) for row in cursor.fetchall()]

            except Exception as e:
                logger.log("error", f"❌ Erro ao buscar anúncios do SQLite: {e}")

        return anuncios

    def get_estatisticas(self) -> Dict:
        """Retorna estatísticas do sistema"""
        pedidos = self.buscar_pedidos(limite=1000)
        anuncios = self.buscar_anuncios_ativos()

        hoje = datetime.now().date()
        pedidos_hoje = [
            p for p in pedidos 
            if datetime.fromisoformat(p['created_at']).date() == hoje
        ]

        # Calcular por status
        por_status = {}
        for pedido in pedidos:
            status = pedido.get('status', 'pendente')
            por_status[status] = por_status.get(status, 0) + 1

        # Calcular valores
        valor_total = sum(p.get('valor', 0) for p in pedidos)
        valor_medio = valor_total / len(pedidos) if pedidos else 0

        # Por pizza
        por_pizza = {}
        for pedido in pedidos:
            pizza = pedido.get('pizza', 'Desconhecida').split()[0]
            por_pizza[pizza] = por_pizza.get(pizza, 0) + 1

        return {
            "total_pedidos": len(pedidos),
            "pedidos_hoje": len(pedidos_hoje),
            "anuncios_ativos": len(anuncios),
            "por_status": por_status,
            "valor_total": valor_total,
            "valor_medio": valor_medio,
            "por_pizza": por_pizza,
            "modo_banco": self.modo_atual
        }

    def get_modo(self):
        return self.modo_atual

# Inicializar banco de dados
db = DatabaseManager()

# ==================== SISTEMA DE PEDIDOS ====================
class SistemaPedidos:
    """Sistema de gerenciamento de pedidos"""

    TAXA_ENTREGA = 5.00

    def calcular_valor(self, sabor: str, tamanho: str = "grande") -> float:
        """Calcula valor do pedido"""
        sabor_info = PizzaSabor.SABORES.get(sabor.lower())
        if not sabor_info:
            return 40.00  # Valor padrão

        tamanho_info = PizzaSabor.TAMANHOS.get(tamanho.lower(), PizzaSabor.TAMANHOS["grande"])
        valor_base = sabor_info["preco"]
        multiplicador = tamanho_info["multiplicador"]

        return round(valor_base * multiplicador, 2)

    def criar_pedido_data(self, chat_id: str, dados: Dict) -> Dict:
        """Cria estrutura de dados do pedido"""
        sabor = dados['pizza'].split()[0].lower()
        tamanho = dados.get('tamanho', 'grande').lower()
        valor_pizza = self.calcular_valor(sabor, tamanho)

        return {
            "user_id": str(chat_id),
            "nome": dados['nome'],
            "pizza": dados['pizza'],
            "tamanho": PizzaSabor.TAMANHOS.get(tamanho, {}).get("nome", "Grande"),
            "endereco": dados['endereco'],
            "telefone": dados.get('telefone', 'Não informado'),
            "idade": dados.get('idade', 'Não informado'),
            "pagamento": dados['pagamento'],
            "observacoes": dados.get('observacoes', ''),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "pendente",
            "valor": valor_pizza,
            "taxa_entrega": self.TAXA_ENTREGA,
            "fonte": db.get_modo()
        }

    def formatar_resumo_pedido(self, pedido_data: Dict, codigo: str) -> str:
        """Formata resumo do pedido para o cliente"""
        valor_total = pedido_data['valor'] + pedido_data['taxa_entrega']
        status_info = PizzaSabor.STATUS.get(pedido_data['status'], {"nome": "Pendente", "emoji": "🟡"})

        return f"""
{status_info['emoji']} *PEDIDO CONFIRMADO!* 🎉

📋 *CÓDIGO:* `{codigo}`
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🍕 *Pizza:* {pedido_data['pizza']}
📏 *Tamanho:* {pedido_data['tamanho']}
👤 *Cliente:* {pedido_data['nome']}
📱 *Telefone:* {pedido_data['telefone']}
🏠 *Endereço:* {pedido_data['endereco']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💳 *Pagamento:* {pedido_data['pagamento']}
💰 *Valor pizza:* R$ {pedido_data['valor']:.2f}
🚚 *Taxa entrega:* R$ {pedido_data['taxa_entrega']:.2f}
💵 *Total a pagar:* R$ {valor_total:.2f}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 *Observações:* {pedido_data['observacoes'] or 'Nenhuma'}
📊 *Status:* {status_info['nome']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏰ *Previsão de entrega:* 30-45 minutos
📞 *Dúvidas:* (11) 99999-9999

*Agradecemos sua preferência!* 🍕
"""

sistema_pedidos = SistemaPedidos()

# ==================== SISTEMA DE ADMIN ====================
class SistemaAdmin:
    """Sistema de administração"""

    @staticmethod
    def is_admin(chat_id: int) -> bool:
        """Verifica se o usuário é administrador"""
        return chat_id == DONO_ID

    @staticmethod
    def formatar_pedidos_para_admin(pedidos: List[Dict]) -> str:
        """Formata lista de pedidos para visualização do admin"""
        if not pedidos:
            return "📭 *Nenhum pedido encontrado.*"

        resposta = f"📊 *TOTAL DE PEDIDOS:* {len(pedidos)}\n\n"

        for i, pedido in enumerate(pedidos[:15], 1):
            status_info = PizzaSabor.STATUS.get(pedido.get('status', 'pendente'), {"nome": "Pendente", "emoji": "🟡"})

            resposta += f"{status_info['emoji']} *Pedido #{i}*\n"
            resposta += f"📋 `{pedido.get('codigo_pedido', 'N/A')}`\n"
            resposta += f"👤 {pedido.get('nome', 'N/A')}\n"
            resposta += f"🍕 {pedido.get('pizza', 'N/A')}\n"
            resposta += f"📍 {pedido.get('endereco', 'N/A')[:30]}...\n"
            resposta += f"💰 R$ {pedido.get('valor', 0):.2f} | 📊 {pedido.get('status', 'pendente').title()}\n"
            resposta += f"📅 {pedido.get('created_at', '')[:16]}\n"
            resposta += "━━━━━━━━━━━━━━\n"

        if len(pedidos) > 15:
            resposta += f"\n*... e mais {len(pedidos) - 15} pedidos*"

        return resposta

admin = SistemaAdmin()

# ==================== HANDLERS DE COMANDOS ====================
# Dados temporários dos usuários
user_sessions = {}

@bot.message_handler(commands=['start', 'menu', 'cardapio'])
def comando_menu(mensagem):
    """Menu principal com anúncios"""
    chat_id = mensagem.chat.id

    # Limpar sessão anterior
    if chat_id in user_sessions:
        del user_sessions[chat_id]

    logger.log("info", f"Usuário {chat_id} acessou o menu")

    # Mostrar anúncios ativos
    anuncios = db.buscar_anuncios_ativos(tipo="geral")
    if anuncios:
        for anuncio in anuncios[:2]:  # Máximo 2 anúncios
            try:
                bot.send_message(
                    chat_id,
                    f"📢 *{anuncio['titulo']}*\n\n{anuncio['mensagem']}\n\n━━━━━━━━━━━━━━",
                    parse_mode="Markdown"
                )
                time.sleep(0.3)
            except Exception as e:
                logger.log("error", f"Erro ao enviar anúncio: {e}")

    # Menu principal
    menu_texto = """
*🍕 *PIZZARIA ROMEO* 🍕*
_Sabores que conquistam corações!_

*🎯 COMO FAZER PEDIDO:*
1. Escolha um sabor abaixo
2. Preencha seus dados
3. Confirme o pedido
4. Acompanhe o status
5. Pizza entregue! 🚚

*📍 ÁREA DE ENTREGA:*
• Centro • Jardins • Vila Nova
• Zona Sul (consulte disponibilidade)

*⏰ HORÁRIO DE FUNCIONAMENTO:*
Todos os dias: 18:00 - 23:00

━━━━━━━━━━━━━━━━━━━━━━
*🎨 ESCOLHA SEU SABOR:*

*SALGADAS 🧂*
/calabresa - Calabresa tradicional
/portuguesa - Portuguesa completa  
/marguerita - Marguerita clássica
/frango - Frango c/ Catupiry
/quatroqueijos - 4 Queijos especiais

*DOCES 🍬*
/chocolate - Chocolate ao leite
/romeuejulieta - Goiabada c/ Queijo

━━━━━━━━━━━━━━━━━━━━━━
*🛠️ OUTROS COMANDOS:*
/status - Ver status do pedido
/ajuda - Ajuda e contato
/promocoes - Promoções ativas
"""

    bot.send_message(chat_id, menu_texto)

    # Se for admin, mostrar opção
    if admin.is_admin(chat_id):
        bot.send_message(chat_id, "👑 *Modo Administrador Ativo*\nUse /admin para acessar o painel completo")

@bot.message_handler(commands=['calabresa', 'portuguesa', 'marguerita', 'frango', 'quatroqueijos', 'chocolate', 'romeuejulieta'])
def iniciar_pedido(mensagem):
    """Inicia um novo pedido"""
    chat_id = mensagem.chat.id
    comando = mensagem.text.replace("/", "").lower()

    if comando not in PizzaSabor.SABORES:
        bot.send_message(chat_id, "❌ Sabor não encontrado. Use /menu para ver as opções.")
        return

    sabor_info = PizzaSabor.SABORES[comando]

    # Iniciar sessão
    user_sessions[chat_id] = {
        'pizza': sabor_info['nome'],
        'descricao': sabor_info['desc'],
        'preco_base': sabor_info['preco'],
        'etapa': 'nome',
        'timestamp': time.time()
    }

    logger.log("info", f"Iniciando pedido de {comando} para {chat_id}")

    # Responder
    resposta = f"""
{sabor_info['emoji']} *{sabor_info['nome']}*

*{sabor_info['desc']}*

💰 *Valor (Grande):* R$ {sabor_info['preco']:.2f}
📏 *Tamanho padrão:* Grande (35cm)

Vamos começar seu pedido! 🎉

*1️⃣ Qual seu nome completo?*
"""

    bot.send_message(chat_id, resposta)

# Handler para processar etapas do pedido
@bot.message_handler(func=lambda m: m.chat.id in user_sessions and user_sessions[m.chat.id].get('etapa') in ['nome', 'telefone', 'endereco', 'idade', 'tamanho', 'pagamento', 'observacoes'])
def processar_etapa_pedido(mensagem):
    """Processa cada etapa do pedido"""
    chat_id = mensagem.chat.id
    sessao = user_sessions[chat_id]
    etapa = sessao['etapa']
    texto = mensagem.text.strip()

    try:
        if etapa == 'nome':
            if len(texto) < 3:
                bot.send_message(chat_id, "❌ Nome muito curto. Digite seu nome completo:")
                return

            sessao['nome'] = texto
            sessao['etapa'] = 'telefone'

            bot.send_message(
                chat_id, 
                f"✅ Obrigado, *{texto.split()[0]}*! 😊\n\n"
                f"*2️⃣ Qual seu número de telefone?*\n"
                f"(Com DDD, ex: 11 99999-9999)"
            )

        elif etapa == 'telefone':
            # Validar telefone (simplificado)
            numeros = ''.join(filter(str.isdigit, texto))
            if len(numeros) < 10 or len(numeros) > 11:
                bot.send_message(chat_id, "❌ Telefone inválido. Digite um número com DDD (ex: 11 99999-9999):")
                return

            # Formatar telefone
            if len(numeros) == 10:
                telefone_formatado = f"({numeros[:2]}) {numeros[2:6]}-{numeros[6:]}"
            else:
                telefone_formatado = f"({numeros[:2]}) {numeros[2:7]}-{numeros[7:]}"

            sessao['telefone'] = telefone_formatado
            sessao['etapa'] = 'endereco'

            bot.send_message(
                chat_id,
                "*3️⃣ Qual o endereço de entrega?*\n"
                "(Rua, número, bairro, complemento)\n"
                "*Exemplo:* Rua das Flores, 123 - Centro"
            )

        elif etapa == 'endereco':
            if len(texto) < 10:
                bot.send_message(chat_id, "❌ Endereço muito curto. Digite um endereço completo:")
                return

            sessao['endereco'] = texto
            sessao['etapa'] = 'idade'

            bot.send_message(
                chat_id,
                "*4️⃣ Para registro, qual sua idade?*\n"
                "(Apenas número, ex: 25)"
            )

        elif etapa == 'idade':
            try:
                idade = int(texto)
                if idade < 1 or idade > 120:
                    raise ValueError
                sessao['idade'] = str(idade)
                sessao['etapa'] = 'tamanho'

                # Oferecer tamanhos
                markup = telebot.types.ReplyKeyboardMarkup(
                    one_time_keyboard=True, 
                    resize_keyboard=True,
                    row_width=2
                )

                for tamanho_key, tamanho_info in PizzaSabor.TAMANHOS.items():
                    texto_botao = f"{tamanho_info['nome']} ({tamanho_info['diametro']})"
                    markup.add(texto_botao)

                bot.send_message(
                    chat_id,
                    "*5️⃣ Escolha o tamanho da pizza:*\n\n"
                    "📏 *Tamanhos disponíveis:*\n"
                    "• Pequena (25cm) - 4 fatias\n"
                    "• Média (30cm) - 6 fatias\n"
                    "• Grande (35cm) - 8 fatias\n"
                    "• Família (45cm) - 12 fatias",
                    reply_markup=markup
                )

            except ValueError:
                bot.send_message(chat_id, "❌ Idade inválida. Digite um número entre 1 e 120:")

        elif etapa == 'tamanho':
            # Identificar tamanho selecionado
            tamanho_selecionado = None
            for tamanho_key, tamanho_info in PizzaSabor.TAMANHOS.items():
                if tamanho_info['nome'].lower() in texto.lower():
                    tamanho_selecionado = tamanho_key
                    break

            if not tamanho_selecionado:
                tamanho_selecionado = 'grande'  # Padrão

            sessao['tamanho'] = tamanho_selecionado
            sessao['etapa'] = 'pagamento'

            # Calcular valor
            sabor = sessao['pizza'].split()[0].lower()
            tamanho_info = PizzaSabor.TAMANHOS[tamanho_selecionado]
            valor = sistema_pedidos.calcular_valor(sabor, tamanho_selecionado)
            valor_total = valor + sistema_pedidos.TAXA_ENTREGA

            markup = telebot.types.ReplyKeyboardMarkup(
                one_time_keyboard=True, 
                resize_keyboard=True,
                row_width=2
            )
            markup.add('💵 Dinheiro', '💳 Cartão (crédito)', '💳 Cartão (débito)', '📱 PIX')

            bot.send_message(
                chat_id,
                f"*6️⃣ Escolha a forma de pagamento:*\n\n"
                f"💰 *Resumo do valor:*\n"
                f"• Pizza {tamanho_info['nome']}: R$ {valor:.2f}\n"
                f"• Taxa de entrega: R$ {sistema_pedidos.TAXA_ENTREGA:.2f}\n"
                f"• *Total: R$ {valor_total:.2f}*",
                reply_markup=markup
            )

        elif etapa == 'pagamento':
            sessao['pagamento'] = texto
            sessao['etapa'] = 'observacoes'

            markup = telebot.types.ReplyKeyboardRemove()
            bot.send_message(
                chat_id,
                "*7️⃣ Alguma observação ou instrução especial?*\n\n"
                "Exemplos:\n"
                "• 'Sem cebola'\n"
                "• 'Portão azul'\n"
                "• 'Tirar azeitona'\n\n"
                "Ou digite *OK* para pular.",
                reply_markup=markup
            )

        elif etapa == 'observacoes':
            if texto.upper() == 'OK' or texto.lower() == 'nenhuma':
                sessao['observacoes'] = ''
            else:
                sessao['observacoes'] = texto

            # Finalizar pedido
            finalizar_pedido_completo(chat_id)

    except Exception as e:
        logger.log("error", f"Erro no processamento do pedido: {e}", chat_id)
        bot.send_message(
            chat_id, 
            "❌ Ocorreu um erro no processamento. Por favor, comece novamente com /menu"
        )
        if chat_id in user_sessions:
            del user_sessions[chat_id]

def finalizar_pedido_completo(chat_id):
    """Finaliza o pedido e salva no banco"""
    try:
        sessao = user_sessions[chat_id]

        # Verificar timeout (30 minutos)
        if time.time() - sessao.get('timestamp', 0) > 1800:
            bot.send_message(chat_id, "⏰ *Sessão expirada!*\nPor favor, inicie um novo pedido com /menu")
            if chat_id in user_sessions:
                del user_sessions[chat_id]
            return

        # Criar dados do pedido
        pedido_data = sistema_pedidos.criar_pedido_data(chat_id, sessao)

        # Mostrar processamento
        mensagem_processando = bot.send_message(
            chat_id, 
            "⏳ *Processando seu pedido...*\n\n"
            "📦 Gerando código único...\n"
            "💾 Salvando no sistema...\n"
            "✅ Confirmando disponibilidade..."
        )

        # Salvar no banco
        sucesso, codigo, fonte = db.salvar_pedido(pedido_data)

        if sucesso:
            # Editar mensagem de processamento
            bot.edit_message_text(
                "✅ *Pedido processado com sucesso!*",
                chat_id=chat_id,
                message_id=mensagem_processando.message_id
            )

            # Enviar resumo completo
            resumo = sistema_pedidos.formatar_resumo_pedido(pedido_data, codigo)
            bot.send_message(chat_id, resumo)

            # Enviar notificação para admin se for diferente do cliente
            if not admin.is_admin(chat_id):
                try:
                    bot.send_message(
                        DONO_ID,
                        f"📦 *NOVO PEDIDO RECEBIDO!*\n\n"
                        f"📋 Código: `{codigo}`\n"
                        f"👤 Cliente: {sessao['nome']}\n"
                        f"🍕 Pizza: {sessao['pizza']}\n"
                        f"📍 Endereço: {sessao['endereco'][:50]}...\n"
                        f"💰 Valor: R$ {pedido_data['valor']:.2f}\n"
                        f"📱 Telefone: {sessao['telefone']}\n\n"
                        f"💾 Salvo em: {fonte.upper()}"
                    )
                except Exception as e:
                    logger.log("error", f"Erro ao notificar admin: {e}")

            logger.log("success", f"Pedido {codigo} finalizado para {chat_id}")
        else:
            bot.edit_message_text(
                "❌ *Não foi possível processar seu pedido.*\n\n"
                "Por favor, tente novamente ou entre em contato:\n"
                "📞 (11) 99999-9999",
                chat_id=chat_id,
                message_id=mensagem_processando.message_id
            )
            logger.log("error", f"Falha ao salvar pedido para {chat_id}")

    except Exception as e:
        logger.log("error", f"Erro ao finalizar pedido: {e}", chat_id)
        bot.send_message(
            chat_id, 
            "❌ Ocorreu um erro ao processar seu pedido.\n"
            "Por favor, tente novamente ou entre em contato."
        )

    finally:
        # Limpar sessão
        if chat_id in user_sessions:
            del user_sessions[chat_id]

# ==================== COMANDOS DE ADMINISTRAÇÃO ====================

@bot.message_handler(commands=['admin'])
def comando_admin(mensagem):
    """Painel de administração"""
    chat_id = mensagem.chat.id

    if not admin.is_admin(chat_id):
        bot.send_message(chat_id, "❌ *Acesso negado!*\nEste comando é apenas para administradores.")
        return

    estatisticas = db.get_estatisticas()

    menu_admin = f"""
*👑 PAINEL DE ADMINISTRAÇÃO*

*📊 Status do Sistema:*
💾 Banco: *{db.get_modo().upper()}*
📦 Pedidos totais: *{estatisticas['total_pedidos']}*
📅 Pedidos hoje: *{estatisticas['pedidos_hoje']}*
📢 Anúncios ativos: *{estatisticas['anuncios_ativos']}*

*📦 GESTÃO DE PEDIDOS:*
/pedidos - Ver todos os pedidos
/pedidos_hoje - Pedidos de hoje
/pedidos_pendentes - Pedidos pendentes
/buscar_pedido - Buscar pedido específico
/cancelar_pedido - Cancelar pedido
/status_pedido - Alterar status

*📢 COMUNICAÇÃO:*
/anunciar - Criar anúncio
/anuncios - Ver anúncios ativos
/remover_anuncio - Remover anúncio
/enviar_mensagem - Mensagem para cliente

*📊 RELATÓRIOS:*
/relatorio - Relatório completo
/estatisticas - Estatísticas detalhadas
/backup - Criar backup dos dados

*⚙️ SISTEMA:*
/config - Configurações do sistema
/logs - Ver logs do sistema
/status_sistema - Status detalhado
/reiniciar - Reiniciar conexões
"""

    bot.send_message(chat_id, menu_admin)

@bot.message_handler(commands=['pedidos'])
def comando_ver_pedidos(mensagem):
    """Ver todos os pedidos"""
    chat_id = mensagem.chat.id

    if not admin.is_admin(chat_id):
        bot.send_message(chat_id, "❌ *Acesso negado!*")
        return

    pedidos = db.buscar_pedidos(limite=50)
    resposta = admin.formatar_pedidos_para_admin(pedidos)

    bot.send_message(chat_id, resposta)

@bot.message_handler(commands=['pedidos_hoje'])
def comando_pedidos_hoje(mensagem):
    """Pedidos de hoje"""
    chat_id = mensagem.chat.id

    if not admin.is_admin(chat_id):
        bot.send_message(chat_id, "❌ *Acesso negado!*")
        return

    hoje = datetime.now().date()
    todos_pedidos = db.buscar_pedidos(limite=200)
    pedidos_hoje = [
        p for p in todos_pedidos 
        if datetime.fromisoformat(p['created_at']).date() == hoje
    ]

    resposta = f"📅 *PEDIDOS DE HOJE ({hoje.strftime('%d/%m/%Y')})*\n\n"
    resposta += admin.formatar_pedidos_para_admin(pedidos_hoje)

    bot.send_message(chat_id, resposta)

@bot.message_handler(commands=['pedidos_pendentes'])
def comando_pedidos_pendentes(mensagem):
    """Pedidos pendentes"""
    chat_id = mensagem.chat.id

    if not admin.is_admin(chat_id):
        bot.send_message(chat_id, "❌ *Acesso negado!*")
        return

    pedidos_pendentes = db.buscar_pedidos(filtros={"status": "pendente"})

    resposta = f"🟡 *PEDIDOS PENDENTES: {len(pedidos_pendentes)}*\n\n"
    resposta += admin.formatar_pedidos_para_admin(pedidos_pendentes)

    bot.send_message(chat_id, resposta)

@bot.message_handler(commands=['cancelar_pedido'])
def comando_cancelar_pedido(mensagem):
    """Cancelar um pedido"""
    chat_id = mensagem.chat.id

    if not admin.is_admin(chat_id):
        bot.send_message(chat_id, "❌ *Acesso negado!*")
        return

    bot.send_message(
        chat_id,
        "❌ *CANCELAR PEDIDO*\n\nDigite o *código do pedido* que deseja cancelar (ex: PED20241225123045ABCDEF):"
    )

    bot.register_next_step_handler(mensagem, processar_cancelamento)

def processar_cancelamento(mensagem):
    """Processa o cancelamento do pedido"""
    chat_id = mensagem.chat.id
    codigo = mensagem.text.strip().upper()

    if not codigo.startswith('PED'):
        bot.send_message(chat_id, "❌ Código inválido. Deve começar com 'PED'")
        return

    # Pedir motivo
    user_sessions[chat_id] = {
        'acao': 'cancelar_pedido',
        'codigo': codigo
    }

    markup = telebot.types.ReplyKeyboardMarkup(
        one_time_keyboard=True, 
        resize_keyboard=True,
        row_width=2
    )
    markup.add('Cliente solicitou', 'Fora da área', 'Estoque insuficiente', 'Outro motivo')

    bot.send_message(
        chat_id,
        "📝 *Selecione ou digite o motivo do cancelamento:*",
        reply_markup=markup
    )

    bot.register_next_step_handler(mensagem, processar_motivo_cancelamento)

def processar_motivo_cancelamento(mensagem):
    """Processa o motivo do cancelamento"""
    chat_id = mensagem.chat.id

    if chat_id not in user_sessions:
        bot.send_message(chat_id, "❌ Sessão expirada.")
        return

    motivo = mensagem.text
    codigo = user_sessions[chat_id]['codigo']

    # Cancelar pedido
    sucesso = db.atualizar_status_pedido(codigo, "cancelado", motivo)

    if sucesso:
        resposta = f"""
✅ *PEDIDO CANCELADO*

📋 *Código:* `{codigo}`
📝 *Motivo:* {motivo}
⏰ *Cancelado em:* {datetime.now().strftime('%H:%M')}

_O pedido foi marcado como cancelado no sistema._
"""
        bot.send_message(chat_id, resposta, reply_markup=telebot.types.ReplyKeyboardRemove())
    else:
        bot.send_message(chat_id, f"❌ Pedido `{codigo}` não encontrado ou já cancelado.")

    # Limpar sessão
    if chat_id in user_sessions:
        del user_sessions[chat_id]

@bot.message_handler(commands=['status_pedido'])
def comando_status_pedido(mensagem):
    """Alterar status de um pedido"""
    chat_id = mensagem.chat.id

    if not admin.is_admin(chat_id):
        bot.send_message(chat_id, "❌ *Acesso negado!*")
        return

    bot.send_message(
        chat_id,
        "🔄 *ALTERAR STATUS DO PEDIDO*\n\nDigite o *código do pedido*:"
    )

    bot.register_next_step_handler(mensagem, processar_codigo_status)

def processar_codigo_status(mensagem):
    """Processa código para alterar status"""
    chat_id = mensagem.chat.id
    codigo = mensagem.text.strip().upper()

    if not codigo.startswith('PED'):
        bot.send_message(chat_id, "❌ Código inválido.")
        return

    # Salvar na sessão
    user_sessions[chat_id] = {
        'acao': 'alterar_status',
        'codigo': codigo
    }

    # Mostrar opções de status
    markup = telebot.types.ReplyKeyboardMarkup(
        one_time_keyboard=True, 
        resize_keyboard=True,
        row_width=2
    )

    for status_key, status_info in PizzaSabor.STATUS.items():
        markup.add(f"{status_info['emoji']} {status_info['nome']}")

    bot.send_message(
        chat_id,
        "📊 *Selecione o novo status:*",
        reply_markup=markup
    )

    bot.register_next_step_handler(mensagem, processar_novo_status)

def processar_novo_status(mensagem):
    """Processa novo status do pedido"""
    chat_id = mensagem.chat.id

    if chat_id not in user_sessions:
        bot.send_message(chat_id, "❌ Sessão expirada.")
        return

    # Identificar status selecionado
    texto = mensagem.text
    novo_status = None

    for status_key, status_info in PizzaSabor.STATUS.items():
        if status_info['emoji'] in texto or status_info['nome'].lower() in texto.lower():
            novo_status = status_key
            break

    if not novo_status:
        novo_status = 'pendente'

    codigo = user_sessions[chat_id]['codigo']

    # Atualizar status
    sucesso = db.atualizar_status_pedido(codigo, novo_status)

    if sucesso:
        status_info = PizzaSabor.STATUS.get(novo_status, {"nome": "Pendente", "emoji": "🟡"})
        resposta = f"""
✅ *STATUS ATUALIZADO*

{status_info['emoji']} *Código:* `{codigo}`
📊 *Novo status:* {status_info['nome']}
⏰ *Atualizado em:* {datetime.now().strftime('%H:%M')}
"""
        bot.send_message(chat_id, resposta, reply_markup=telebot.types.ReplyKeyboardRemove())
    else:
        bot.send_message(chat_id, f"❌ Pedido `{codigo}` não encontrado.")

    # Limpar sessão
    if chat_id in user_sessions:
        del user_sessions[chat_id]

@bot.message_handler(commands=['buscar_pedido'])
def comando_buscar_pedido(mensagem):
    """Buscar pedido específico"""
    chat_id = mensagem.chat.id

    if not admin.is_admin(chat_id):
        bot.send_message(chat_id, "❌ *Acesso negado!*")
        return

    bot.send_message(
        chat_id,
        "🔍 *BUSCAR PEDIDO*\n\nDigite o *código do pedido* ou *nome do cliente*:"
    )

    bot.register_next_step_handler(mensagem, processar_busca_pedido)

def processar_busca_pedido(mensagem):
    """Processa busca de pedido"""
    chat_id = mensagem.chat.id
    termo = mensagem.text.strip()

    # Buscar pedidos
    todos_pedidos = db.buscar_pedidos(limite=100)
    resultados = []

    for pedido in todos_pedidos:
        if (termo.upper() in pedido.get('codigo_pedido', '').upper() or
            termo.lower() in pedido.get('nome', '').lower() or
            termo in pedido.get('telefone', '')):
            resultados.append(pedido)

    if resultados:
        resposta = f"🔍 *RESULTADOS DA BUSCA: {len(resultados)}*\n\n"
        resposta += admin.formatar_pedidos_para_admin(resultados)
    else:
        resposta = f"❌ *Nenhum pedido encontrado para:* {termo}"

    bot.send_message(chat_id, resposta)

@bot.message_handler(commands=['anunciar'])
def comando_anunciar(mensagem):
    """Criar um anúncio"""
    chat_id = mensagem.chat.id

    if not admin.is_admin(chat_id):
        bot.send_message(chat_id, "❌ *Acesso negado!*")
        return

    # Iniciar criação de anúncio
    user_sessions[chat_id] = {
        'acao': 'criar_anuncio',
        'etapa': 'titulo'
    }

    bot.send_message(
        chat_id,
        "📢 *CRIAR NOVO ANÚNCIO*\n\n*1️⃣ Digite o título do anúncio:*\n(ex: 🎉 PROMOÇÃO ESPECIAL)"
    )

    bot.register_next_step_handler(mensagem, processar_titulo_anuncio)

def processar_titulo_anuncio(mensagem):
    """Processa título do anúncio"""
    chat_id = mensagem.chat.id

    if chat_id not in user_sessions or user_sessions[chat_id].get('acao') != 'criar_anuncio':
        bot.send_message(chat_id, "❌ Sessão expirada.")
        return

    user_sessions[chat_id]['titulo'] = mensagem.text
    user_sessions[chat_id]['etapa'] = 'mensagem'

    bot.send_message(
        chat_id,
        "*2️⃣ Agora digite a mensagem do anúncio:*\n(Máximo: 1000 caracteres)"
    )

    bot.register_next_step_handler(mensagem, processar_mensagem_anuncio)

def processar_mensagem_anuncio(mensagem):
    """Processa mensagem do anúncio"""
    chat_id = mensagem.chat.id

    if chat_id not in user_sessions or user_sessions[chat_id].get('acao') != 'criar_anuncio':
        bot.send_message(chat_id, "❌ Sessão expirada.")
        return

    if len(mensagem.text) > 1000:
        bot.send_message(chat_id, "❌ Mensagem muito longa. Máximo 1000 caracteres. Digite novamente:")
        bot.register_next_step_handler(mensagem, processar_mensagem_anuncio)
        return

    user_sessions[chat_id]['mensagem'] = mensagem.text
    user_sessions[chat_id]['etapa'] = 'tipo'

    markup = telebot.types.ReplyKeyboardMarkup(
        one_time_keyboard=True, 
        resize_keyboard=True
    )
    markup.add('📢 Geral', '🎉 Promoção', '⚠️ Aviso', '📋 Informativo')

    bot.send_message(
        chat_id,
        "*3️⃣ Selecione o tipo do anúncio:*",
        reply_markup=markup
    )

    bot.register_next_step_handler(mensagem, processar_tipo_anuncio)

def processar_tipo_anuncio(mensagem):
    """Processa tipo do anúncio"""
    chat_id = mensagem.chat.id

    if chat_id not in user_sessions or user_sessions[chat_id].get('acao') != 'criar_anuncio':
        bot.send_message(chat_id, "❌ Sessão expirada.")
        return

    # Determinar tipo
    texto = mensagem.text.lower()
    if 'promoção' in texto:
        tipo = 'promocao'
    elif 'aviso' in texto:
        tipo = 'aviso'
    elif 'informativo' in texto:
        tipo = 'informativo'
    else:
        tipo = 'geral'

    user_sessions[chat_id]['tipo'] = tipo

    # Criar dados do anúncio
    anuncio_data = {
        "titulo": user_sessions[chat_id]['titulo'],
        "mensagem": user_sessions[chat_id]['mensagem'],
        "tipo": tipo,
        "prioridade": 1,
        "criado_em": datetime.now(timezone.utc).isoformat(),
        "ativo": True,
        "visualizacoes": 0
    }

    # Salvar anúncio
    sucesso = db.salvar_anuncio(anuncio_data)

    if sucesso:
        resposta = f"""
✅ *ANÚNCIO CRIADO COM SUCESSO!*

📢 *Título:* {anuncio_data['titulo']}
📝 *Mensagem:* {anuncio_data['mensagem'][:100]}...
📌 *Tipo:* {tipo.title()}
⏰ *Criado em:* {datetime.now().strftime('%H:%M')}

O anúncio será exibido para todos os usuários no próximo /menu
"""
        bot.send_message(chat_id, resposta, reply_markup=telebot.types.ReplyKeyboardRemove())
    else:
        bot.send_message(chat_id, "❌ Erro ao salvar anúncio. Tente novamente.")

    # Limpar sessão
    if chat_id in user_sessions:
        del user_sessions[chat_id]

@bot.message_handler(commands=['anuncios'])
def comando_ver_anuncios(mensagem):
    """Ver anúncios ativos"""
    chat_id = mensagem.chat.id

    if not admin.is_admin(chat_id):
        bot.send_message(chat_id, "❌ *Acesso negado!*")
        return

    anuncios = db.buscar_anuncios_ativos()

    if not anuncios:
        bot.send_message(chat_id, "📭 *Nenhum anúncio ativo no momento.*")
        return

    resposta = "📢 *ANÚNCIOS ATIVOS*\n\n"

    for i, anuncio in enumerate(anuncios, 1):
        tipo_emoji = {
            'geral': '📢',
            'promocao': '🎉',
            'aviso': '⚠️',
            'informativo': '📋'
        }.get(anuncio.get('tipo', 'geral'), '📢')

        prioridade_emoji = "🔴" if anuncio.get('prioridade', 1) == 3 else "🟡" if anuncio.get('prioridade', 1) == 2 else "🟢"

        resposta += f"{tipo_emoji}{prioridade_emoji} *{anuncio['titulo']}*\n"
        resposta += f"📝 {anuncio['mensagem'][:60]}...\n"
        resposta += f"📌 Tipo: {anuncio.get('tipo', 'geral').title()} | 🏷️ Prioridade: {anuncio.get('prioridade', 1)}\n"
        resposta += f"📅 {anuncio['criado_em'][:10]} | 👁️ {anuncio.get('visualizacoes', 0)} visualizações\n"
        resposta += f"🆔 ID: `{anuncio['id']}`\n"
        resposta += "━━━━━━━━━━━━━━\n"

    resposta += f"\n*Total:* {len(anuncios)} anúncio(s) ativo(s)"
    bot.send_message(chat_id, resposta)

@bot.message_handler(commands=['remover_anuncio'])
def comando_remover_anuncio(mensagem):
    """Remover um anúncio"""
    chat_id = mensagem.chat.id

    if not admin.is_admin(chat_id):
        bot.send_message(chat_id, "❌ *Acesso negado!*")
        return

    anuncios = db.buscar_anuncios_ativos()

    if not anuncios:
        bot.send_message(chat_id, "📭 Nenhum anúncio para remover.")
        return

    # Mostrar lista de anúncios
    resposta = "🗑️ *REMOVER ANÚNCIO*\n\n"
    resposta += "Selecione o ID do anúncio para remover:\n\n"

    for anuncio in anuncios[:10]:  # Limitar a 10
        resposta += f"`{anuncio['id']}` - {anuncio['titulo'][:30]}...\n"

    bot.send_message(chat_id, resposta)
    bot.register_next_step_handler(mensagem, processar_remocao_anuncio)

def processar_remocao_anuncio(mensagem):
    """Processa remoção de anúncio"""
    chat_id = mensagem.chat.id
    anuncio_id = mensagem.text.strip()

    try:
        # Tentar desativar no banco
        if db.sqlite_conn:
            cursor = db.sqlite_conn.cursor()
            cursor.execute("UPDATE anuncios SET ativo = 0 WHERE id = ?", (anuncio_id,))
            db.sqlite_conn.commit()

            if cursor.rowcount > 0:
                bot.send_message(chat_id, f"✅ Anúncio ID `{anuncio_id}` removido com sucesso!")
            else:
                bot.send_message(chat_id, f"❌ Anúncio ID `{anuncio_id}` não encontrado.")

        # Também tentar no Supabase se estiver ativo
        if db.supabase:
            try:
                db.supabase.table("anuncios").update({"ativo": False}).eq("id", anuncio_id).execute()
            except:
                pass

    except Exception as e:
        bot.send_message(chat_id, f"❌ Erro ao remover anúncio: {e}")

@bot.message_handler(commands=['enviar_mensagem'])
def comando_enviar_mensagem(mensagem):
    """Enviar mensagem para cliente"""
    chat_id = mensagem.chat.id

    if not admin.is_admin(chat_id):
        bot.send_message(chat_id, "❌ *Acesso negado!*")
        return

    bot.send_message(
        chat_id,
        "📨 *ENVIAR MENSAGEM PARA CLIENTE*\n\nDigite o *código do pedido*:"
    )

    bot.register_next_step_handler(mensagem, processar_mensagem_cliente)

def processar_mensagem_cliente(mensagem):
    """Processa envio de mensagem"""
    chat_id = mensagem.chat.id
    codigo = mensagem.text.strip().upper()

    # Buscar pedido
    pedidos = db.buscar_pedidos(filtros={"codigo_pedido": codigo})

    if not pedidos:
        bot.send_message(chat_id, f"❌ Pedido `{codigo}` não encontrado.")
        return

    pedido = pedidos[0]
    user_sessions[chat_id] = {
        'acao': 'enviar_mensagem',
        'codigo': codigo,
        'user_id': pedido['user_id']
    }

    bot.send_message(
        chat_id,
        f"👤 *Cliente:* {pedido['nome']}\n"
        f"📋 *Pedido:* {pedido['pizza']}\n"
        f"📱 *Telefone:* {pedido.get('telefone', 'Não informado')}\n\n"
        f"*Agora digite a mensagem:*"
    )

    bot.register_next_step_handler(mensagem, enviar_mensagem_final)

def enviar_mensagem_final(mensagem):
    """Envia a mensagem final para o cliente"""
    chat_id = mensagem.chat.id

    if chat_id not in user_sessions:
        bot.send_message(chat_id, "❌ Sessão expirada.")
        return

    texto_mensagem = mensagem.text
    user_id = user_sessions[chat_id]['user_id']
    codigo = user_sessions[chat_id]['codigo']

    try:
        # Enviar para o cliente
        bot.send_message(
            user_id,
            f"📨 *MENSAGEM DA PIZZARIA ROMEO*\n\n"
            f"{texto_mensagem}\n\n"
            f"📋 *Pedido:* {codigo}\n"
            f"📞 *Dúvidas:* (11) 99999-9999"
        )

        bot.send_message(
            chat_id, 
            f"✅ Mensagem enviada para o cliente do pedido `{codigo}`!"
        )

        logger.log("info", f"Mensagem enviada para cliente {user_id} (pedido {codigo})")

    except Exception as e:
        bot.send_message(chat_id, f"❌ Erro ao enviar mensagem: {e}")
        logger.log("error", f"Erro ao enviar mensagem: {e}")

    # Limpar sessão
    if chat_id in user_sessions:
        del user_sessions[chat_id]

@bot.message_handler(commands=['relatorio'])
def comando_relatorio(mensagem):
    """Relatório completo"""
    chat_id = mensagem.chat.id

    if not admin.is_admin(chat_id):
        bot.send_message(chat_id, "❌ *Acesso negado!*")
        return

    estatisticas = db.get_estatisticas()

    relatorio = f"""
📈 *RELATÓRIO COMPLETO - PIZZARIA ROMEO*

*📊 ESTATÍSTICAS GERAIS*
• Total de pedidos: *{estatisticas['total_pedidos']}*
• Pedidos hoje: *{estatisticas['pedidos_hoje']}*
• Anúncios ativos: *{estatisticas['anuncios_ativos']}*
• Valor total: *R$ {estatisticas['valor_total']:.2f}*
• Valor médio: *R$ {estatisticas['valor_medio']:.2f}*

*📋 DISTRIBUIÇÃO POR STATUS*
"""

    for status_key, status_info in PizzaSabor.STATUS.items():
        count = estatisticas['por_status'].get(status_key, 0)
        relatorio += f"{status_info['emoji']} {status_info['nome']}: *{count}*\n"

    # Top 5 pizzas mais pedidas
    relatorio += f"\n*🍕 TOP 5 PIZZAS MAIS PEDIDAS*\n"

    sorted_pizzas = sorted(
        estatisticas['por_pizza'].items(), 
        key=lambda x: x[1], 
        reverse=True
    )[:5]

    for pizza, count in sorted_pizzas:
        sabor_info = PizzaSabor.SABORES.get(pizza.lower(), {"emoji": "🍕"})
        relatorio += f"{sabor_info.get('emoji', '🍕')} {pizza.title()}: *{count}*\n"

    relatorio += f"""
*💾 INFORMAÇÕES DO SISTEMA*
• Banco de dados: *{estatisticas['modo_banco'].upper()}*
• Sessões ativas: *{len(user_sessions)}*
• Data do relatório: *{datetime.now().strftime('%d/%m/%Y %H:%M')}*
"""

    bot.send_message(chat_id, relatorio)

@bot.message_handler(commands=['estatisticas'])
def comando_estatisticas(mensagem):
    """Estatísticas rápidas"""
    chat_id = mensagem.chat.id

    if not admin.is_admin(chat_id):
        bot.send_message(chat_id, "❌ *Acesso negado!*")
        return

    estatisticas = db.get_estatisticas()

    resposta = f"""
📊 *ESTATÍSTICAS RÁPIDAS*

*📦 PEDIDOS*
• Total: *{estatisticas['total_pedidos']}*
• Hoje: *{estatisticas['pedidos_hoje']}*
• Valor total: *R$ {estatisticas['valor_total']:.2f}*

*📢 ANÚNCIOS*
• Ativos: *{estatisticas['anuncios_ativos']}*

*📈 STATUS ATUAIS*
"""

    for status_key, status_info in PizzaSabor.STATUS.items():
        count = estatisticas['por_status'].get(status_key, 0)
        if count > 0:
            resposta += f"{status_info['emoji']} {status_info['nome']}: *{count}*\n"

    resposta += f"""
*💾 SISTEMA*
• Banco: {estatisticas['modo_banco'].title()}
• Atualizado: {datetime.now().strftime('%H:%M:%S')}
"""

    bot.send_message(chat_id, resposta)

@bot.message_handler(commands=['backup'])
def comando_backup(mensagem):
    """Criar backup dos dados"""
    chat_id = mensagem.chat.id

    if not admin.is_admin(chat_id):
        bot.send_message(chat_id, "❌ *Acesso negado!*")
        return

    try:
        bot.send_message(chat_id, "💾 *Gerando backup...*")

        # Coletar dados
        pedidos = db.buscar_pedidos(limite=1000)
        anuncios = db.buscar_anuncios_ativos()

        # Criar estrutura de backup
        backup_data = {
            "metadata": {
                "data_backup": datetime.now(timezone.utc).isoformat(),
                "total_pedidos": len(pedidos),
                "total_anuncios": len(anuncios),
                "sistema": "Pizzaria Romeo Bot",
                "versao": "2.0"
            },
            "pedidos": pedidos,
            "anuncios": anuncios
        }

        # Salvar arquivo temporário
        filename = f"backup_pizzaria_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)

        # Enviar arquivo
        with open(filename, 'rb') as f:
            bot.send_document(
                chat_id,
                f,
                caption=f"📦 *BACKUP COMPLETO*\n\n"
                       f"📊 Pedidos: {len(pedidos)}\n"
                       f"📢 Anúncios: {len(anuncios)}\n"
                       f"📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
                       f"💾 Tamanho: {os.path.getsize(filename) / 1024:.1f} KB"
            )

        # Limpar arquivo
        os.remove(filename)

        logger.log("success", f"Backup criado por {chat_id}")

    except Exception as e:
        bot.send_message(chat_id, f"❌ Erro ao criar backup: {e}")
        logger.log("error", f"Erro no backup: {e}")

@bot.message_handler(commands=['config'])
def comando_config(mensagem):
    """Configurações do sistema"""
    chat_id = mensagem.chat.id

    if not admin.is_admin(chat_id):
        bot.send_message(chat_id, "❌ *Acesso negado!*")
        return

    estatisticas = db.get_estatisticas()

    config_text = f"""
*⚙️ CONFIGURAÇÕES DO SISTEMA*

*🔧 BANCO DE DADOS:*
• Modo atual: *{db.get_modo().upper()}*
• Supabase: {'✅ Conectado' if db.supabase else '❌ Offline'}
• SQLite: {'✅ Ativo' if db.sqlite_conn else '❌ Inativo'}

*📊 ESTATÍSTICAS:*
• Pedidos salvos: *{estatisticas['total_pedidos']}*
• Anúncios ativos: *{estatisticas['anuncios_ativos']}*
• Sessões ativas: *{len(user_sessions)}*

*🔑 CONFIGURAÇÕES:*
• Dono ID: `{DONO_ID}`
• Token Telegram: {'✅ Configurado' if CHAVE_API else '❌ Não configurado'}
• Supabase URL: {'✅ Configurada' if SUPABASE_URL else '❌ Não configurada'}

*📈 STATUS:*
• Bot: ✅ Online
• Web Server: ✅ Ativo
• Logs: ✅ Ativos ({len(json.load(open(logger.log_file, 'r')) if os.path.exists(logger.log_file) else 0)} registros)

*🔄 COMANDOS DISPONÍVEIS:*
/status_sistema - Status detalhado
/logs - Ver logs do sistema
/reiniciar - Reiniciar conexões
"""

    bot.send_message(chat_id, config_text)

@bot.message_handler(commands=['logs'])
def comando_logs(mensagem):
    """Ver logs do sistema"""
    chat_id = mensagem.chat.id

    if not admin.is_admin(chat_id):
        bot.send_message(chat_id, "❌ *Acesso negado!*")
        return

    try:
        if os.path.exists(logger.log_file):
            with open(logger.log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)

            # Últimos 15 logs
            ultimos_logs = logs[-15:]

            resposta = "📝 *ÚLTIMOS LOGS DO SISTEMA*\n\n"

            for log in ultimos_logs:
                nivel = log.get('nivel', 'info')
                emoji = {
                    'info': 'ℹ️',
                    'success': '✅',
                    'warning': '⚠️',
                    'error': '❌'
                }.get(nivel, '📝')

                hora = datetime.fromisoformat(log['timestamp']).strftime('%H:%M:%S')
                mensagem = log['mensagem'][:60] + '...' if len(log['mensagem']) > 60 else log['mensagem']
                resposta += f"{emoji} *[{hora}]* {mensagem}\n"

            resposta += f"\n*Total de logs:* {len(logs)}"

            bot.send_message(chat_id, resposta)
        else:
            bot.send_message(chat_id, "📭 Nenhum log encontrado.")

    except Exception as e:
        bot.send_message(chat_id, f"❌ Erro ao ler logs: {e}")

@bot.message_handler(commands=['status_sistema'])
def comando_status_sistema(mensagem):
    """Status detalhado do sistema"""
    chat_id = mensagem.chat.id

    if not admin.is_admin(chat_id):
        bot.send_message(chat_id, "❌ *Acesso negado!*")
        return

    estatisticas = db.get_estatisticas()

    status_text = f"""
*🔧 STATUS DETALHADO DO SISTEMA*

*🤖 BOT TELEGRAM:*
• Status: ✅ Online
• Modo: Infinity Polling
• Parse Mode: Markdown V2
• Usuários ativos: {len(user_sessions)}

*💾 BANCO DE DADOS:*
• Modo principal: *{db.get_modo().upper()}*
• Supabase: {'✅ Conectado' if db.supabase else '❌ Offline'}
• SQLite: {'✅ Pronto' if db.sqlite_conn else '❌ Erro'}
• Pedidos salvos: *{estatisticas['total_pedidos']}*
• Anúncios ativos: *{estatisticas['anuncios_ativos']}*

*🌐 SERVIDOR WEB:*
• Status: ✅ Ativo (Flask)
• Porta: 8080
• Keep Alive: ✅ Funcionando

*📊 ESTATÍSTICAS EM TEMPO REAL:*
• Sessões ativas: *{len(user_sessions)}*
• Pedidos hoje: *{estatisticas['pedidos_hoje']}*
• Valor total: R$ {estatisticas['valor_total']:.2f}
• Status pendentes: {estatisticas['por_status'].get('pendente', 0)}

*⚙️ CONFIGURAÇÕES:*
• Dono ID: `{DONO_ID}`
• Ambiente: {'Produção' if os.getenv('ENV') == 'production' else 'Desenvolvimento'}
• Versão: 2.0

*🔄 RECURSOS ATIVOS:*
• Sistema de pedidos: ✅ Completo
• Sistema de anúncios: ✅ Completo  
• Sistema de admin: ✅ Completo
• Backup automático: ✅ Disponível
• Logs detalhados: ✅ Ativos
• Banco híbrido: ✅ Funcional

*📈 PRÓXIMAS AÇÕES RECOMENDADAS:*
1. Monitorar pedidos pendentes: /pedidos_pendentes
2. Verificar logs do sistema: /logs
3. Criar backup regular: /backup
4. Verificar anúncios ativos: /anuncios
"""

    bot.send_message(chat_id, status_text)

@bot.message_handler(commands=['reiniciar'])
def comando_reiniciar(mensagem):
    """Reiniciar conexões do sistema"""
    chat_id = mensagem.chat.id

    if not admin.is_admin(chat_id):
        bot.send_message(chat_id, "❌ *Acesso negado!*")
        return

    bot.send_message(chat_id, "🔄 *Reiniciando conexões do sistema...*")

    # Reinicializar banco de dados
    global db
    db = DatabaseManager()

    bot.send_message(
        chat_id,
        f"✅ *Conexões reiniciadas com sucesso!*\n\n"
        f"📊 Novo status:\n"
        f"• Banco: {db.get_modo().upper()}\n"
        f"• Supabase: {'✅ Conectado' if db.supabase else '❌ Offline'}\n"
        f"• SQLite: {'✅ Ativo' if db.sqlite_conn else '❌ Inativo'}"
    )

    logger.log("success", f"Sistema reiniciado por {chat_id}")

# ==================== COMANDOS PÚBLICOS ADICIONAIS ====================

@bot.message_handler(commands=['ajuda', 'help'])
def comando_ajuda(mensagem):
    """Ajuda e contato"""
    chat_id = mensagem.chat.id

    ajuda_text = """
*📞 AJUDA E CONTATO*

*🤔 COMO FAÇO UM PEDIDO?*
1. Use /menu para ver o cardápio
2. Escolha uma pizza (ex: /calabresa)
3. Siga as instruções passo a passo
4. Confirme seus dados
5. Aguarde a confirmação!

*⏰ HORÁRIO DE FUNCIONAMENTO:*
• Segunda a Domingo: 18:00 - 23:00
• Feriados: Consulte disponibilidade

*📍 ÁREA DE ENTREGA:*
• Centro
• Jardins  
• Vila Nova
• Zona Sul (consulte disponibilidade)

*💰 FORMAS DE PAGAMENTO:*
• 💵 Dinheiro (troco para até R$ 50,00)
• 💳 Cartão (débito/crédito) - máquina na entrega
• 📱 PIX - Chave: pizzaria.romeo@email.com

*📱 CONTATO:*
• Telefone/WhatsApp: (11) 99999-9999
• Instagram: @pizzariaromeo
• Facebook: /PizzariaRomeoOficial

*🚚 INFORMAÇÕES DE ENTREGA:*
• Taxa fixa: R$ 5,00
• Grátis para pedidos acima de R$ 60,00
• Tempo médio: 30-45 minutos
• Entregador identificado

*❓ PROBLEMAS COM PEDIDO?*
• Use /status para verificar status
• Entre em contato pelo telefone
• Responda à mensagem de confirmação

*🎉 PROMOÇÕES ESPECIAIS:*
• Segunda: 20% de desconto em DOCES
• Quarta: 2ª pizza 50% off (mesmo sabor)
• Sexta: Brinde refrigerante 1L

*⚙️ COMANDOS DISPONÍVEIS:*
/menu - Ver cardápio completo
/status - Verificar status do pedido
/ajuda - Esta mensagem de ajuda
/promocoes - Ver promoções ativas
"""

    bot.send_message(chat_id, ajuda_text)

@bot.message_handler(commands=['status'])
def comando_status_pedido_usuario(mensagem):
    """Verificar status do pedido do usuário"""
    chat_id = mensagem.chat.id

    # Buscar últimos pedidos do usuário
    pedidos = db.buscar_pedidos(filtros={"user_id": str(chat_id)})

    if not pedidos:
        bot.send_message(
            chat_id,
            "📭 *Você ainda não fez nenhum pedido.*\n\n"
            "Use /menu para ver o cardápio e fazer seu primeiro pedido! 🍕\n\n"
            "🎉 *Dica:* Na sua primeira compra, ganhe 10% de desconto!"
        )
        return

    # Mostrar últimos 3 pedidos
    resposta = "📋 *SEUS ÚLTIMOS PEDIDOS*\n\n"

    for i, pedido in enumerate(pedidos[:3], 1):
        status_info = PizzaSabor.STATUS.get(pedido.get('status', 'pendente'), {"nome": "Pendente", "emoji": "🟡"})

        resposta += f"{status_info['emoji']} *Pedido #{i}*\n"
        resposta += f"📋 `{pedido.get('codigo_pedido', 'N/A')}`\n"
        resposta += f"🍕 {pedido.get('pizza', 'N/A')}\n"
        resposta += f"📊 Status: *{pedido.get('status', 'pendente').title()}*\n"
        resposta += f"📅 {pedido.get('created_at', '')[:16]}\n"

        if pedido.get('status') == 'entregue':
            resposta += "✅ *Pedido entregue! Obrigado pela preferência!*\n"
        elif pedido.get('status') == 'cancelado':
            resposta += "❌ *Pedido cancelado*\n"
        elif pedido.get('status') == 'saiu_entrega':
            resposta += "🚚 *Pizza a caminho! Fique atento ao telefone.*\n"

        resposta += "━━━━━━━━━━━━━━\n"

    if len(pedidos) > 3:
        resposta += f"\n*... e mais {len(pedidos) - 3} pedidos anteriores*"

    valor_total = sum(p.get('valor', 0) for p in pedidos)
    resposta += f"\n💰 *Total gasto conosco:* R$ {valor_total:.2f}"
    resposta += f"\n📞 *Dúvidas?* (11) 99999-9999"

    bot.send_message(chat_id, resposta)

@bot.message_handler(commands=['promocoes'])
def comando_promocoes(mensagem):
    """Mostra promoções ativas"""
    chat_id = mensagem.chat.id

    # Buscar anúncios do tipo promoção
    anuncios = db.buscar_anuncios_ativos(tipo="promocao")

    if not anuncios:
        promocoes_text = """
🎉 *PROMOÇÕES DA SEMANA*

*SEGUNDA DULÇURA* 🍬
• 20% de desconto em TODAS as pizzas doces
• Válido toda segunda-feira

*QUARTA DA DUPLA* 🍕🍕  
• 2ª pizza 50% off (mesmo sabor)
• Aproveite para compartilhar!

*SEXTA REFRI* 🥤
• Ganhe 1L de refrigerante grátis
• Em pedidos acima de R$ 50,00

*FIM DE SEMANA FAMÍLIA* 👨‍👩‍👧‍👦
• Pizza Família + 2 refrigerantes 2L
• Apenas R$ 79,90 (economize R$ 20,00)

🎁 *CLIENTE FREQUENTE:*
• A cada 5 pedidos, ganhe 1 pizza média grátis!
• Use /status para acompanhar seus pedidos.

📱 *PAGUE COM PIX E GANHE:*
• 5% de desconto adicional
• Processamento instantâneo
"""
    else:
        promocoes_text = "🎉 *PROMOÇÕES ATIVAS*\n\n"
        for anuncio in anuncios:
            promocoes_text += f"📢 *{anuncio['titulo']}*\n{anuncio['mensagem']}\n\n"

        promocoes_text += "━━━━━━━━━━━━━━\n"
        promocoes_text += "*PROMOÇÕES PERMANENTES:*\n"
        promocoes_text += "• Entrega grátis acima de R$ 60,00\n"
        promocoes_text += "• Programa cliente frequente\n"
        promocoes_text += "• Desconto no PIX: 5%\n"

    promocoes_text += "\n📞 *Mais informações:* (11) 99999-9999"

    bot.send_message(chat_id, promocoes_text)

# ==================== HANDLER PARA MENSAGENS NÃO RECONHECIDAS ====================

@bot.message_handler(func=lambda mensagem: True)
def mensagem_nao_reconhecida(mensagem):
    """Responde a mensagens não reconhecidas"""
    chat_id = mensagem.chat.id

    if mensagem.text:
        resposta = f"""
Olá! Sou o *assistente virtual da Pizzaria Romeo*! 🤖🍕

Não entendi sua mensagem. Aqui estão os comandos disponíveis:

*🍕 FAZER PEDIDO:*
/menu - Ver cardápio completo

*📋 MEUS PEDIDOS:*
/status - Ver status dos pedidos

*📞 AJUDA:*
/ajuda - Ajuda e contato
/promocoes - Ver promoções

*🎯 ESCOLHA UMA PIZZA:*
/calabresa - Calabresa tradicional
/portuguesa - Portuguesa completa  
/marguerita - Marguerita clássica
/frango - Frango c/ Catupiry
/quatroqueijos - 4 Queijos especiais
/chocolate - Chocolate ao leite
/romeuejulieta - Goiabada c/ Queijo

*Ou responda diretamente ao que precisa!* 😊
"""

        bot.send_message(chat_id, resposta)
        logger.log("info", f"Mensagem não reconhecida de {chat_id}: {mensagem.text[:50]}")

# ==================== INICIALIZAÇÃO DO SISTEMA ====================

def banner():
    """Exibe banner de inicialização"""
    banner_text = """
╔══════════════════════════════════════════════════╗
║           🍕 PIZZARIA ROMEO BOT v2.0            ║
║           Sistema Completo de Delivery           ║
╚══════════════════════════════════════════════════╝
"""
    print(banner_text)

def mostrar_status_inicial():
    """Mostra status inicial do sistema"""
    print("\n" + "="*60)
    print("🔍 STATUS INICIAL DO SISTEMA")
    print("="*60)

    print(f"\n✅ CONFIGURAÇÕES:")
    print(f"   • Telegram Token: {'✅ OK' if CHAVE_API else '❌ FALTA'}")
    print(f"   • Supabase URL: {'✅ OK' if SUPABASE_URL else '⚠️  FALTA (usando SQLite)'}")
    print(f"   • Supabase Key: {'✅ OK' if SUPABASE_KEY else '⚠️  FALTA (usando SQLite)'}")
    print(f"   • Dono ID: {DONO_ID if DONO_ID else '❌ NÃO CONFIGURADO'}")

    print(f"\n🔗 CONEXÕES:")
    print(f"   • Modo banco: {db.get_modo().upper()}")
    print(f"   • Supabase: {'✅ CONECTADO' if db.supabase else '❌ OFFLINE'}")
    print(f"   • SQLite: {'✅ PRONTO' if db.sqlite_conn else '❌ ERRO'}")

    print(f"\n📊 DADOS INICIAIS:")
    pedidos = db.buscar_pedidos(limite=5)
    anuncios = db.buscar_anuncios_ativos()
    print(f"   • Pedidos existentes: {len(pedidos)}")
    print(f"   • Anúncios ativos: {len(anuncios)}")

    print(f"\n🌐 SERVIDOR WEB:")
    print(f"   • Status: ✅ INICIANDO")
    print(f"   • Porta: 8080")

    print("\n" + "="*60)
    print("🤖 INICIANDO BOT TELEGRAM...")
    print("="*60 + "\n")

if __name__ == "__main__":
    try:
        # Mostrar banner
        banner()

        # Mostrar status inicial
        mostrar_status_inicial()

        # Iniciar servidor web
        keep_alive()
        logger.log("success", "Servidor web iniciado na porta 8080")

        # Iniciar bot
        logger.log("info", "Iniciando bot Telegram...")
        bot.infinity_polling(timeout=30, long_polling_timeout=10)

    except Exception as e:
        logger.log("error", f"Erro fatal: {e}")
        print(f"\n❌ ERRO FATAL: {e}")
        print("🔄 Reiniciando em 10 segundos...")
        time.sleep(10)
        os.execv(sys.executable, ['python'] + sys.argv)
