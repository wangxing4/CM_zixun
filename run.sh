#!/bin/bash
set -u

echo "== 清理旧报告 =="
rm -rf allure-results allure-report

PYTHON_BIN="${PYTHON_BIN:-.venv/bin/python}"
if [ ! -x "$PYTHON_BIN" ]; then
  PYTHON_BIN="$(command -v python3 || true)"
fi

if [ -z "$PYTHON_BIN" ]; then
  echo "未找到 Python，请先配置虚拟环境或安装 python3"
  exit 1
fi

echo "== 执行测试 =="
"$PYTHON_BIN" -m pytest
TEST_EXIT_CODE=$?

echo "== 生成 Allure 静态报告 =="
if [ -d allure-results ] && command -v allure >/dev/null 2>&1; then
  allure generate allure-results -o allure-report --clean
  echo "报告已生成：allure-report/index.html"
elif [ ! -d allure-results ]; then
  echo "未找到 allure-results，跳过报告生成"
else
  echo "未安装 allure 命令，跳过报告生成"
fi

exit "$TEST_EXIT_CODE"
