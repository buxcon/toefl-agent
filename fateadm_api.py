import hashlib
import time
import json
import requests
import logging

logging.root.setLevel(logging.DEBUG)

ENABLE_LOGGING = False
BASE_URL = "http://pred.fateadm.com"


class Empty(object):
    def __init__(self):
        self.value = None


class Response(object):
    def __init__(self):
        self.ret_code = -1
        self.remaining = 0.0
        self.message = "success"
        self.request_id = None
        self.prediction = Empty()

    def __str__(self):
        return "ret_code=%d, remaining=%f, message=%s, request_id=%s, prediction=%s" \
               % (self.ret_code, self.remaining, self.message, self.request_id, self.prediction)

    def parse_json_response(self, response):
        if response is None:
            self.message = "请求失败"
            return

        json_response = json.loads(response)
        self.ret_code = int(json_response["RetCode"])
        self.message = json_response["ErrMsg"]
        self.request_id = json_response["RequestId"]

        if self.ret_code == 0:
            response_data = json_response["RspData"]
            if response_data is not None and response_data != "":
                json_response_data = json.loads(response_data)
                if "cust_val" in json_response_data:
                    self.remaining = float(json_response_data["cust_val"])
                if "result" in json_response_data:
                    self.prediction.value = json_response_data["result"]


def calc_sign(pd_id, passwd, timestamp):
    md5 = hashlib.md5()
    md5.update((timestamp + passwd).encode())
    c_sign = md5.hexdigest()

    md5 = hashlib.md5()
    md5.update((pd_id + timestamp + c_sign).encode())
    c_sign = md5.hexdigest()

    return c_sign


def calc_card_sign(card_id, card_key, timestamp, passwd):
    md5 = hashlib.md5()
    md5.update(passwd + timestamp + card_id + card_key)
    return md5.hexdigest()


def predict_request(url, body, img_data=""):
    post_data = body
    files = {
        'img_data': ('img_data', img_data)
    }
    headers = {
        'User-Agent': 'Mozilla/5.0',
    }
    response_data = requests.post(url, post_data, files=files, headers=headers)

    response = Response()
    response.parse_json_response(response_data.text)

    return response


class CaptchaPredictionApi(object):
    # API接口调用类
    # 参数（appID，appKey，pdID，pdKey）
    def __init__(self, app_id, app_key, pd_id, pd_key):
        self.app_id = app_id
        if app_id is None:
            self.app_id = ""
        self.app_key = app_key
        self.pd_id = pd_id
        self.pd_key = pd_key
        self.host = BASE_URL

    def set_host(self, url):
        self.host = url

    def check_balance(self):
        t = str(int(time.time()))
        sign = calc_sign(self.pd_id, self.pd_key, t)
        param = {
            "user_id": self.pd_id,
            "timestamp": t,
            "sign": sign
        }
        url = self.host + "/api/custval"

        response = predict_request(url, param)
        if ENABLE_LOGGING:
            if response.ret_code == 0:
                logging.debug("[余额查询成功] %s" % str(response))
            else:
                logging.warning("[余额查询失败] %s" % str(response))

        return response

    def check_latency(self, pred_type):
        t = str(int(time.time()))
        sign = calc_sign(self.pd_id, self.pd_key, t)
        param = {
            "user_id": self.pd_id,
            "timestamp": t,
            "sign": sign,
            "predict_type": pred_type,
        }
        if self.app_id != "":
            a_sign = calc_sign(self.app_id, self.app_key, t)
            param["appid"] = self.app_id
            param["asign"] = a_sign
        url = self.host + "/api/qcrtt"

        response = predict_request(url, param)
        if ENABLE_LOGGING:
            if response.ret_code == 0:
                logging.debug("[延迟查询成功] %s" % str(response))
            else:
                logging.warning("[延迟查询失败] %s" % str(response))

        return response

    def refund(self, request_id):
        if request_id == "":
            return
        t = str(int(time.time()))
        sign = calc_sign(self.pd_id, self.pd_key, t)
        param = {
            "user_id": self.pd_id,
            "timestamp": t,
            "sign": sign,
            "request_id": request_id
        }
        url = self.host + "/api/capjust"

        response = predict_request(url, param)
        if ENABLE_LOGGING:
            if response.ret_code == 0:
                logging.debug("[退款成功] %s" % str(response))
            else:
                logging.warning("[退款失败] %s" % str(response))

        return response

    def recharge(self, card_id, card_key):
        t = str(int(time.time()))
        sign = calc_sign(self.pd_id, self.pd_key, t)
        c_sign = calc_card_sign(card_id, card_key, t, self.pd_key)
        param = {
            "user_id": self.pd_id,
            "timestamp": t,
            "sign": sign,
            "cardid": card_id,
            "csign": c_sign
        }
        url = self.host + "/api/charge"

        response = predict_request(url, param)
        if ENABLE_LOGGING:
            if response.ret_code == 0:
                logging.debug("[充值成功] %s" % str(response))
            else:
                logging.warning("[充值失败] %s" % str(response))

        return response

    def predict(self, prediction_type, img_data, head_info=""):
        t = str(int(time.time()))
        sign = calc_sign(self.pd_id, self.pd_key, t)
        param = {
            "user_id": self.pd_id,
            "timestamp": t,
            "sign": sign,
            "predict_type": prediction_type,
            "up_type": "mt"
        }
        if head_info is not None or head_info != "":
            param["head_info"] = head_info
        if self.app_id != "":
            a_sign = calc_sign(self.app_id, self.app_key, t)
            param["appid"] = self.app_id
            param["asign"] = a_sign
        url = self.host + "/api/capreg"
        files = img_data

        response = predict_request(url, param, files)
        if ENABLE_LOGGING:
            if response.ret_code == 0:
                logging.debug("[识别成功] %s" % str(response))
            else:
                logging.warning("[识别失败] %s" % str(response))
                if response.ret_code == 4003:
                    logging.warning("[余额不足]")

        return response

    def predict_from_file(self, prediction_type, file_name, head_info=""):
        with open(file_name, "rb") as file:
            data = file.read()
        return self.predict(prediction_type, data, head_info=head_info)

    def simple_check_balance(self):
        response = self.check_balance()
        return response.remaining

    def simple_refund(self, request_id):
        return self.refund(request_id).ret_code

    def simple_recharge(self, card_id, card_key):
        return self.recharge(card_id, card_key).ret_code

    def simple_predict(self, prediction_type, img_data, head_info=""):
        response = self.predict(prediction_type, img_data, head_info)
        return response.prediction.value

    def simple_predict_from_file(self, prediction_type, file_name, head_info=""):
        response = self.predict_from_file(prediction_type, file_name, head_info)
        return response.prediction.value


def demo():
    pd_id = "100000"
    pd_key = "123456"
    app_id = "100001"
    app_key = "123456"
    prediction_type = "30400"

    api = CaptchaPredictionApi(app_id, app_key, pd_id, pd_key)
    prediction = api.predict_from_file(prediction_type, "img.jpg")  # 返回详细识别结果
    if prediction.ret_code == 0:
        # 识别的结果如果与预期不符，可以调用这个接口将预期不符的订单退款
        # 退款仅在正常识别出结果后，无法通过网站验证的情况，请勿非法或者滥用，否则可能进行封号处理
        api.refund(prediction.request_id)
