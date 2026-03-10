#!/usr/bin/env bash
set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    Installing Lisa                           ║"
echo "╚══════════════════════════════════════════════════════════════╝"

# 1. check python
python3 --version >/dev/null 2>&1 || { echo "[lisa] Python3 required."; exit 1; }

# 2. check ollama
ollama --version >/dev/null 2>&1 || { echo "[lisa] Ollama required. Install from https://ollama.com"; exit 1; }

# 3. create venv and install
echo "[lisa] Setting up virtual environment..."
python3 -m venv .env
source .env/bin/activate 2>/dev/null || source .env/bin/activate.fish 2>/dev/null || true
pip install -e . --quiet

# 4. run environment probe
echo "[lisa] Detecting system environment..."
python3 -m env.probe

# 5. install fish hook
FISH_CONF="$HOME/.config/fish/conf.d"
if [ -d "$FISH_CONF" ]; then
    cp shell/hook.fish "$FISH_CONF/lisa.fish"
    echo "[lisa] Fish hook installed → $FISH_CONF/lisa.fish"
fi

# 6. install bash/zsh hook
if [ -f "$HOME/.bashrc" ]; then
    echo "source $(pwd)/shell/hook.sh" >> "$HOME/.bashrc"
    echo "[lisa] Bash hook added to ~/.bashrc"
fi

# 7. systemd timer for trimmer
if command -v systemctl >/dev/null 2>&1; then
    SYSTEMD_USER="$HOME/.config/systemd/user"
    mkdir -p "$SYSTEMD_USER"

    cat > "$SYSTEMD_USER/lisa-trim.service" << SERVICE
[Unit]
Description=Lisa memory trimmer

[Service]
Type=oneshot
ExecStart=$(pwd)/.env/bin/python -m memory.trimmer
WorkingDirectory=$(pwd)
SERVICE

    cat > "$SYSTEMD_USER/lisa-trim.timer" << TIMER
[Unit]
Description=Run Lisa memory trimmer daily

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
TIMER

    systemctl --user enable lisa-trim.timer 2>/dev/null || true
    systemctl --user start lisa-trim.timer 2>/dev/null || true
    echo "[lisa] Systemd timer installed (daily memory trim)."
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Lisa installed. Restart your shell then:                    ║"
echo "║  lisa \"install nmap and scan localhost\"                      ║"
echo "╚══════════════════════════════════════════════════════════════╝"
