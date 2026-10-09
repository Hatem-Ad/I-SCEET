#!/bin/bash
# ================================================================================
#  I-SCEET — Launch Script
#  Usage: bash start.sh            (VENV_DIR can be overridden from the env)
#  Copyright (c) 2026 Hatem Adouani — MIT License
# ================================================================================

set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${VENV_DIR:-$REPO_DIR/.venv}"
UI_DIR="$REPO_DIR/ui"
LOG_FILE="$REPO_DIR/isceet.log"

# ── COLORS ────────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "======================================"
echo "   I-SCEET Toolchain"
echo "   Intelligent Safety-Critical"
echo "   Engineering Environment Toolchain"
echo "======================================"
echo -e "${NC}"

# ── STEP 1: Check configuration ───────────────────────────────────────────────
echo -e "${YELLOW}[1/4] Checking configuration...${NC}"
if [ ! -f "$REPO_DIR/.env" ] || ! grep -qE '^COLAB_URL=.+' "$REPO_DIR/.env"; then
    echo -e "${RED}⚠️  COLAB_URL is not set in .env — copy .env.example to .env and set it.${NC}"
    echo -e "${RED}   The UI will start, but the pipeline cannot reach the model server.${NC}"
else
    echo -e "${GREEN}✅ .env found with COLAB_URL${NC}"
fi

# ── STEP 2: Activate virtual environment ──────────────────────────────────────
echo -e "${YELLOW}[2/4] Activating virtual environment...${NC}"
if [ ! -f "$VENV_DIR/bin/activate" ]; then
    echo -e "${YELLOW}⚠️  Venv not found. Creating $VENV_DIR ...${NC}"
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    pip install --quiet -r "$REPO_DIR/requirements.txt"
    echo -e "${GREEN}✅ Venv created and dependencies installed${NC}"
else
    source "$VENV_DIR/bin/activate"
    echo -e "${GREEN}✅ Venv activated: $VENV_DIR${NC}"
fi

# ── STEP 3: Initialize SQLite database ────────────────────────────────────────
echo -e "${YELLOW}[3/4] Initializing database...${NC}"
(cd "$REPO_DIR" && python3 -c "from Backend.db import init_db; init_db(); print('DB ready')")
echo -e "${GREEN}✅ SQLite database ready${NC}"

# ── STEP 4: Launch Streamlit ──────────────────────────────────────────────────
echo -e "${YELLOW}[4/4] Launching I-SCEET interface...${NC}"
echo ""
echo -e "${GREEN}======================================"
echo "   🚀 I-SCEET is starting..."
echo "   Open: http://localhost:8501"
echo "======================================"
echo -e "${NC}"
echo ""
echo "📋 Quick start:"
echo "   1. Go to '1 Upload' → create project + upload docs"
echo "   2. Go to '2 Pipeline' → check the Colab connection → launch"
echo "   3. Go to '3 Revue' → review generated artifacts"
echo ""
echo "Press Ctrl+C to stop"
echo ""

cd "$UI_DIR"
streamlit run app.py \
    --server.port 8501 \
    --server.headless false \
    --browser.gatherUsageStats false \
    2>&1 | tee -a "$LOG_FILE"
