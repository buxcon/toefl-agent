import logging

from utils import LoginUtils

logging.root.setLevel(logging.INFO)

if __name__ == "__main__":
    username = input("用户名: ")
    password = input("密码: ")
    LoginUtils.mock_login(username, password)
