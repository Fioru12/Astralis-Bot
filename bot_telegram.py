#!/usr/bin/env python3
"""
Astralis Server Manager Bot 🚀
Bot Telegram con menu a pulsanti per gestire:
- Server Zomboid
- Macchina (reboot, shutdown, screen on/off)
- Docker (container, servizi)
- Monitoraggio e notifiche
"""

import os
import sys
import subprocess
import time
import re
import logging
from pathlib import Path

# Configurazione
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "IL_TUO_TOKEN_QUI")
AUTHORIZED_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

PROJECT_DIR = Path(__file__).parent.resolve()
DOCKER_COMPOSE = PROJECT_DIR / "docker-compose.yml"
SERVER_INI = PROJECT_DIR / "data" / "Server" / "AstralisZomboid.ini"

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


# ========== UTILITY ==========

def run_cmd(cmd, timeout=30):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip() or r.stderr.strip()
    except Exception as e:
        return f"Errore: {e}"


def is_authorized(update):
    if not AUTHORIZED_CHAT_ID or AUTHORIZED_CHAT_ID == "IL_TUO_CHAT_ID_QUI":
        return True
    return str(update.effective_user.id) == AUTHORIZED_CHAT_ID or str(update.effective_chat.id) == AUTHORIZED_CHAT_ID


# ========== DATI SISTEMA ==========

def get_system():
    cpu = run_cmd(r"top -bn1 | grep 'Cpu(s)' | awk '{print $2+$4}'") or "N/A"
    cpu_temp = run_cmd("cat /sys/class/thermal/thermal_zone*/temp 2>/dev/null | head -1")
    cpu_temp = f"{int(cpu_temp)/1000:.1f}°C" if cpu_temp and cpu_temp.isdigit() else "N/A"
    mem = run_cmd("free -h | grep Mem: | awk '{print $3\"/\"$2}'") or "N/A"
    mem_p = run_cmd("free | grep Mem: | awk '{printf \"%.0f\", $3/$2*100}'") or "0"
    disk = run_cmd("df -h / | tail -1 | awk '{print $3\"/\"$2\" (\"$5\")\"}'") or "N/A"
    uptime = run_cmd("uptime -p | sed 's/up //'") or "N/A"
    load = run_cmd("cat /proc/loadavg | awk '{print $1, $2, $3}'") or "N/A"
    return {"cpu": f"{cpu}%", "temp": cpu_temp, "ram": mem, "ram_p": f"{mem_p}%", "disk": disk, "uptime": uptime, "load": load}


def get_docker():
    status = run_cmd("docker ps -a --filter name=zomboid-server --format '{{.Status}}' 2>/dev/null")
    running = "Up" in status if status else False
    containers = run_cmd("docker ps --format 'table {{.Names}}\t{{.Status}}' 2>/dev/null") or "Nessun container"
    return {"running": running, "status": status or "Fermo", "containers": containers}


def get_server_config():
    cfg = {}
    if SERVER_INI.exists():
        with open(SERVER_INI) as f:
            for line in f:
                l = line.strip()
                if "=" in l and not l.startswith("#"):
                    k, v = l.split("=", 1)
                    cfg[k.strip()] = v.strip()
    return cfg


# ========== TASTIERA ==========

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, BotCommand
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

def home_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎮 Zomboid", callback_data="menu_zomboid")],
        [InlineKeyboardButton("🖥️ Server", callback_data="menu_server")],
        [InlineKeyboardButton("🐳 Docker", callback_data="menu_docker")],
        [InlineKeyboardButton("📊 Monitor", callback_data="menu_monitor")],
        [InlineKeyboardButton("❓ Aiuto", callback_data="help")],
    ])

def back_home():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Home", callback_data="home")]])

def zomboid_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Status", callback_data="z_status")],
        [InlineKeyboardButton("▶️ Avvia", callback_data="z_start"),
         InlineKeyboardButton("⏹️ Ferma", callback_data="z_stop")],
        [InlineKeyboardButton("🔄 Riavvia", callback_data="z_restart")],
        [InlineKeyboardButton("🏠 Home", callback_data="home")],
    ])

