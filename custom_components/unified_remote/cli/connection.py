"Handle with connection and requests"
import re
from json import dumps
from uuid import uuid4
from hashlib import sha256

from requests import Session


class Connection:
    """Handle with target connection, in this case, with Unified Remote host client."""

    def __init__(self):
        self.__url = ""
        self.__source_guid = ""
        self.__headers = ""
        # Creating a persistent http session
        self.__session = Session()

        self.web_user = ""
        self.web_password = ""

    def __del__(self):
        self.__session.close()

    def connect(self, host, port):
        "Establish connection with host client."

        self.__url = f"http://{host}:{port}/client/"
        assert self.__validate_url(), AssertionError("Malformed URL")
        self.__set_headers()
        self.__gen_guid()
        self.__autenticate()

    def __gen_guid(self):
        """Generates an unique id to perform requests.\n
        That one is can differ from the connection id provided by \"__set_headers()\" function."""

        self.__source_guid = f"web-{uuid4()}"

    def __validate_url(self):
        """Uses a regex from some StackOverflow hole for URL validating."""

        regex = re.compile(
            r"^(?:http|ftp)s?://"  # http:// or https://
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # domain...
            r"localhost|"  # localhost...
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
            r"(?::\d+)?"  # optional port
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )

        return re.match(regex, self.__url) is not None

    def __set_headers(self):
        """Do the first connection to fetch provided Connection ID
        and set it to request headers."""

        response = self.__session.get(self.__url + "connect")
        self.__conn_id  = response.json()["id"] # Session later
        headers = {"UR-Connection-ID": self.__conn_id}
        self.__headers = headers

    def __encrypt_sha256(self, hash_str):
        sha_sign = sha256(hash_str.encode()).hexdigest()
        return sha_sign

    def __autenticate(self):
        "Do some server authentication to make connection persistent and stable."

        password = str(uuid4())
        payload = {
            "Action": 0,
            "Request": 0,
            "Version": 10,
            "Password": password,
            "Platform": "web",
            "Source": self.__source_guid,
        }
        response = self.__session.post(
            self.__url + "request", headers=self.__headers, data=dumps(payload)
        )
        pw_uuid = response.json()["Password"]

        # hash is SHA256 of PWUID + WEBPW + REQUID - Or - SHA256(user:pw)
        hash_pw = self.__encrypt_sha256(f"{pw_uuid}{self.web_password}{password}")
        #hash_pw = self.__encrypt_sha256("{self.web_user}:{self.web_password}")

        payload = {
            "Capabilities": {
                "Actions": True,
                "Sync": True,
                "Grid": True,
                "Fast": False,
                "Loading": True,
                "Encryption2": True,
            },
            "Action": 1,
            "Request": 1,
            "Password": hash_pw,
            "Source": self.__source_guid,
        }
        self.__session.post(
            self.__url + "request", headers=self.__headers, data=dumps(payload)
        )

    def exe_remote(self, remoteID, action, extras=None):
        """Executes given remote id and action using a post request.\n
        Returns request response for exception handling purpose."""

        payload = {
            "ID": remoteID,
            "Action": 7,
            "Request": 7,
            "Run": {"Name": action},
            "Source": self.__source_guid,
        }
        if extras is not None:
            payload["Run"]["Extras"] = extras

        return self.__session.post(
            self.__url + "request", headers=self.__headers, data=dumps(payload)
        )

    def get_headers(self):
        return self.__headers

    def get_url(self):
        return self.__url
