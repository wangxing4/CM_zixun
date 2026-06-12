import json

import requests
from common.config import load_env
from utils.logger import get_logger

logger = get_logger()

SENSITIVE_KEYS = {"token", "password", "mobile", "loginname", "openid", "deviceid"}


def _mask_value(key, value):
    key = key.lower()
    if value is None:
        return value

    if key in {"token", "password"}:
        return "***"

    if key in SENSITIVE_KEYS:
        value = str(value)
        if len(value) <= 7:
            return "***"
        return f"{value[:3]}***{value[-4:]}"

    return value


def _sanitize(data):
    if isinstance(data, dict):
        return {key: _mask_value(key, _sanitize(value)) for key, value in data.items()}
    if isinstance(data, list):
        return [_sanitize(item) for item in data]
    return data


def _format_log(data, limit=1000):
    try:
        text = json.dumps(_sanitize(data), ensure_ascii=False)
    except TypeError:
        text = str(_sanitize(data))
    return text[:limit]


class HttpClient:

    def __init__(self, env="test", timeout=10):
        # 环境配置
        env_config = load_env(env)

        self.base_url = env_config["base_url"]
        self.session = requests.Session()
        self.timeout = timeout

        self.token = None  # token缓存
        self.last_exchange = None

    # 仅在 fixture 或需要显式鉴权的测试中调用登录。
    def login(self, login_name="18168313566", password="123456"):
        url = self.base_url + "/tenantadmin/user/login"

        payload = {
            "sysId": "CB2Q3EWLFCQ92V9B",
            "reqData": {
                "loginName": login_name,
                "password": password,
                "loginType": 1
            },
            "appWebFlag": "5"
        }

        logger.info(f"[LOGIN] url={url}")
        logger.info(f"[LOGIN] payload={_format_log(payload)}")
        self.last_exchange = {
            "method": "POST",
            "url": url,
            "headers": {},
            "json": _sanitize(payload),
        }

        try:
            response = self.session.post(
                url=url,
                json=payload,
                timeout=self.timeout
            )

            res = response.json()

            logger.info(f"[LOGIN] status_code={response.status_code}")
            logger.info(f"[LOGIN] response={_format_log(res)}")
            self.last_exchange["response"] = {
                "status_code": response.status_code,
                "body": _sanitize(res),
            }

            if res.get("code") != 200:
                logger.error(f"[LOGIN] failed: {res}")
                raise Exception("登录失败")

            token = res["data"]["token"]
            self.set_token(token)

            logger.info("[LOGIN] token获取成功")
            return token

        except Exception as e:
            logger.error(f"[LOGIN] exception: {e}")
            if self.last_exchange is not None:
                self.last_exchange["error"] = str(e)
            raise

    # 统一维护 token 和 session headers，避免多处手写。
    def set_token(self, token):
        self.token = token
        self.session.headers.update({"token": token})

    # HttpClient 只负责发请求，不再隐式触发登录。
    def request(self, method, url, **kwargs):
        headers = kwargs.get("headers", {}).copy()

        if self.token:
            headers["token"] = self.token
        kwargs["headers"] = headers

        real_url = self.base_url + url

        logger.info(f"[{method}] url={real_url}")
        logger.info(f"[{method}] headers={_format_log(headers)}")
        logger.info(f"[{method}] params={_format_log(kwargs.get('params'))}")
        logger.info(f"[{method}] json={_format_log(kwargs.get('json'))}")
        logger.info(f"[{method}] data={_format_log(kwargs.get('data'))}")

        self.last_exchange = {
            "method": method,
            "url": real_url,
            "headers": _sanitize(headers),
            "params": _sanitize(kwargs.get("params")),
            "json": _sanitize(kwargs.get("json")),
            "data": _sanitize(kwargs.get("data")),
        }

        try:
            response = self.session.request(
                method=method,
                url=real_url,
                timeout=self.timeout,
                **kwargs
            )

            logger.info(f"[{method}] status_code={response.status_code}")
            try:
                response_body = response.json()
            except ValueError:
                response_body = response.text[:1000]

            logger.info(f"[{method}] response={_format_log(response_body)}")
            self.last_exchange["response"] = {
                "status_code": response.status_code,
                "body": _sanitize(response_body),
            }

            return response

        except requests.exceptions.RequestException as e:
            logger.error(f"[{method}] request failed: {e}")
            logger.error(f"[{method}] url={real_url}")
            if self.last_exchange is not None:
                self.last_exchange["error"] = str(e)
            raise

    # =========================
    # 对外方法
    # =========================
    def post(self, url, **kwargs):
        return self.request("POST", url, **kwargs)

    def get(self, url, **kwargs):
        return self.request("GET", url, **kwargs)