def server_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💻 Sistema", callback_data="s_system")],
        [InlineKeyboardButton("🖥️ Schermo OFF", callback_data="s_screen_off"),
         InlineKeyboardButton("🖥️ Schermo ON", callback_data="s_screen_on")],
        [InlineKeyboardButton("🔄 Riavvia PC", callback_data="s_reboot"),
         InlineKeyboardButton("⏻ Spegni PC", callback_data="s_shutdown")],
        [InlineKeyboardButton("🔁 Riavvia Bot", callback_data="s_restart_bot")],
        [InlineKeyboardButton("🏠 Home", callback_data="home")],
    ])

def docker_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Container", callback_data="d_containers")],
        [InlineKeyboardButton("🔄 Riavvia Docker", callback_data="d_restart_docker")],
        [InlineKeyboardButton("🏠 Home", callback_data="home")],
    ])

def monitor_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Risorse", callback_data="m_risorse")],
        [InlineKeyboardButton("🔔 Test Notifica", callback_data="m_test_notify")],
        [InlineKeyboardButton("📝 Ultimi Log", callback_data="m_logs")],
        [InlineKeyboardButton("🏠 Home", callback_data="home")],
    ])


# ========== HANDLER ==========

async def home(update, context):
    query = update.callback_query
    if query:
        await query.answer()
        await query.message.edit_text("🏠 <b>Astralis Server Manager</b>\n\nScegli una sezione:", parse_mode="HTML", reply_markup=home_keyboard())
    else:
        await update.message.reply_text("🏠 <b>Astralis Server Manager</b>\n\nScegli una sezione:", parse_mode="HTML", reply_markup=home_keyboard())

async def start(update, context):
    if not is_authorized(update):
        await update.message.reply_text("❌ Non sei autorizzato.")
        return
    chat_id = update.effective_chat.id
    logger.info(f"Chat ID: {chat_id}")
    await home(update, context)


# --- ZOMBOID ---

async def menu_zomboid(update, context):
    q = update.callback_query
    await q.answer()
    docker = get_docker()
    emoji = "✅" if docker["running"] else "❌"
    await q.message.edit_text(f"<b>🎮 ZOMBOID</b>\n\n{emoji} Stato: {docker['status']}", parse_mode="HTML", reply_markup=zomboid_keyboard())

async def z_status(update, context):
    q = update.callback_query
    await q.answer()
    docker = get_docker()
    sys = get_system()
    cfg = get_server_config()
    e = "✅" if docker["running"] else "❌"
    msg = f"""<b>🎮 ZOMBOID - Status</b>
{e} Stato: <b>{'ONLINE' if docker['running'] else 'OFFLINE'}</b>
📌 IP: <code>95.246.185.101:{cfg.get('DefaultPort','16261')}</code>
🗺️ Mappa: {cfg.get('Map','Muldraugh, KY')}
🚗 PVP: {'✅' if cfg.get('PVP')=='true' else '❌'}
🔓 Accesso: {'Aperto' if cfg.get('Open')=='true' else 'Whitelist'}

🖥️ CPU: {sys['cpu']} @ {sys['temp']}
💾 RAM: {sys['ram']} ({sys['ram_p']})
💿 Disco: {sys['disk']}
⏱️ Uptime: {sys['uptime']}"""
    await q.message.edit_text(msg, parse_mode="HTML", reply_markup=zomboid_keyboard())

async def z_start(update, context):
    q = update.callback_query
    await q.answer()
    await q.message.edit_text("🔄 Avvio server...", reply_markup=back_home())
    run_cmd(f"cd {PROJECT_DIR} && docker compose up -d")
    time.sleep(3)
    s = get_docker()
    if s["running"]:
        await q.message.edit_text("✅ Server avviato!", reply_markup=zomboid_keyboard())
    else:
        await q.message.edit_text("⚠️ Errore avvio server", reply_markup=zomboid_keyboard())

async def z_stop(update, context):
    q = update.callback_query
    await q.answer()
    run_cmd(f"cd {PROJECT_DIR} && docker compose down")
    time.sleep(2)
    await q.message.edit_text("⏹️ Server fermato!", reply_markup=zomboid_keyboard())

async def z_restart(update, context):
    q = update.callback_query
    await q.answer()
    await q.message.edit_text("🔄 Riavvio server...", reply_markup=back_home())
    run_cmd(f"cd {PROJECT_DIR} && docker compose restart")
    time.sleep(3)
    await q.message.edit_text("🔄 Server riavviato!", reply_markup=zomboid_keyboard())


