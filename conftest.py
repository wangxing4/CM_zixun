import json
import platform
from pathlib import Path

import pytest
import allure
from common.config import PROJECT_ROOT, load_env
from common.http_client import HttpClient


@pytest.fixture
def client():
    # 匿名客户端用于登录、注册等不应预置登录态的场景。
    return HttpClient(env="test")


@pytest.fixture
def auth_client(client):
    # 已登录客户端用于默认依赖 token 的业务接口场景。
    client.login()
    return client


def _allure_results_dir(config):
    report_dir = getattr(config.option, "allure_report_dir", None)
    if not report_dir:
        return None

    report_dir = Path(report_dir)
    if not report_dir.is_absolute():
        report_dir = PROJECT_ROOT / report_dir
    return report_dir


def pytest_sessionfinish(session, exitstatus):
    results_dir = _allure_results_dir(session.config)
    if not results_dir:
        return

    results_dir.mkdir(parents=True, exist_ok=True)
    env_config = load_env("test")
    environment = {
        "Project": "CM_zixun",
        "Environment": "test",
        "Base URL": env_config.get("base_url", ""),
        "Python": platform.python_version(),
        "Platform": platform.platform(),
    }
    (results_dir / "environment.properties").write_text(
        "\n".join(f"{key}={value}" for key, value in environment.items()),
        encoding="utf-8"
    )
    categories = [
        {
            "name": "环境或网络问题",
            "matchedStatuses": ["broken"],
            "messageRegex": ".*(ConnectionError|NameResolutionError|Timeout|DNS).*"
        },
        {
            "name": "测试数据问题",
            "matchedStatuses": ["failed", "skipped", "broken"],
            "messageRegex": ".*(次数已用完|未找到|前置数据|测试账号).*"
        },
        {
            "name": "断言失败",
            "matchedStatuses": ["failed"],
            "messageRegex": ".*AssertionError.*"
        }
    ]
    (results_dir / "categories.json").write_text(
        json.dumps(categories, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


# =============================
# 失败自动记录（Allure）
# =============================
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item):
    outcome = yield
    report = outcome.get_result()

    if report.when in ("setup", "call") and report.failed:
        allure.attach(
            str(report.longrepr),
            name="失败信息",
            attachment_type=allure.attachment_type.TEXT
        )

        client = item.funcargs.get("auth_client") or item.funcargs.get("client")
        last_exchange = getattr(client, "last_exchange", None)
        if last_exchange:
            allure.attach(
                json.dumps(last_exchange, ensure_ascii=False, indent=2),
                name="最后一次接口请求响应",
                attachment_type=allure.attachment_type.JSON
            )
