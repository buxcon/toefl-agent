import time
import logging
import requests

from Crypto.Cipher import AES
from Crypto.Hash import MD5

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

from fateadm_api import CaptchaPredictionApi


class LoginUtils(object):
    @staticmethod
    def pkcs7_padding(message):
        stuffing = 16 - len(message) % 16
        return message + chr(stuffing) * stuffing

    @staticmethod
    def encrypt_password(password, captcha, iv):
        key = ("0123456789AB" + captcha.upper()).encode("UTF-8")
        padded_secret = LoginUtils.pkcs7_padding(MD5.new(password.encode("UTF-8")).hexdigest())

        cipher = AES.new(key, AES.MODE_CBC, iv.encode("UTF-8"))
        return cipher.encrypt(padded_secret).hex()

    @staticmethod
    def try_extract_iv(driver, max_retry_times=10):
        for i in range(max_retry_times + 1):
            iv = driver.find_element_by_id("ivstr").get_attribute("value")
            if iv is not None and iv != "":
                return iv
            time.sleep(1)

        return None

    @staticmethod
    def try_extract_captcha_image_url(driver, max_retry_times=10):
        for i in range(max_retry_times + 1):
            url = driver.find_element_by_id("chkImg").get_attribute("src")
            if "loading" not in url:
                return url
            time.sleep(1)

        return None

    @staticmethod
    def mock_login(username, password):
        firefox_options = webdriver.FirefoxOptions()
        firefox_options.headless = True
        driver = webdriver.Remote(command_executor="http://127.0.0.1:4444/wd/hub", options=firefox_options)

        driver.get("https://toefl.neea.cn/login")
        wait = WebDriverWait(driver, 10)
        csrf_token = wait.until(ec.presence_of_element_located((By.NAME, "CSRFToken"))).get_attribute("value")
        iv = LoginUtils.try_extract_iv(driver)
        if iv is None:
            logging.error("[登录页加载失败]")
            exit(-1)
        logging.info("[登录页加载完成] 跨站请求凭据=%s, AES初始向量=%s" % (csrf_token, iv))

        driver.find_element_by_id("verifyCode").click()
        captcha_image_url = LoginUtils.try_extract_captcha_image_url(driver)
        if captcha_image_url is None:
            logging.error("[验证码加载失败]")
            exit(-1)
        logging.info("[取得验证码图片链接] %s" % captcha_image_url)

        captcha_image = requests.get(captcha_image_url).content
        captcha_prediction = CaptchaUtils.predict(captcha_image)
        logging.info("[验证码识别预测结果] %s" % captcha_prediction)

        driver.find_element_by_id("userName").send_keys(username)
        driver.find_element_by_id("textPassword").send_keys(password)
        driver.find_element_by_id("verifyCode").send_keys(captcha_prediction)
        logging.info(
            "[登录表单] username=%s, password=%s, captcha=%s, csrf_token=%s"
            % (username, LoginUtils.encrypt_password(password, captcha_prediction, iv), captcha_prediction, csrf_token)
        )
        driver.find_element_by_id("btnLogin").click()

        name = wait.until(ec.presence_of_element_located((By.CLASS_NAME, "span9"))).text
        print(name)

        cookies = driver.get_cookies()
        driver.quit()

        return cookies


class CaptchaUtils(object):
    FF_APP_ID = "328168"
    FF_APP_KEY = "ftWRyMKcHSDaQcHW466qzOKtyce0qZh5"
    FF_PD_ID = "128168"
    FF_PD_KEY = "Q0cdEbFQASdThQvrJzHCkMbaWUgQNqBi"

    @staticmethod
    def predict(captcha_image):
        prediction_api = CaptchaPredictionApi(
            CaptchaUtils.FF_APP_ID, CaptchaUtils.FF_APP_KEY, CaptchaUtils.FF_PD_ID, CaptchaUtils.FF_PD_KEY
        )
        return prediction_api.simple_predict("20400", captcha_image)
