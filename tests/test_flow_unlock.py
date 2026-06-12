import allure
import json
import pytest
from common.read_yaml import load_yaml

api = load_yaml("config/api.yaml")

# 固定设备/账号参数，不随用例变化
OPEN_ID = "oTa_P5dkROw9m8lP4ol-WxD6Natg"    # TODO: 填入实际值
DEVICE_ID = "17763979615604702830"  # TODO: 填入实际值
APP_ID = "wxa746fd1d5e30d98b"     # TODO: 填入实际值

SEARCH_BODY = {
    "sysId": "CB2Q3EWLFCQ92V9B",
    "reqData": {
        "pageNum": 1,
        "pageSize": 50,
        "search": ""
    },
    "appWebFlag": "5"
}


def _build_unlock_body(item):
    buy_id = item["buyId"]
    return {
        "sysId": "CB2Q3EWLFCQ92V9B",
        "reqData": {
            "openId": OPEN_ID,
            "deviceId": DEVICE_ID,
            "appId": APP_ID,
            "notifyUrl": "https://test.caimuwang.com/api",
            "serviceName": item["goodsName"],
            "orderModule": "01",
            "orderType": "01",
            "payType": "0",
            "totalAmount": 0,
            "payAmount": 0,
            "pendingAmount": 0,
            "thirdPayType": 22,
            "thirdPayment": "weChat",
            "currency": "元",
            "relationId": buy_id,
            "relationType": "buy",
            "remark": "1",
            "extra": {
                "relationId": buy_id,
                "relationType": "buy",
                "ticketType": "0",
                "useCount": 1
            },
            "attach": json.dumps({"id": buy_id}, separators=(',', ':'))
        },
        "appWebFlag": "5"
    }


@allure.feature("订单模块")
@allure.story("业务流：查询-解锁-校验")

@allure.title("正常流程：查询→解锁→状态校验")
def test_flow_unlock(auth_client):
    # 该业务流会连续调用搜索和解锁接口，统一复用已登录客户端。

    # Step 1: 查询列表，取第一条 status="0" 的数据
    with allure.step("Step1 查询求购列表，获取 status=0 的数据"):
        search_res = auth_client.post(api["search"], json=SEARCH_BODY).json()
        allure.attach(
            json.dumps(search_res, ensure_ascii=False, indent=2),
            "查询响应",
            allure.attachment_type.JSON
        )
        assert search_res.get("code") == 200, f"查询失败: {search_res}"

        items = search_res["data"]["list"]
        target = next((i for i in items if i.get("status") == "0"), None)
        if target is None:
            pytest.skip("列表中未找到 status=0 的前置数据，无法执行正常解锁流程")

        buy_id = target["buyId"]
        allure.attach(
            json.dumps(target, ensure_ascii=False, indent=2),
            f"待解锁数据 buyId={buy_id}",
            allure.attachment_type.JSON
        )

    # Step 2: 解锁订单
    with allure.step(f"Step2 解锁订单 buyId={buy_id}"):
        unlock_body = _build_unlock_body(target)
        unlock_res = auth_client.post(api["unlock"], json=unlock_body).json()
        allure.attach(
            json.dumps(unlock_body, ensure_ascii=False, indent=2),
            "解锁请求参数",
            allure.attachment_type.JSON
        )
        allure.attach(
            json.dumps(unlock_res, ensure_ascii=False, indent=2),
            "解锁响应",
            allure.attachment_type.JSON
        )
        if unlock_res.get("code") == 600 and unlock_res.get("msg") == "次数已用完":
            pytest.skip("测试账号解锁次数已用完，无法验证正常解锁流程")

        assert unlock_res.get("code") == 200, \
            f"期望code=200(操作成功)，实际返回: {unlock_res}"

    # Step 3: 重新查询，校验 status 已不为 "0"
    with allure.step(f"Step3 重新查询，校验 buyId={buy_id} 的 status 已变化"):
        verify_res = auth_client.post(api["search"], json=SEARCH_BODY).json()
        allure.attach(
            json.dumps(verify_res, ensure_ascii=False, indent=2),
            "重新查询响应",
            allure.attachment_type.JSON
        )
        assert verify_res.get("code") == 200, f"重新查询失败: {verify_res}"

        new_items = verify_res["data"]["list"]
        found = next((i for i in new_items if i.get("buyId") == buy_id), None)
        allure.attach(
            json.dumps(new_items, ensure_ascii=False, indent=2),
            "重新查询结果",
            allure.attachment_type.JSON
        )

        # 若该条目仍在列表中，断言 status 已变化；若已不在列表中，视为解锁成功
        if found:
            assert found.get("status") != "0", (
                f"buyId={buy_id} 解锁后 status 仍为 '0'，实际值: {found.get('status')}"
            )
@allure.title("已解锁场景：重复解锁返回已解锁提示")
def test_already_unlocked(auth_client):
    # 重复解锁场景同样依赖搜索和解锁接口的登录态。

    #取列表中status为1的数据
    with allure.step("Step1 查询求购列表，获取 status=1 的数据"):
        search_res = auth_client.post(api["search"], json=SEARCH_BODY).json()
        allure.attach(
            json.dumps(search_res, ensure_ascii=False, indent=2),
            "查询响应",
            allure.attachment_type.JSON
        )
        assert search_res.get("code") == 200, f"查询失败: {search_res}"
        items = search_res["data"]["list"]
        target = next((i for i in items if i.get("status") == "1"), None)

        if target is None:
            pytest.skip("列表中未找到 status=1 的前置数据，无法验证重复解锁场景")

        buy_id = target["buyId"]
        allure.attach(
            json.dumps(target, ensure_ascii=False, indent=2),
            f"已经解锁数据 buyId={buy_id}",
            allure.attachment_type.JSON
        )

        # Step 2: 再次解锁已解锁的订单
    with allure.step(f"Step2 再次解锁已解锁订单 buyId={buy_id}"):
        already_unlock_body = _build_unlock_body(target)
        already_unlock_res = auth_client.post(api["unlock"], json=already_unlock_body).json()
        allure.attach(
            json.dumps(already_unlock_body, ensure_ascii=False, indent=2),
            "解锁请求参数",
            allure.attachment_type.JSON
        )
        allure.attach(
            json.dumps(already_unlock_res, ensure_ascii=False, indent=2),
            "解锁响应",
            allure.attachment_type.JSON
        )
        assert already_unlock_res.get("code") == 600, \
            f"期望code=600(已解锁)，实际返回: {already_unlock_res}"
