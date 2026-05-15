import requests
from common.config import load_env
from utils.logger import get_logger

logger = get_logger()


class HttpClient:

    def __init__(self, env="test", timeout=10):
        # 环境配置
        env_config = load_env(env)

        self.base_url = env_config["base_url"]
        self.session = requests.Session()
        self.timeout = timeout

        self.token = None  # token缓存

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
        logger.info(f"[LOGIN] payload={payload}")

        try:
            response = self.session.post(
                url=url,
                json=payload,
                timeout=self.timeout
            )

            res = response.json()

            logger.info(f"[LOGIN] status_code={response.status_code}")
            logger.info(f"[LOGIN] response={res}")

            if res.get("code") != 200:
                logger.error(f"[LOGIN] failed: {res}")
                raise Exception("登录失败")

            token = res["data"]["token"]
            self.set_token(token)

            logger.info("[LOGIN] token获取成功")
            return token

        except Exception as e:
            logger.error(f"[LOGIN] exception: {e}")
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
        logger.info(f"[{method}] headers={headers}")
        logger.info(f"[{method}] params={kwargs.get('params')}")
        logger.info(f"[{method}] json={kwargs.get('json')}")
        logger.info(f"[{method}] data={kwargs.get('data')}")

        try:
            response = self.session.request(
                method=method,
                url=real_url,
                timeout=self.timeout,
                **kwargs
            )

            logger.info(f"[{method}] status_code={response.status_code}")
            logger.info(f"[{method}] response={response.text[:500]}")

            return response

        except requests.exceptions.RequestException as e:
            logger.error(f"[{method}] request failed: {e}")
            logger.error(f"[{method}] url={real_url}")
            raise

    # =========================
    # 对外方法
    # =========================
    def post(self, url, **kwargs):
        return self.request("POST", url, **kwargs)

    def get(self, url, **kwargs):
        return self.request("GET", url, **kwargs)