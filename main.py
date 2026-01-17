import sys
# --- PARCHE PARA EL ERROR PYAUDIOOP ---
try:
    import audioop
except ImportError:
    from types import ModuleType
    mock_audioop = ModuleType('audioop')
    sys.modules['audioop'] = mock_audioop

import telebot, os, random
from telebot import types
from pydub import AudioSegment
from flask import Flask
from threading import Thread

# --- SERVIDOR PARA RENDER ---
app = Flask('')
@app.route('/')
def home(): return "DJ FARAON V4 - SOLO ARCHIVOS 🔥"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    Thread(target=run).start()

# --- CONFIGURACIÓN ---
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)
user_files = {} # Para guardar los archivos temporalmente

# --- COMANDOS ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🔥 **DJ FARAON V4 - MODO MANUAL**\n\n1. Envíame el archivo MP3.\n2. Elige la intro (Oficial o Personal).\n3. Recibe tu WAV/MP3 Q0.")

# --- MANEJADOR DE ARCHIVOS ---
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

    if not file_info:
        bot.reply_to(message, "❌ ¡Eso no es música, carnal!")
        return

    # Guardamos datos para la siguiente fase
    user_files[message.chat.id] = {
        'file_id': file_info.file_id,
        'file_name': file_name
    }

    # Preguntar por la Intro
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ USAR INTRO PERSONAL", callback_data="intro_p"))
    markup.add(types.InlineKeyboardButton("❌ USAR INTRO OFICIAL", callback_data="intro_o"))
    
    bot.reply_to(message, "🎵 Archivo listo. **¿Qué intro le pego?**", reply_markup=markup)

# --- PROCESAMIENTO ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('intro_'))
def process_audio(call):
    chat_id = call.message.chat.id
    if chat_id not in user_files:
        bot.send_message(chat_id, "❌ Error, manda el archivo de nuevo.")
        return

    use_personal = (call.data == "intro_p")
    bot.edit_message_text(f"🚀 Procesando con {'Intro Personal' if use_personal else 'Intro Oficial'} (Q0)...", chat_id, call.message.message_id)

    try:
        # Descargar el MP3 que mandaste
        file_info = bot.get_file(user_files[chat_id]['file_id'])
        downloaded = bot.download_file(file_info.file_path)
        input_p = f"in_{chat_id}.mp3"
        with open(input_p, 'wb') as f:
            f.write(downloaded)

        # Seleccionar Intro
        intro_file = "Intro_Personal.wav" if use_personal else "Intrucidity.wav"
        
        if not os.path.exists(intro_file):
            bot.send_message(chat_id, f"⚠️ Error: No encontré `{intro_file}` en GitHub.")
            return

        # Mezclar
        base = AudioSegment.from_file(intro_file)
        song = AudioSegment.from_file(input_p)

        # Bypass (+3% pitch, Mono, 44.1kHz)
        song = song._spawn(song.raw_data, overrides={'frame_rate': int(song.frame_rate * 1.03)}).set_frame_rate(44100).set_channels(1)

        final = base.append(song, crossfade=2000)
        
        # Nombre de salida
        clean_name = "".join([c for c in user_files[chat_id]['file_name'] if c.isalnum() or c==' ']).strip()
        out_name = f"{clean_name}_MIX.wav"

        # Exportación Calidad 0 WAV/MP3
        final.export(out_name, format="wav", codec="libmp3lame", parameters=["-q:a", "0"])

        # Enviar
        with open(out_name, 'rb') as f:
            bot.send_document(chat_id, f, caption=f"✅ **{clean_name}** procesado.")

        # Limpiar
        os.remove(input_p)
        os.remove(out_name)
        del user_files[chat_id]

    except Exception as e:
        bot.send_message(chat_id, f"❌ Falló el proceso: {e}")

if __name__ == "__main__":
    keep_alive()
    bot.polling(none_stop=True)

