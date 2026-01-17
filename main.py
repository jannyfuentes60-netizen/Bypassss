import telebot, os, random
from telebot import types
from pydub import AudioSegment, effects
from yt_dlp import YoutubeDL
from flask import Flask
from threading import Thread

# --- SERVIDOR PARA KOYEB ---
app = Flask('')
@app.route('/')
def home(): return "YouTube DJ Faraon V4 Online 🔥"
def run(): app.run(host='0.0.0.0', port=8000) # Koyeb usa el 8000 o 8080
def keep_alive(): Thread(target=run).start()

# --- CONFIGURACIÓN ---
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)
user_states = {}

# --- EFECTOS DE MEZCLA ---
def apply_pro_fx(audio):
    fx_list = ['highpass', 'lowpass', 'normal']
    choice = random.choice(fx_list)
    if choice == 'highpass': return audio.high_pass_filter(1200)
    if choice == 'lowpass': return audio.low_pass_filter(1500)
    return audio

# --- BUSCADOR ---
@bot.message_handler(commands=['buscar'])
def search_youtube(message):
    query = message.text.replace('/buscar ', '')
    if not query or query == '/buscar':
        bot.reply_to(message, "¡DJ! Pon el nombre: `/buscar Gata Only` 🎵")
        return
    
    bot.send_message(message.chat.id, f"🔍 Buscando '{query}' en YouTube...")
    
    try:
        ydl_opts = {'format': 'bestaudio/best', 'quiet': True, 'noplaylist': True}
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)['entries'][0]
            title = info['title']
            url = info['webpage_url']
        
        user_states[message.chat.id] = {'query': title, 'url': url}
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📥 Descargar y Mixear", callback_data="start_dl"))
        bot.send_message(message.chat.id, f"💎 **Encontrado:** {title}\n¿Le damos al bypass?", reply_markup=markup)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "start_dl")
def download_process(call):
    chat_id = call.message.chat.id
    url = user_states[chat_id]['url']
    bot.edit_message_text(f"Bajando audio de la nube... ☁️", chat_id, call.message.message_id)
    
    try:
        path = f"song_{chat_id}.mp3"
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'song_{chat_id}.%(ext)s',
            'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '128'}],
            'quiet': True
        }
        with YoutubeDL(ydl_opts) as ydl: ydl.download([url])
        
        user_states[chat_id]['song_path'] = path
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ Con Intro Extra", callback_data="intro_si"))
        markup.add(types.InlineKeyboardButton("❌ Solo Intrucidity", callback_data="intro_no"))
        bot.send_message(chat_id, "¡Listo! ¿Metemos voz o intro extra? 🎤", reply_markup=markup)
    except Exception as e:
        bot.send_message(chat_id, f"Error: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('intro_'))
def handle_intro(call):
    chat_id = call.message.chat.id
    if call.data == "intro_si":
        user_states[chat_id]['waiting_intro'] = True
        bot.send_message(chat_id, "Mándame el audio de tu intro. 🎤")
    else:
        bot.send_message(chat_id, "Mezclando... 🎚️")
        process_mix(chat_id, None)

@bot.message_handler(content_types=['audio', 'voice', 'document'])
def receive_intro(message):
    chat_id = message.chat.id
    if user_states.get(chat_id, {}).get('waiting_intro'):
        file_info = bot.get_file(message.audio.file_id if message.audio else message.voice.file_id if message.voice else message.document.file_id)
        intro_path = f"opt_{chat_id}.mp3"
        with open(intro_path, 'wb') as f: f.write(bot.download_file(file_info.file_path))
        process_mix(chat_id, intro_path)

def process_mix(chat_id, opt_path):
    try:
        # Base obligatoria
        base = AudioSegment.from_file("Intrucidity.wav")
        if opt_path:
            opt = apply_pro_fx(AudioSegment.from_file(opt_path))
            base = base.append(opt, crossfade=1500)
        
        # Bypass de canción
        song = AudioSegment.from_file(user_states[chat_id]['song_path'])
        song = song._spawn(song.raw_data, overrides={'frame_rate': int(song.frame_rate * 1.04)}).set_frame_rate(44100).set_channels(1)
        
        final = base.append(song, crossfade=2000)
        if len(final) > 420000: final = final[:420000] # Límite 7 min
        
        out = f"RESULT_{chat_id}.mp3"
        final.export(out, format="mp3", bitrate="128k")
        
        with open(out, 'rb') as f:
            bot.send_audio(chat_id, f, caption="✅ **BYPASS OK**\nSúbelo como: 333_MIX_YT")
            
        # Limpieza total
        for p in [user_states[chat_id]['song_path'], opt_path, out]:
            if p and os.path.exists(p): os.remove(p)
        user_states.pop(chat_id)
    except Exception as e:
        bot.send_message(chat_id, f"Fallo: {e}")

if __name__ == "__main__":
    keep_alive()
    bot.polling()

