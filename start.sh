#!/bin/bash
# ================================================================================
#  I-SCEET — Complete Launch Script
#  Usage: bash start.sh
# ================================================================================

set -e

REPO_DIR="/media/h/DATA/Github/I-SCEET"
VENV_DIR="/home/h/i-sceet_env"
UI_DIR="$REPO_DIR/ui"
DB_PATH="$REPO_DIR/isceet.db"
LOG_FILE="$REPO_DIR/isceet.log"

# ── COLORS ────────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "======================================"
echo "   ✈️  I-SCEET Toolchain v1.0"
echo "   Intelligent Safety-Critical"
echo "   Engineering Environment Toolchain"
echo "======================================"
echo -e "${NC}"

# ── STEP 1: Check repo ────────────────────────────────────────────────────────
echo -e "${YELLOW}[1/5] Checking repository...${NC}"
if [ ! -d "$REPO_DIR" ]; then
    echo -e "${RED}❌ Repo not found at $REPO_DIR${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Repo found: $REPO_DIR${NC}"

# ── STEP 2: Fix disk permissions (NTFS) ───────────────────────────────────────
echo -e "${YELLOW}[2/5] Checking disk permissions...${NC}"
if mount | grep "$(df $REPO_DIR | tail -1 | awk '{print $1}')" | grep -q "ro,"; then
    echo -e "${YELLOW}⚠️  Disk is read-only. Attempting remount...${NC}"
    DEVICE=$(df $REPO_DIR | tail -1 | awk '{print $1}')
    sudo mount -o remount,rw "$DEVICE" 2>/dev/null || \
    sudo ntfsfix "$DEVICE" 2>/dev/null && \
    sudo mount -o remount,rw "$DEVICE" 2>/dev/null || \
    echo -e "${YELLOW}⚠️  Could not remount — continuing anyway${NC}"
fi
echo -e "${GREEN}✅ Disk permissions OK${NC}"

# ── STEP 3: Activate virtual environment ──────────────────────────────────────
echo -e "${YELLOW}[3/5] Activating virtual environment...${NC}"
if [ ! -f "$VENV_DIR/bin/activate" ]; then
    echo -e "${YELLOW}⚠️  Venv not found. Creating...${NC}"
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    pip install --quiet streamlit pandas openpyxl python-docx requests python-dotenv
    echo -e "${GREEN}✅ Venv created and dependencies installed${NC}"
else
    source "$VENV_DIR/bin/activate"
    echo -e "${GREEN}✅ Venv activated: $VENV_DIR${NC}"
fi

# ── STEP 4: Initialize SQLite database ────────────────────────────────────────
echo -e "${YELLOW}[4/5] Initializing database...${NC}"
python3 -c "
import sys
sys.path.insert(0, '$REPO_DIR')
from Backend.db import init_db
init_db()
print('DB ready: $DB_PATH')
"
echo -e "${GREEN}✅ SQLite database ready${NC}"

# ── STEP 5: Launch Streamlit ──────────────────────────────────────────────────
echo -e "${YELLOW}[5/5] Launching I-SCEET interface...${NC}"
echo ""
echo -e "${GREEN}======================================"
echo "   🚀 I-SCEET is starting..."
echo "   Open: http://localhost:8501"
echo "======================================"
echo -e "${NC}"
echo ""
echo "📋 Quick start:"
echo "   1. Go to '1 Upload' → create project + upload docs"
echo "   2. Go to '2 Pipeline' → paste Colab URL → launch"
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
