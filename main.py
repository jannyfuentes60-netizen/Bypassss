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
def home(): return "DJ FARAON V4 - STATUS: ONLINE 🔥"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    Thread(target=run).start()

# --- CONFIGURACIÓN ---
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)
user_states = {}

# --- OPCIONES DE YOUTUBE (NUEVA ESTRATEGIA DE FORMATOS) ---
YDL_OPTIONS = {
    # Cambiamos a 'best' para que si no hay audio solo, baje el video y extraiga
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
    bot.reply_to(message, "🔥 **DJ FARAON V4** listo.\nEscribe `/buscar nombre_de_la_rola`.")

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
        markup.add(types.InlineKeyboardButton("📥 Descargar y Mixear", callback_data="start_dl"))
        bot.send_message(message.chat.id, f"💎 **Encontrado:** {title}\n¿Lo procesamos?", reply_markup=markup)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error YouTube: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "start_dl")
def download_process(call):
    chat_id = call.message.chat.id
    url = user_states[chat_id]['url']
    bot.edit_message_text(f"Bajando y convirtiendo... 🛠️", chat_id, call.message.message_id)
    
    try:
        # Usamos un nombre de archivo temporal
        temp_filename = f"temp_song_{chat_id}"
        
        download_opts = YDL_OPTIONS.copy()
        download_opts.update({
            'format': 'bestaudio/best', # Intentar el mejor audio, si no lo que sea
            'outtmpl': f'{temp_filename}.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '128',
            }],
        })

        with YoutubeDL(download_opts) as ydl: 
            ydl.download([url])
        
        if not os.path.exists("Intrucidity.wav"):
            bot.send_message(chat_id, "⚠️ Error: Falta 'Intrucidity.wav' en tu GitHub.")
            return

        # Buscamos el archivo que se descargó (la extensión puede variar antes de ser mp3)
        actual_filename = f"{temp_filename}.mp3"
        
        base = AudioSegment.from_file("Intrucidity.wav")
        song = AudioSegment.from_file(actual_filename)
        
        # Bypass: Pitch +3% y Mono
        song = song._spawn(song.raw_data, overrides={'frame_rate': int(song.frame_rate * 1.03)}).set_frame_rate(44100).set_channels(1)
        
        final = base.append(song, crossfade=2000)
        out = f"RESULT_{chat_id}.mp3"
        final.export(out, format="mp3", bitrate="128k")
        
        with open(out, 'rb') as f:
            bot.send_audio(chat_id, f, caption="✅ **MIX LISTO**\n[ BYPASS OK ]")
            
        # Limpieza de archivos temporales
        os.remove(actual_filename)
        os.remove(out)
        
    except Exception as e:
        bot.send_message(chat_id, f"❌ Error en proceso: {e}")

if __name__ == "__main__":
    keep_alive()
    bot.polling(none_stop=True)

