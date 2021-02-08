import logging

from selenium import webdriver

from test import TestCase


logging.root.setLevel(logging.INFO)

if __name__ == "__main__":
    firefox_options = webdriver.FirefoxOptions()
    firefox_options.headless = True

    cookies = TestCase.login_test(firefox_options)
    info = TestCase.keep_online_test(firefox_options, cookies)

    print(info)