# --- SERVER ---

async def menu_server(update, context):
    q = update.callback_query
    await q.answer()
    await q.message.edit_text("<b>🖥️ SERVER</b>\n\nGestisci la macchina:", parse_mode="HTML", reply_markup=server_keyboard())

async def s_system(update, context):
    q = update.callback_query
    await q.answer()
    s = get_system()
    msg = f"""<b>💻 SISTEMA</b>
🖥️ CPU: {s['cpu']} 🌡️ {s['temp']}
💾 RAM: {s['ram']} ({s['ram_p']})
💿 Disco: {s['disk']}
📊 Load: {s['load']}
⏱️ Uptime: {s['uptime']}"""
    await q.message.edit_text(msg, parse_mode="HTML", reply_markup=server_keyboard())

async def s_screen_off(update, context):
    q = update.callback_query
    await q.answer()
    run_cmd("sudo DISPLAY=:0 xset dpms force off 2>/dev/null || sudo vbetool dpms off 2>/dev/null")
    await q.message.edit_text("🖥️ Schermo spento! (Risparmio ~20W)", reply_markup=server_keyboard())

async def s_screen_on(update, context):
    q = update.callback_query
    await q.answer()
    run_cmd("sudo DISPLAY=:0 xset dpms force on 2>/dev/null || sudo vbetool dpms on 2>/dev/null")
    await q.message.edit_text("🖥️ Schermo acceso!", reply_markup=server_keyboard())

async def s_reboot(update, context):
    q = update.callback_query
    await q.answer()
    await q.message.edit_text("⚠️ Riavvio PC tra 10 secondi...\nIl bot tornerà online automaticamente.", reply_markup=None)
    run_cmd("sudo shutdown -r +1 'Riavvio richiesto da Telegram'")

async def s_shutdown(update, context):
    q = update.callback_query
    await q.answer()
    await q.message.edit_text("⚠️ Spegnimento PC tra 1 minuto...\nPer annullare: sudo shutdown -c", reply_markup=None)
    run_cmd("sudo shutdown -h +1 'Spegnimento richiesto da Telegram'")

async def s_restart_bot(update, context):
    q = update.callback_query
    await q.answer()
    run_cmd("sudo systemctl restart astralis-bot 2>/dev/null")
    await q.message.edit_text("🔄 Bot riavviato! Tornerà online tra pochi secondi.", reply_markup=None)


# --- DOCKER ---

async def menu_docker(update, context):
    q = update.callback_query
    await q.answer()
    c = run_cmd("docker ps --format 'table {{.Names}}\t{{.Status}}' 2>/dev/null") or "Nessun container"
    await q.message.edit_text(f"<b>🐳 DOCKER</b>\n\n<pre>{c}</pre>", parse_mode="HTML", reply_markup=docker_keyboard())

async def d_containers(update, context):
    q = update.callback_query
    await q.answer()
    c = run_cmd("docker ps -a --format 'table {{.Names}}\t{{.Status}}' 2>/dev/null") or "Nessun container"
    await q.message.edit_text(f"<b>📋 TUTTI I CONTAINER</b>\n\n<pre>{c}</pre>", parse_mode="HTML", reply_markup=docker_keyboard())

async def d_restart_docker(update, context):
    q = update.callback_query
    await q.answer()
    run_cmd("systemctl restart docker 2>/dev/null")
    await q.message.edit_text("🔄 Docker riavviato! I container ripartiranno automaticamente.", reply_markup=docker_keyboard())


# --- MONITOR ---

async def menu_monitor(update, context):
    q = update.callback_query
    await q.answer()
    await q.message.edit_text("<b>📊 MONITOR</b>\n\nRisorse, log e notifiche:", parse_mode="HTML", reply_markup=monitor_keyboard())

async def m_risorse(update, context):
    q = update.callback_query
    await q.answer()
    s = get_system()
    docker = get_docker()
    msg = f"""<b>📊 RISORSE</b>
🖥️ CPU: {s['cpu']} 🌡️ {s['temp']}
💾 RAM: {s['ram']} ({s['ram_p']})
💿 Disco: {s['disk']}
📊 Load: {s['load']}
⏱️ Uptime: {s['uptime']}

<b>🐳 Docker:</b> {docker['status']}
<b>🎮 Zomboid:</b> {'✅ Online' if docker['running'] else '❌ Offline'}"""
    await q.message.edit_text(msg, parse_mode="HTML", reply_markup=monitor_keyboard())

