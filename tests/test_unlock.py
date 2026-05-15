import pytest
import allure
import json
from common.read_yaml import load_yaml

api = load_yaml("config/api.yaml")
cases = load_yaml("data/unlock.yaml")

@allure.feature("订单模块")
@allure.story("订单解锁")
@pytest.mark.parametrize(
    "case",
    cases,
    ids=[case["name"] for case in cases]
)
@allure.title("{case[name]}")

def test_unlock(auth_client, case):
    # 解锁接口默认依赖登录态，统一复用已登录客户端。

    with allure.step("发送解锁订单请求"):
        res = auth_client.post(api["unlock"], json=case["body"]).json()

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