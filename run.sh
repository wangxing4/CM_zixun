#!/bin/bash

echo "== 清理旧报告 =="
rm -rf allure-results allure-report

echo "== 执行测试 =="
pytest

echo "== 生成并打开 Allure 报告 =="
allure serve allure-results