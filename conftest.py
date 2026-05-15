import pytest
import allure
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

# =============================
# 失败自动记录（Allure）
# =============================
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item):
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        allure.attach(
            "用例执行失败",
            name="失败信息",
            attachment_type=allure.attachment_type.TEXT
        )