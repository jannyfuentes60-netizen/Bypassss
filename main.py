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
from pydub import AudioSegment, effects
from yt_dlp import YoutubeDL
from flask import Flask
from threading import Thread

# --- SERVIDOR PARA RENDER ---
app = Flask('')
@app.route('/')
def home(): return "DJ FARAON V4 STATUS: ONLINE 🔥"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    Thread(target=run).start()

# --- CONFIGURACIÓN ---
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)
user_states = {}

# --- FUNCIÓN DE EFECTOS ---
def apply_pro_fx(audio):
    fx_list = ['highpass', 'lowpass', 'normal']
    choice = random.choice(fx_list)
    if choice == 'highpass': return audio.high_pass_filter(1200)
    if choice == 'lowpass': return audio.low_pass_filter(1500)
    return audio

# --- COMANDOS ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🔥 **DJ FARAON V4** en la casa.\nUsa `/buscar nombre_de_la_rola` para mezclar.")

@bot.message_handler(commands=['buscar'])
def search_youtube(message):
    query = message.text.replace('/buscar ', '')
    if not query or query == '/buscar':
        bot.reply_to(message, "¡DJ! Pon el nombre: `/buscar Gata Only` 🎵")
        return
    
    bot.send_message(message.chat.id, f"🔍 Buscando '{query}'...")
    
    try:
        # Configuración agresiva para evitar bloqueos
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'noplaylist': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'nocheckcertificate': True,
            'geo_bypass': True,
            'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
        }
        
        # Carga cookies si existen en el repositorio
        if os.path.exists("cookies.txt"):
            ydl_opts['cookiefile'] = 'cookies.txt'

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)['entries'][0]
            title = info['title']
            url = info['webpage_url']
        
        user_states[message.chat.id] = {'query': title, 'url': url}
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📥 Descargar y Mixear", callback_data="start_dl"))
        bot.send_message(message.chat.id, f"💎 **Encontrado:** {title}\n¿Lo procesamos?", reply_markup=markup)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error de YouTube: {e}\n(Revisa que tu cookies.txt sea formato Netscape)")

@bot.callback_query_handler(func=lambda call: call.data == "start_dl")
def download_process(call):
    chat_id = call.message.chat.id
    url = user_states[chat_id]['url']
    bot.edit_message_text(f"Bajando y aplicando Bypass... 🛠️", chat_id, call.message.message_id)
    
    try:
        path = f"song_{chat_id}.mp3"
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'song_{chat_id}.%(ext)s',
            'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '128'}],
            'quiet': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
        }
        
        if os.path.exists("cookies.txt"):
            ydl_opts['cookiefile'] = 'cookies.txt'

        with YoutubeDL(ydl_opts) as ydl: ydl.download([url])
        
        if not os.path.exists("Intrucidity.wav"):
            bot.send_message(chat_id, "⚠️ Error: Falta 'Intrucidity.wav' en GitHub.")
            return

        base = AudioSegment.from_file("Intrucidity.wav")
        song = AudioSegment.from_file(path)
        
        # Bypass: Pitch +3% y Mono
        song = song._spawn(song.raw_data, overrides={'frame_rate': int(song.frame_rate * 1.03)}).set_frame_rate(44100).set_channels(1)
        
        final = base.append(song, crossfade=2000)
        out = f"RESULT_{chat_id}.mp3"
        final.export(out, format="mp3", bitrate="128k")
        
        with open(out, 'rb') as f:
            bot.send_audio(chat_id, f, caption="✅ **MIX LISTO**\n[ CORRUPTED ]")
            
        os.remove(path)
        os.remove(out)
        
    except Exception as e:
        bot.send_message(chat_id, f"❌ Error: {e}")

if __name__ == "__main__":
    keep_alive()
    bot.polling(none_stop=True)

