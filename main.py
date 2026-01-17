import sys
import os

# --- PARCHE DE HIERRO PARA AUDIOOP ---
try:
    import audioop
except ImportError:
    try:
        import audioop_lts as audioop
        sys.modules['audioop'] = audioop
    except ImportError:
        pass

import telebot
from telebot import types
from pydub import AudioSegment
import librosa
import soundfile as sf
import numpy as np
from flask import Flask
from threading import Thread

# --- SERVIDOR PARA RENDER ---
app = Flask('')
@app.route('/')
def home(): return "DJ FARAON V4 - IA MIXER ONLINE 🔥"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    Thread(target=run).start()

# --- CONFIGURACIÓN ---
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)
user_states = {}

# --- FUNCIÓN DE BYPASS PRO ---
def apply_bypass(audio_path, intro_path):
    intro = AudioSegment.from_file(intro_path)
    song = AudioSegment.from_file(audio_path)
    # Bypass: +4% Pitch para mayor seguridad en Roblox y Mono
    song = song._spawn(song.raw_data, overrides={'frame_rate': int(song.frame_rate * 1.04)})
    song = song.set_frame_rate(44100).set_channels(1)
    return intro.append(song, crossfade=2000)

# --- COMANDOS ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🔥 **DJ FARAON IA PRO**\n\n"
                          "🚀 `/bypass` - Procesa una canción con protección Roblox.\n"
                          "🎧 `/mix` - Mezcla épica entre instrumentales (IA DJ).")

@bot.message_handler(commands=['bypass'])
def cmd_bypass(message):
    user_states[message.chat.id] = 'WAITING_BYPASS'
    bot.reply_to(message, "📥 **MODO BYPASS:** Envíame el MP3 para procesarlo.")

@bot.message_handler(commands=['mix'])
def cmd_mix(message):
    user_states[message.chat.id] = 'WAITING_MIX'
    bot.reply_to(message, "🎧 **MODO AUTOMIX:** Envíame el MP3 y yo me encargo de la transición épica con instrumentales.")

@bot.message_handler(content_types=['audio', 'document'])
def handle_audio(message):
    chat_id = message.chat.id
    state = user_states.get(chat_id)

    if not state:
        bot.reply_to(message, "❌ Primero elige un comando: `/bypass` o `/mix`.")
        return

    file_info = bot.get_file(message.audio.file_id if message.content_type == 'audio' else message.document.file_id)
    downloaded = bot.download_file(file_info.file_path)
    input_p = f"in_{chat_id}.mp3"
    
    with open(input_p, 'wb') as f:
        f.write(downloaded)

    msg = bot.send_message(chat_id, "🪄 La IA está trabajando en tu audio...")

    try:
        if state == 'WAITING_BYPASS':
            # Elegir intro (usamos la oficial por default en este comando)
            final = apply_bypass(input_p, "Intrucidity.wav")
            out_name = f"BYPASS_{chat_id}.wav"
            final.export(out_name, format="wav", codec="libmp3lame", parameters=["-q:a", "0"])
            
        elif state == 'WAITING_MIX':
            # IA AUTOMIX LOGIC
            y, sr = librosa.load(input_p)
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr) # Detectar BPM
            bot.edit_message_text(f"🥁 BPM Detectado: {int(tempo)}. Sincronizando instrumentales...", chat_id, msg.message_id)
            
            # Cargar canción e instrumental
            song = AudioSegment.from_file(input_p)
            # Aquí deberías tener un archivo llamado 'Instrumental_Base.wav' para el mix
            base = AudioSegment.from_file("Intrucidity.wav") 
            
            # Ajuste de volumen IA para transición
            song_in = song.fade_in(3000)
            final = base.append(song_in, crossfade=4000) # Crossfade largo para efecto DJ
            
            out_name = f"AUTOMIX_{chat_id}.wav"
            final.export(out_name, format="wav", codec="libmp3lame", parameters=["-q:a", "0"])

        with open(out_name, 'rb') as f:
            bot.send_document(chat_id, f, caption=f"✅ **{state} COMPLETADO**")

        os.remove(input_p)
        os.remove(out_name)
        user_states[chat_id] = None

    except Exception as e:
        bot.send_message(chat_id, f"❌ Error IA: {e}")

if __name__ == "__main__":
    keep_alive()
    bot.polling(none_stop=True)

