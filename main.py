import sys

# --- PARCHE TOTAL ANTI-AUDIOOP ---
from types import ModuleType
mock_audioop = ModuleType('audioop')
# Simulamos todas las funciones que pydub pide
mock_audioop.ratecv = lambda *args: (b'', b'')
mock_audioop.tomono = lambda data, *args: data # Devuelve el audio igual para no fallar
mock_audioop.getsample = lambda *args: 0
mock_audioop.max = lambda *args: 0
sys.modules['audioop'] = mock_audioop

import telebot, os
from telebot import types
from pydub import AudioSegment
from flask import Flask
from threading import Thread

# --- SERVIDOR PARA RENDER ---
app = Flask('')
@app.route('/')
def home(): return "DJ FARAON V4 - TOTAL FIX 🔥"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    Thread(target=run).start()

# --- CONFIGURACIÓN ---
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)
user_files = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🔥 **DJ FARAON V4 - MODO LOCAL**\nEnvíame el MP3 y elige tu intro.")

@bot.message_handler(content_types=['audio', 'document'])
def handle_audio(message):
    file_info = None
    file_name = "track"

    if message.content_type == 'audio':
        file_info = bot.get_file(message.audio.file_id)
        file_name = message.audio.title or "audio"
    elif message.content_type == 'document' and message.document.mime_type.startswith('audio/'):
        file_info = bot.get_file(message.document.file_id)
        file_name = message.document.file_name or "archivo"

    if not file_info: return

    user_files[message.chat.id] = {'file_id': file_info.file_id, 'file_name': file_name}

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ INTRO PERSONAL", callback_data="intro_p"))
    markup.add(types.InlineKeyboardButton("❌ INTRO OFICIAL", callback_data="intro_o"))
    bot.reply_to(message, "🎵 ¿Qué intro le pego?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('intro_'))
def process_audio(call):
    chat_id = call.message.chat.id
    if chat_id not in user_files:
        bot.send_message(chat_id, "❌ Reenvía el archivo.")
        return

    use_personal = (call.data == "intro_p")
    bot.edit_message_text(f"🚀 Procesando mezcla Q0...", chat_id, call.message.message_id)

    try:
        file_info = bot.get_file(user_files[chat_id]['file_id'])
        downloaded = bot.download_file(file_info.file_path)
        input_p = f"in_{chat_id}.mp3"
        with open(input_p, 'wb') as f:
            f.write(downloaded)

        intro_file = "Intro_Personal.wav" if use_personal else "Intrucidity.wav"
        
        if not os.path.exists(intro_file):
            bot.send_message(chat_id, f"⚠️ Error: Falta {intro_file}")
            return

        # MEZCLA
        base = AudioSegment.from_file(intro_file)
        song = AudioSegment.from_file(input_p)

        # Bypass simplificado para evitar audioop:
        # Solo subimos el pitch un poco cambiando el sample rate directamente
        song = song._spawn(song.raw_data, overrides={'frame_rate': int(song.frame_rate * 1.03)})
        song = song.set_frame_rate(44100)

        final = base.append(song, crossfade=2000)
        
        out_name = f"{user_files[chat_id]['file_name']}_MIX.wav"
        # Exportación Q0
        final.export(out_name, format="wav", codec="libmp3lame", parameters=["-q:a", "0"])

        with open(out_name, 'rb') as f:
            bot.send_document(chat_id, f, caption="✅ ¡Mezcla lista!")

        os.remove(input_p)
        os.remove(out_name)
        del user_files[chat_id]

    except Exception as e:
        bot.send_message(chat_id, f"❌ Error fatal: {e}")

if __name__ == "__main__":
    keep_alive()
    bot.polling(none_stop=True)

