import logging

from utils import LoginUtils

logging.root.setLevel(logging.INFO)

if __name__ == "__main__":
    username = input("用户名: ")
    password = input("密码: ")
    LoginUtils.mock_login(username, password)
    # LoginUtils.mock_login("21328572", "Arey0umyxi0ngdi?")