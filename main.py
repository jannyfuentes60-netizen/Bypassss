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
def home(): return "DJ FARAON V4 - YT + OPTIONAL INTRO 🔥"

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
    'extractor_args': {'youtube': {'player_skip': ['webpage', 'configs'], 'player_client': ['android', 'web']}}
}

if os.path.exists("cookies.txt"):
    YDL_OPTIONS['cookiefile'] = 'cookies.txt'

# --- COMANDOS ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🔥 **DJ FARAON V4**\nEscribe `/buscar nombre_de_la_rola` para empezar.")

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
        
        # PREGUNTA POR LA INTRO
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ SÍ (Intro Personal)", callback_data="use_personal"))
        markup.add(types.InlineKeyboardButton("❌ NO (Intro Oficial)", callback_data="use_official"))
        
        bot.send_message(message.chat.id, f"💎 **Encontrado:** {title}\n\n**¿Quieres usar tu Intro Personal?**", reply_markup=markup)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error YouTube: {e}")

@bot.callback_query_handler(func=lambda call: call.data in ["use_personal", "use_official"])
def download_process(call):
    chat_id = call.message.chat.id
    if chat_id not in user_states:
        bot.send_message(chat_id, "❌ Error de sesión, busca de nuevo.")
        return

    use_personal = (call.data == "use_personal")
    url = user_states[chat_id]['url']
    bot.edit_message_text(f"🚀 Procesando con {'Intro Personal' if use_personal else 'Intro Oficial'}...", chat_id, call.message.message_id)
    
    try:
        temp_filename = f"temp_{chat_id}"
        download_opts = YDL_OPTIONS.copy()
        download_opts.update({
            'outtmpl': f'{temp_filename}.%(ext)s',
            'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '0'}],
        })

        with YoutubeDL(download_opts) as ydl: ydl.download([url])
        
        # Definir intro
        intro_file = "Intro_Personal.wav" if use_personal else "Intrucidity.wav"
        
        if not os.path.exists(intro_file):
            bot.send_message(chat_id, f"⚠️ Error: No encontré el archivo `{intro_file}` en GitHub.")
            return

        actual_filename = f"{temp_filename}.mp3"
        base = AudioSegment.from_file(intro_file)
        song = AudioSegment.from_file(actual_filename)
        
        # Bypass: Pitch +3% y Mono
        song = song._spawn(song.raw_data, overrides={'frame_rate': int(song.frame_rate * 1.03)}).set_frame_rate(44100).set_channels(1)
        
        final = base.append(song, crossfade=2000)
        
        clean_title = "".join([c for c in user_states[chat_id]['query'] if c.isalnum() or c==' ']).strip()
        out = f"{clean_title}_MIX.wav"
        
        # Exportación Q0 WAV/MP3
        final.export(out, format="wav", codec="libmp3lame", parameters=["-q:a", "0"])
        
        with open(out, 'rb') as f:
            bot.send_document(chat_id, f, caption=f"✅ **{clean_title}**\n[ {'PERSONAL' if use_personal else 'OFICIAL'} ]")
            
        os.remove(actual_filename)
        os.remove(out)
        del user_states[chat_id]
        
    except Exception as e:
        bot.send_message(chat_id, f"❌ Error: {e}")

if __name__ == "__main__":
    keep_alive()
    bot.polling(none_stop=True)

