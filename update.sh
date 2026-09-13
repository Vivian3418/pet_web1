#!/usr/bin/env bash
# =============================================================================
# vv_pet01 更新脚本
#
# 用途：拉取最新代码并重新构建、启动 Docker 服务，适用于部署机的例行更新。
#
# 用法：
#   ./update.sh                  # 标准更新：git pull + 重建镜像 + 滚动重启
#   ./update.sh --skip-pull      # 跳过 git pull，仅用当前代码重建并重启
#   ./update.sh --no-cache       # 构建时不使用 Docker 层缓存（排查构建问题时用）
#
# 说明：
#   * 数据库与上传文件位于具名数据卷 vv_pet01_data，重建容器不会丢失数据。
#   * 构建成功后才会重启容器，构建失败时旧容器保持运行，服务不受影响。
# =============================================================================

set -euo pipefail

# ------------------------------- 配置 ---------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

GIT_REMOTE="${GIT_REMOTE:-origin}"
GIT_BRANCH="${GIT_BRANCH:-}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"
HEALTH_TIMEOUT="${HEALTH_TIMEOUT:-90}"   # 等待容器变为 healthy 的秒数
NO_CACHE=""
SKIP_PULL=""

# ------------------------------ 工具函数 ------------------------------------
# info: 输出蓝色步骤日志；ok: 绿色成功日志；die: 红色错误日志并以 1 退出。
info() { printf '\033[1;34m[update]\033[0m %s\n' "$*"; }
ok()   { printf '\033[1;32m[  ok  ]\033[0m %s\n' "$*"; }
die()  { printf '\033[1;31m[fail  ]\033[0m %s\n' "$*" >&2; exit 1; }

usage() {
    sed -n '2,16p' "$0" | sed 's/^# \{0,1\}//'
    exit 0
}

# ------------------------------ 参数解析 ------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --skip-pull) SKIP_PULL="1" ;;
        --no-cache)  NO_CACHE="1" ;;
        -h|--help)   usage ;;
        *)           die "未知参数：$1（使用 --help 查看用法）" ;;
    esac
    shift
done

# ------------------------------ 前置检查 ------------------------------------
command -v docker >/dev/null 2>&1 || die "未检测到 docker 命令，请先安装 Docker"
[[ -f "$COMPOSE_FILE" ]] || die "找不到 $COMPOSE_FILE，请在项目根目录运行本脚本"

# 兼容 Docker Compose v2（docker compose）与 v1（docker-compose）
if docker compose version >/dev/null 2>&1; then
    COMPOSE=(docker compose -f "$COMPOSE_FILE")
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE=(docker-compose -f "$COMPOSE_FILE")
else
    die "未检测到 Docker Compose（docker compose 或 docker-compose 均可）"
fi

# ------------------------------ 第 1 步：拉取代码 ----------------------------
if [[ -n "$SKIP_PULL" ]]; then
    info "已跳过 git pull（--skip-pull）"
elif [[ -d .git ]]; then
    git diff --quiet || die "工作区存在未提交改动，为避免覆盖请先提交或储藏（git stash）后再更新"
    [[ -n "$GIT_BRANCH" ]] && git checkout "$GIT_BRANCH"
    info "拉取最新代码（$GIT_REMOTE $(git branch --show-current)）..."
    git pull --ff-only "$GIT_BRANCH" && ok "代码已是最新（$(git log -1 --format='%h %s')）" \
        || die "git pull 失败：存在分叉或网络问题，请手动处理后重试"
else
    info "当前目录不是 git 仓库，跳过拉取，直接使用现有代码构建"
fi

# ------------------------------ 第 2 步：构建镜像 ----------------------------
info "构建 Docker 镜像..."
BUILD_ARGS=(--pull)
[[ -n "$NO_CACHE" ]] && BUILD_ARGS+=(--no-cache)
"${COMPOSE[@]}" build "${BUILD_ARGS[@]}"
ok "镜像构建完成"

# ------------------------------ 第 3 步：重启服务 ----------------------------
# up -d 会对比镜像 ID：镜像有变化时重建容器，无变化时保持原容器不动；
# 数据卷 vv_pet01_data 在容器重建后依然挂载，数据不丢失。
info "启动 / 滚动更新服务..."
"${COMPOSE[@]}" up -d
ok "服务已启动"

# ------------------------------ 第 4 步：健康检查 ----------------------------
CONTAINER="${COMPOSE_PROJECT_NAME:-vv_pet01}_web"
info "等待容器健康检查通过（最长 ${HEALTH_TIMEOUT}s）..."
elapsed=0
until [[ "$(docker inspect -f '{{.State.Health.Status}}' "$CONTAINER" 2>/dev/null || echo unknown)" == "healthy" ]]; do
    (( elapsed += 3 ))
    if (( elapsed >= HEALTH_TIMEOUT )); then
        "${COMPOSE[@]}" logs --tail 30 web
        die "容器在 ${HEALTH_TIMEOUT}s 内未变为 healthy，请查看上方日志排查"
    fi
    sleep 3
done
ok "容器健康检查通过"

# ------------------------------ 第 5 步：清理旧镜像 -------------------------
# 重建后旧镜像会变成 <none> 悬空镜像，定期清理避免占用磁盘。
docker image prune -f >/dev/null 2>&1 && ok "已清理悬空旧镜像"

# ------------------------------ 结果摘要 ------------------------------------
ok "更新完成！访问 http://127.0.0.1:8000（中文 / 英文）"
"${COMPOSE[@]}" ps
