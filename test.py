from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

from utils import LoginUtils


class TestCase(object):
    @staticmethod
    def login_test(options):
        driver = webdriver.Remote(command_executor="http://127.0.0.1:4444/wd/hub", options=options)

        username = input("用户名: ")
        password = input("密码: ")
        cookies = LoginUtils.mock_login(driver, username, password)

        driver.quit()
        return cookies

    @staticmethod
    def keep_online_test(options, cookies):
        driver = webdriver.Remote(command_executor="http://127.0.0.1:4444/wd/hub", options=options)

        driver.get("https://toefl.neea.cn/myHome/21328572/index")
        for cookie in cookies:
            driver.add_cookie(cookie)
        driver.get("https://toefl.neea.cn/myHome/21328572/index")

        wait = WebDriverWait(driver, 10)
        info = wait.until(ec.presence_of_element_located((By.CLASS_NAME, "span9"))).text

        driver.quit()
        return info
