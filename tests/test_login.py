import pytest
import allure
import json
from common.read_yaml import load_yaml

api = load_yaml("config/api.yaml")
cases = load_yaml("data/login.yaml")

@allure.feature("登录模块")
@allure.story("登录接口")
@pytest.mark.parametrize(
    "case",
    cases,
    ids = [case["name"] for case in cases]
)
@allure.title("{case[name]}")
def test_login(client, case):
    # 登录接口必须使用匿名客户端，避免请求前预置 token。

    with allure.step("发送登录请求"):
        res = client.post(api["login"], json=case["body"]).json()

    # with allure.step("打印请求和响应"):
    #     print("请求：", case["body"])
    #     print("响应：", res)

    with allure.step("请求信息"):
        allure.attach(
            json.dumps(case["body"], ensure_ascii=False, indent=2),
            "请求参数",
            allure.attachment_type.JSON
        )

    with allure.step("响应信息"):
        allure.attach(
            json.dumps(res, ensure_ascii=False, indent=2),
            "响应结果",
            allure.attachment_type.JSON
        )

    with allure.step("断言code"):
        assert res.get("code") == case["expect"]["code"], f"实际返回: {res}"

    if case["expect"].get("has_token"):
        token = res.get("token") or res.get("data", {}).get("token")
        assert token, f"token不存在或为空: {res}"