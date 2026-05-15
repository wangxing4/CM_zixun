import allure
import copy
import json
import random
import pytest
from common.read_yaml import load_yaml

api = load_yaml("config/api.yaml")
cases = load_yaml("data/register.yaml")

SYS_ID = "CB2Q3EWLFCQ92V9B"
APP_WEB_FLAG = "5"

# 已注册的手机号（用于验证已注册场景）
REGISTERED_MOBILE = "18168313566"


def generate_mobile():
    return "13" + str(random.randint(100000000, 999999999))


def _check_user_status_body(mobile):
    return {
        "sysId": SYS_ID,
        "reqData": {"loginName": mobile},
        "appWebFlag": APP_WEB_FLAG
    }


def _sms_login_body(mobile):
    return {
        "sysId": SYS_ID,
        "reqData": {"mobile": mobile},
        "appWebFlag": APP_WEB_FLAG
    }


def _register_body(mobile, code="123456"):
    return {
        "sysId": SYS_ID,
        "reqData": {
            "loginName": mobile,
            "password": "",
            "loginType": 2,
            "code": code,
            "activityId": None,
            "activityType": None,
            "bindSourceAssociationId": None,
            "bindSourceType": None,
            "recommendId": None,
            "registerPage": "5",
            "relationId": None,
            "relationType": None
        },
        "appWebFlag": APP_WEB_FLAG
    }


# =========================================================
# 场景一：完整注册流程（新用户三步走）
# =========================================================
@allure.feature("注册模块")
@allure.story("正常注册流程")
@allure.title("新用户完整注册流程：校验手机号→发送短信→注册")
def test_flow_register_new_user(client):
    # 新用户注册流程应从匿名状态开始。
    mobile = generate_mobile()

    # Step 1: 校验手机号是否已注册
    with allure.step(f"Step1 校验手机号 {mobile} 未注册"):
        check_body = _check_user_status_body(mobile)
        check_res = client.post(api["check_user_status"], json=check_body).json()
        allure.attach(
            json.dumps(check_body, ensure_ascii=False, indent=2),
            "请求参数",
            allure.attachment_type.JSON
        )
        allure.attach(
            json.dumps(check_res, ensure_ascii=False, indent=2),
            "响应结果",
            allure.attachment_type.JSON
        )
        assert check_res.get("code") == 200, f"校验手机号接口异常: {check_res}"

    # Step 2: 发送短信验证码
    with allure.step(f"Step2 向 {mobile} 发送短信验证码"):
        sms_body = _sms_login_body(mobile)
        sms_res = client.post(api["sms_login"], json=sms_body).json()
        allure.attach(
            json.dumps(sms_body, ensure_ascii=False, indent=2),
            "请求参数",
            allure.attachment_type.JSON
        )
        allure.attach(
            json.dumps(sms_res, ensure_ascii=False, indent=2),
            "响应结果",
            allure.attachment_type.JSON
        )
        assert sms_res.get("code") == 200, f"发送短信失败: {sms_res}"

    # Step 3: 提交注册（验证码后端固定为 123456）
    with allure.step(f"Step3 提交注册 {mobile}"):
        reg_body = _register_body(mobile)
        reg_res = client.post(api["login"], json=reg_body).json()
        allure.attach(
            json.dumps(reg_body, ensure_ascii=False, indent=2),
            "请求参数",
            allure.attachment_type.JSON
        )
        allure.attach(
            json.dumps(reg_res, ensure_ascii=False, indent=2),
            "响应结果",
            allure.attachment_type.JSON
        )
        assert reg_res.get("code") == 200, f"注册失败: {reg_res}"

        token = reg_res.get("data", {}).get("token")
        assert token, f"注册成功但未返回 token: {reg_res}"


# =========================================================
# 场景二：已注册手机号重复注册
# =========================================================
@allure.feature("注册模块")
@allure.story("已注册手机号校验")
@allure.title("已注册手机号：checkUserStatus 返回已注册状态")
def test_check_already_registered(client):
    # 已注册手机号校验不应依赖预置登录态。

    with allure.step(f"校验已注册手机号 {REGISTERED_MOBILE}"):
        check_body = _check_user_status_body(REGISTERED_MOBILE)
        check_res = client.post(api["check_user_status"], json=check_body).json()
        allure.attach(
            json.dumps(check_body, ensure_ascii=False, indent=2),
            "请求参数",
            allure.attachment_type.JSON
        )
        allure.attach(
            json.dumps(check_res, ensure_ascii=False, indent=2),
            "响应结果",
            allure.attachment_type.JSON
        )
        assert check_res.get("code") == 200, f"接口异常: {check_res}"
        # 已注册用户 data 中应有标识，根据实际返回字段调整
        user_status = check_res.get("data", {})
        assert user_status, f"已注册手机号未返回用户状态信息: {check_res}"


# =========================================================
# 场景三：注册第三步参数化（异常用例）
# =========================================================
@allure.feature("注册模块")
@allure.story("注册接口参数校验")
@pytest.mark.parametrize(
    "case",
    cases,
    ids=[case["name"] for case in cases]
)
@allure.title("{case[name]}")
def test_register_params(client, case):
    # 注册参数校验需要保持匿名请求语义。

    body = copy.deepcopy(case["body"])
    if case.get("random_mobile"):
        body["reqData"]["loginName"] = generate_mobile()

    with allure.step("发送注册请求"):
        res = client.post(api["login"], json=body).json()

    with allure.step("请求信息"):
        allure.attach(
            json.dumps(body, ensure_ascii=False, indent=2),
            "请求参数",
            allure.attachment_type.JSON
        )

    with allure.step("响应信息"):
        allure.attach(
            json.dumps(res, ensure_ascii=False, indent=2),
            "响应结果",
            allure.attachment_type.JSON
        )

    with allure.step("断言 code"):
        assert res.get("code") == case["expect"]["code"], f"实际返回: {res}"

    if case["expect"].get("has_token"):
        token = res.get("data", {}).get("token")
        assert token, f"注册成功但 token 为空: {res}"
