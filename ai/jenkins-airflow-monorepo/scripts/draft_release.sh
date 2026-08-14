#!/bin/bash
# ==============================================================================
# 脚本名称: draft_release.sh
# 功能描述: 从 dev 分支提取指定的 DAG 目录，自动创建发布分支并推送到远端
# 适用场景: Airflow Monorepo 增量发布 (选择性提取功能上线)
# ==============================================================================

set -e # 遇到错误立即退出

# 1. 检查参数
if [ "$#" -eq 0 ]; then
    echo "❌ 错误: 未提供任何要发布的 DAG 名称。"
    echo "👉 用法: $0 <dag_name_1> [dag_name_2] ..."
    echo "💡 示例: bash scripts/draft_release.sh user_behavior_dag sales_report_dag"
    exit 1
fi

# 2. 准备基础信息
# 尝试获取 Git 用户名作为分支前缀，获取不到则使用系统用户名
USER_NAME=$(git config user.name | tr ' ' '_' | tr -d '[[:punct:]]')
if [ -z "$USER_NAME" ]; then
    USER_NAME=$(whoami)
fi
DATE_SUFFIX=$(date +"%Y%m%d%H%M")
RELEASE_BRANCH="release/${USER_NAME}-${DATE_SUFFIX}"

echo "🔄 正在同步远端仓库状态 (fetch origin)..."
git fetch origin dev
git fetch origin main

# 3. 检查本地环境是否干净
if ! git diff-index --quiet HEAD --; then
    echo "❌ 错误: 本地仓库有未提交的修改！"
    echo "请先清理本地状态 (执行 git commit 或 git stash) 后再运行此脚本。"
    exit 1
fi

# 4. 基于最新的 main 创建临时发布分支
echo "🌱 正在基于 origin/main 创建发布分支: $RELEASE_BRANCH"
git checkout -b "$RELEASE_BRANCH" origin/main

# 5. 循环提取特定的 DAG 目录
echo "📦 开始从 dev 分支提取指定的 DAG 代码..."
EXTRACTED_DAGS=""

for DAG in "$@"; do
    DAG_PATH="dags/$DAG"
    
    # 检查 dev 分支是否存在该 DAG 目录
    if git ls-tree -d origin/dev:"dags" | grep -q "^$DAG$"; then
        echo "  ✅ 正在提取: $DAG_PATH"
        # 核心魔法：只把指定的目录 checkout 过来覆盖当前工作区
        git checkout origin/dev -- "$DAG_PATH"
        EXTRACTED_DAGS="$EXTRACTED_DAGS $DAG"
    else
        echo "  ⚠️ 警告: 在 origin/dev 分支中未找到 $DAG_PATH 目录，跳过。"
    fi
done

# 6. 提交并推送
if git status --porcelain | grep -q "^[MADRCU]"; then
    echo "📝 检测到代码变更，正在提交..."
    git commit -m "Release: 提取 DAG 准备发布 -> $EXTRACTED_DAGS"
    
    echo "🚀 正在推送到远端仓库..."
    git push origin "$RELEASE_BRANCH"
    
    echo ""
    echo "================================================================="
    echo "🎉 发布准备成功！"
    echo "📁 包含的 DAG: $EXTRACTED_DAGS"
    echo "🌿 远端分支已创建: $RELEASE_BRANCH"
    echo ""
    echo "👉 下一步操作:"
    echo "   请前往 GitHub，针对分支 [$RELEASE_BRANCH]"
    echo "   创建一个合并到 [main] 分支的 PR (Pull Request)。"
    echo "================================================================="
else
    echo ""
    echo "⚠️ 提取操作未产生任何代码变更 (要发布的 DAG 代码在 main 和 dev 中已完全一致)。"
    echo "🗑️ 正在清理本地临时分支..."
    git checkout main
    git branch -D "$RELEASE_BRANCH"
    echo "✅ 清理完毕，无需发布。"
fi
