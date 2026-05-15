import pytest
import allure
import json
from common.read_yaml import load_yaml

api = load_yaml("config/api.yaml")
cases = load_yaml("data/search.yaml")


@allure.feature("首页搜索")
@allure.story("搜索接口")
@pytest.mark.parametrize(
    "case",
    cases,
    ids = [case["name"] for case in cases]
)
@allure.title("{case[name]}")


def test_search(auth_client, case):
    # 搜索接口默认依赖登录态，统一复用已登录客户端。

    with allure.step("发送搜索请求"):
        res = auth_client.post(api["search"], json=case["body"]).json()

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