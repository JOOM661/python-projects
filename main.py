import telebot
import os
from supabase import create_client
from datetime import datetime, timezone
from dotenv import load_dotenv
from flask import Flask        # <-- NOVO
from threading import Thread   # <-- NOVO

load_dotenv()

# --- CONFIGURAÇÃO WEB (KEEP ALIVE) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot da Pizzaria Romeo está ONLINE! 🍕"

def run():
    # Ele tenta pegar a porta do Railway, se não achar, usa 8080
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- CONFIGURAÇÕES DO BOT ---
CHAVE_API = os.getenv("TELEGRAM_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

bot = telebot.TeleBot(CHAVE_API)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

user_data = {}

# --- FUNÇÕES DE APOIO ---
def salvar_no_banco(chat_id):
    dados = user_data[chat_id]
    try:
        supabase.table("pedidos").insert({
            "user_id": str(chat_id),
            "nome": dados['nome'],
            "pizza": dados['pizza'],
            "endereco": dados['endereco'],
            "idade": dados['idade'],
            "pagamento": dados['pagamento'],
            "created_at": datetime.now(timezone.utc).isoformat()
        }).execute()
        return True
    except Exception as e:
        print(f"Erro Supabase: {e}")
        return False

# --- COMANDOS DO CARDÁPIO ---
@bot.message_handler(commands=['start', 'menu'])
def cardapio(mensagem):
    texto_menu = """
🍕 *CARDÁPIO PIZZARIA ROMEO* 🍕
Escolha seu sabor favorito:

*Salgadas:*
/calabresa - R$ 40,00
/portuguesa - R$ 45,00
/marguerita - R$ 38,00
/frango - R$ 42,00
/quatroqueijos - R$ 48,00

*Doces:*
/chocolate - R$ 35,00
/romeuejulieta - R$ 35,00
"""
    bot.send_message(mensagem.chat.id, texto_menu, parse_mode="Markdown")

@bot.message_handler(commands=['calabresa', 'portuguesa', 'marguerita', 'frango', 'quatroqueijos', 'chocolate', 'romeuejulieta'])
def iniciar_pedido(mensagem):
    sabor = mensagem.text.replace("/", "").capitalize()
    chat_id = mensagem.chat.id
    user_data[chat_id] = {'pizza': sabor}
    msg = bot.reply_to(mensagem, f"Ótima escolha! 🍕\nPara começar, qual o seu **Nome Completo**?")
    bot.register_next_step_handler(msg, proximo_passo_endereco)

def proximo_passo_endereco(mensagem):
    chat_id = mensagem.chat.id
    user_data[chat_id]['nome'] = mensagem.text
    msg = bot.send_message(chat_id, "Qual o **Endereço de Entrega**? (Rua, número, bairro)")
    bot.register_next_step_handler(msg, proximo_passo_idade)

def proximo_passo_idade(mensagem):
    chat_id = mensagem.chat.id
    user_data[chat_id]['endereco'] = mensagem.text
    msg = bot.send_message(chat_id, "Qual a sua **idade**?")
    bot.register_next_step_handler(msg, proximo_passo_pagamento)

def proximo_passo_pagamento(mensagem):
    chat_id = mensagem.chat.id
    user_data[chat_id]['idade'] = mensagem.text
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add('Dinheiro', 'Cartão', 'Pix')
    msg = bot.send_message(chat_id, "Qual a **forma de pagamento**?", reply_markup=markup)
    bot.register_next_step_handler(msg, finalizar_pedido)

def finalizar_pedido(mensagem):
    chat_id = mensagem.chat.id
    user_data[chat_id]['pagamento'] = mensagem.text
    markup = telebot.types.ReplyKeyboardRemove()
    bot.send_message(chat_id, "⏳ Processando seu pedido no sistema...", reply_markup=markup)

    if salvar_no_banco(chat_id):
        resumo = f"✅ *PEDIDO CONFIRMADO!*\n━━━━━━━━━━━━━━━━━━\n🍕 *Pizza:* {user_data[chat_id]['pizza']}\n👤 *Cliente:* {user_data[chat_id]['nome']}\n🏠 *Endereço:* {user_data[chat_id]['endereco']}\n💳 *Pagamento:* {user_data[chat_id]['pagamento']}\n━━━━━━━━━━━━━━━━━━"
        bot.send_message(chat_id, resumo, parse_mode="Markdown")
    else:
        bot.send_message(chat_id, "❌ Erro ao salvar pedido.")

    if chat_id in user_data: del user_data[chat_id]

# --- INICIALIZAÇÃO ---
if __name__ == "__main__":
    print("🌐 Iniciando Servidor Web...")
    keep_alive()  # <--- Faz o Replit gerar a URL
    print("🤖 Bot de Delivery Online!")
    bot.polling(none_stop=True)
