#!/bin/bash
# PumpGuard 一键启动脚本
# 用法: bash start.sh [sim|ai|java|web|bot|all]

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 加载环境变量
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
    echo "[Start] 已加载 .env 配置"
else
    echo "[Start] 未找到 .env，使用默认配置"
    echo "[Start] 提示: cp .env.template .env 并填入飞书配置"
fi

# ── 基础服务 ──────────────────────────────────────────────────────

start_infra() {
    echo "[Start] 启动基础服务 (PostgreSQL / InfluxDB / Kafka / EMQX / MinIO)..."
    docker compose up -d postgres influxdb kafka emqx minio
    echo "[Start] 等待服务就绪..."
    sleep 10
    echo "[Start] 基础服务已就绪"
}

# ── 仿真引擎 ──────────────────────────────────────────────────────

start_sim() {
    echo "[Start] 启动仿真引擎..."
    cd simulation-engine
    pip install -r requirements.txt -q
    python engine.py --output ./output &
    SIM_PID=$!
    cd ..
    echo "[Start] 仿真引擎 PID=$SIM_PID"
}

# ── AI 引擎 ──────────────────────────────────────────────────────

start_ai() {
    echo "[Start] 启动 AI 引擎 (FastAPI :8000)..."
    cd ai-engine
    pip install -r requirements.txt -q
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
    AI_PID=$!
    cd ..
    echo "[Start] AI 引擎 PID=$AI_PID"
}

# ── Java 业务服务 ────────────────────────────────────────────────

start_java() {
    echo "[Start] 编译并启动 Java 业务服务 (Spring Boot :8080)..."
    cd business-server
    ./mvnw spring-boot:run &
    JAVA_PID=$!
    cd ..
    echo "[Start] Java 服务 PID=$JAVA_PID"
}

# ── 前端看板 ──────────────────────────────────────────────────────

start_web() {
    echo "[Start] 启动前端看板 (Vite :3000)..."
    cd web-dashboard
    npm install --silent
    npm run dev &
    WEB_PID=$!
    cd ..
    echo "[Start] 前端看板 PID=$WEB_PID"
}

# ── 飞书 Bot ──────────────────────────────────────────────────────

start_bot() {
    echo "[Start] 启动飞书 Bot..."
    cd feishu-bot
    pip install requests kafka-python -q
    python bot.py &
    BOT_PID=$!
    cd ..
    echo "[Start] 飞书 Bot PID=$BOT_PID"
}

# ── 主逻辑 ──────────────────────────────────────────────────────

MODE=${1:-all}

case $MODE in
    infra)
        start_infra
        ;;
    sim)
        start_sim
        ;;
    ai)
        start_ai
        ;;
    java)
        start_java
        ;;
    web)
        start_web
        ;;
    bot)
        start_bot
        ;;
    all)
        start_infra
        start_sim
        sleep 5
        start_ai
        sleep 3
        start_java
        sleep 10
        start_web
        start_bot
        echo ""
        echo "============================================"
        echo " PumpGuard 全栈已启动"
        echo " 前端看板: http://localhost:3000"
        echo " AI 引擎:  http://localhost:8000/docs"
        echo " Java API: http://localhost:8080/api/pumps"
        echo " EMQX:    http://localhost:18083"
        echo "============================================"
        ;;
    *)
        echo "用法: bash start.sh [infra|sim|ai|java|web|bot|all]"
        ;;
esac

# 捕获 Ctrl+C
trap "echo '关闭所有服务...'; kill 0; exit 0" SIGINT SIGTERM

# 保持前台运行
if [ "$MODE" = "all" ]; then
    wait
fi