async def m_test_notify(update, context):
    q = update.callback_query
    await q.answer()
    await q.message.edit_text("🔔 Test notifica: se vedi questo messaggio, le notifiche funzionano!", reply_markup=monitor_keyboard())

async def m_logs(update, context):
    q = update.callback_query
    await q.answer()
    logs = run_cmd("journalctl -u astralis-bot --since '10 min ago' --no-pager 2>&1 | tail -15")
    if len(logs) > 1500:
        logs = logs[-1500:]
    await q.message.edit_text(f"<b>📝 ULTIMI LOG (10 min)</b>\n\n<pre>{logs}</pre>", parse_mode="HTML", reply_markup=monitor_keyboard())


# --- HELP ---

async def help_cmd(update, context):
    query = update.callback_query
    if query:
        await query.answer()
        await query.message.edit_text("""<b>❓ AIUTO</b>

<b>🎮 Zomboid</b> - Gestisci server
<b>🖥️ Server</b> - Sistema, schermo, reboot
<b>🐳 Docker</b> - Container e servizi
<b>📊 Monitor</b> - Risorse e log

<b>Chat ID:</b> <code>1111385054</code>""", parse_mode="HTML", reply_markup=home_keyboard())
    else:
        await update.message.reply_text("Usa /start per il menu principale!")


# ========== MAIN ==========

def main():
    if TOKEN == "IL_TUO_TOKEN_QUI":
        print("ERRORE: Imposta TELEGRAM_BOT_TOKEN")
        sys.exit(1)

    app = Application.builder().token(TOKEN).build()

    # Comandi
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))

    # Menu callback
    app.add_handler(CallbackQueryHandler(home, pattern="^home$"))
    app.add_handler(CallbackQueryHandler(menu_zomboid, pattern="^menu_zomboid$"))
    app.add_handler(CallbackQueryHandler(menu_server, pattern="^menu_server$"))
    app.add_handler(CallbackQueryHandler(menu_docker, pattern="^menu_docker$"))
    app.add_handler(CallbackQueryHandler(menu_monitor, pattern="^menu_monitor$"))
    app.add_handler(CallbackQueryHandler(help_cmd, pattern="^help$"))

    # Zomboid
    app.add_handler(CallbackQueryHandler(z_status, pattern="^z_status$"))
    app.add_handler(CallbackQueryHandler(z_start, pattern="^z_start$"))
    app.add_handler(CallbackQueryHandler(z_stop, pattern="^z_stop$"))
    app.add_handler(CallbackQueryHandler(z_restart, pattern="^z_restart$"))

    # Server
    app.add_handler(CallbackQueryHandler(s_system, pattern="^s_system$"))
    app.add_handler(CallbackQueryHandler(s_screen_off, pattern="^s_screen_off$"))
    app.add_handler(CallbackQueryHandler(s_screen_on, pattern="^s_screen_on$"))
    app.add_handler(CallbackQueryHandler(s_reboot, pattern="^s_reboot$"))
    app.add_handler(CallbackQueryHandler(s_shutdown, pattern="^s_shutdown$"))
    app.add_handler(CallbackQueryHandler(s_restart_bot, pattern="^s_restart_bot$"))

    # Docker
    app.add_handler(CallbackQueryHandler(d_containers, pattern="^d_containers$"))
    app.add_handler(CallbackQueryHandler(d_restart_docker, pattern="^d_restart_docker$"))

    # Monitor
    app.add_handler(CallbackQueryHandler(m_risorse, pattern="^m_risorse$"))
    app.add_handler(CallbackQueryHandler(m_test_notify, pattern="^m_test_notify$"))
    app.add_handler(CallbackQueryHandler(m_logs, pattern="^m_logs$"))

    # Menu comandi Telegram
    async def set_commands(app):
        await app.bot.set_my_commands([
            BotCommand("start", "Menu principale 🏠"),
            BotCommand("help", "Aiuto ❓"),
        ])
    app.post_init = set_commands

    print("✅ Astralis Server Manager Bot avviato!")
    print("   Menu a pulsanti attivo su Telegram")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()