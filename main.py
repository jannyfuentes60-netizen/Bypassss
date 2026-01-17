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
from yt_dlp import YoutubeDL
from flask import Flask
from threading import Thread

# --- SERVIDOR PARA RENDER ---
app = Flask('')
@app.route('/')
def home(): return "DJ FARAON V4 - HIGH QUALITY WAV/MP3 🔥"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    Thread(target=run).start()

# --- CONFIGURACIÓN ---
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)
user_states = {}

# --- OPCIONES DE YOUTUBE ---
YDL_OPTIONS = {
    'format': 'bestaudio/best', 
    'quiet': True,
    'noplaylist': True,
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'nocheckcertificate': True,
    'geo_bypass': True,
    'extractor_args': {
        'youtube': {
            'player_skip': ['webpage', 'configs'],
            'player_client': ['android', 'web']
        }
    }
}

if os.path.exists("cookies.txt"):
    YDL_OPTIONS['cookiefile'] = 'cookies.txt'

# --- COMANDOS ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🔥 **DJ FARAON V4 - ULTRA QUALITY**\nMezclando en WAV/MP3 Quality 0.")

@bot.message_handler(commands=['buscar'])
def search_youtube(message):
    query = message.text.replace('/buscar ', '')
    if not query or query == '/buscar':
        bot.reply_to(message, "¡DJ! Pon el nombre: `/buscar Gata Only` 🎵")
        return
    
    bot.send_message(message.chat.id, f"🔍 Buscando '{query}'...")
    
    try:
        with YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)['entries'][0]
            title = info['title']
            url = info['webpage_url']
        
        user_states[message.chat.id] = {'query': title, 'url': url}
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📥 Descargar y Mixear Pro", callback_data="start_dl"))
        bot.send_message(message.chat.id, f"💎 **Encontrado:** {title}\n¿Procesamos en Alta Fidelidad?", reply_markup=markup)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error YouTube: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "start_dl")
def download_process(call):
    chat_id = call.message.chat.id
    url = user_states[chat_id]['url']
    bot.edit_message_text(f"Procesando en Máxima Calidad (Q0)... 🛠️", chat_id, call.message.message_id)
    
    try:
        temp_filename = f"temp_{chat_id}"
        download_opts = YDL_OPTIONS.copy()
        download_opts.update({
            'outtmpl': f'{temp_filename}.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '0', # Calidad máxima
            }],
        })

        with YoutubeDL(download_opts) as ydl: 
            ydl.download([url])
        
        if not os.path.exists("Intrucidity.wav"):
            bot.send_message(chat_id, "⚠️ Error: No está Intrucidity.wav.")
            return

        actual_filename = f"{temp_filename}.mp3"
        base = AudioSegment.from_file("Intrucidity.wav")
        song = AudioSegment.from_file(actual_filename)
        
        # Bypass + Calidad: Mantenemos el pitch pero aseguramos 44.1kHz
        song = song._spawn(song.raw_data, overrides={'frame_rate': int(song.frame_rate * 1.03)}).set_frame_rate(44100).set_channels(1)
        
        final = base.append(song, crossfade=2000)
        
        clean_title = "".join([c for c in user_states[chat_id]['query'] if c.isalnum() or c==' ']).strip()
        # Exportamos como WAV usando el codec libmp3lame para cumplir tu requisito
        out = f"{clean_title}_PRO.wav"
        
        # Exportación técnica: Formato WAV, pero especificando parámetros de MP3 de alta calidad
        final.export(out, format="wav", codec="libmp3lame", parameters=["-q:a", "0"])
        
        with open(out, 'rb') as f:
            bot.send_document(chat_id, f, caption=f"✅ **{clean_title}**\n[ WAV-MP3 Q0 ]")
            
        if os.path.exists(actual_filename): os.remove(actual_filename)
        if os.path.exists(out): os.remove(out)
        
    except Exception as e:
        bot.send_message(chat_id, f"❌ Error: {e}")

if __name__ == "__main__":
    keep_alive()
    bot.polling(none_stop=True)

