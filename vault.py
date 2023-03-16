from pathlib import Path
from typing import Any

import hvac
import yaml

from hvac.exceptions import InvalidRequest, InvalidPath

from logger import logger


class VaultMaster:
    def __init__(self, url: str, config_file: Path):
        self.url = url
        self.client = hvac.Client(url=self.url)
        if not config_file.exists():
            raise FileExistsError(f"No config file by path: {config_file}")
        self.__parse_config_file(config_file)

    def __parse_config_file(self, config_file: Path) -> None:
        with open(config_file, "r") as stream:
            try:
                self.config = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                raise AttributeError(f"Error parsing config file: {exc}")

    def start(self, root_token=None):
        """
        :param root_token: optional, if string second time
        """
        self.__start(root_token)

    def __start(self, root_token):

        if root_token:
            self.__root_token = root_token

        logger.info("Starting vault . . . .")
        logger.info(
            f'Statuses: initialized: {self.client.seal_status.get("initialized")} | sealed: {self.client.seal_status.get("sealed")}'
        )
        if not self.client.seal_status.get("initialized"):
            logger.info("Initializing")
            self.__init()
        if self.client.seal_status.get("sealed"):
            logger.info("Unsealing")
            self.__unseal()

            # enable auth methods
            auth_methods = ("approle", "userpass")
            [vault.enable_auth_method(auth_method=auth_method) for auth_method in auth_methods]  # type: ignore

        self.client = hvac.Client(url=self.url, token=self.__root_token)
        logger.info(
            f"Client authenticated (master token): {self.client.is_authenticated()}"
        )

        # set beginner settings
        kv_config: dict = self.config.get("infrastructure")
        for contour in kv_config:
            self.create_kv_area(contour)
            services = kv_config.get(contour)
            for service in services:
                service_config = services.get(service)
                self.set_kv_secret(
                    area=contour, context=f"{service}/config", data=service_config
                )

                # create polices for service access
                vault.create_policy('x', 'x')
                # vault.create_userpass(username='stepa', password='adminadminadmin')

    def __init(self) -> None:
        vault_init_data: dict[str, Any] = self.client.sys.initialize(5, 3)
        # Get vault init data
        self.__unseal_keys: list[str] = vault_init_data.get("keys", None)
        self.__root_token = vault_init_data.get("root_token", None)
        logger.info(f"root token: {self.__root_token}")
        logger.info(f"unseal keys (5): {self.__unseal_keys}")

    def __unseal(self) -> None:
        self.client.sys.submit_unseal_keys(self.__unseal_keys[0:3])
        logger.info(f'initialized: {self.client.seal_status.get("initialized")}')
        logger.info(f'sealed: {self.client.seal_status.get("sealed")}')

    def enable_auth_method(self, auth_method: str) -> None:
        try:
            method_enabled = self.client.sys.enable_auth_method(method_type=auth_method)
        except Exception as ex:
            logger.error(f"Fails when try to enable auth method {auth_method} ex: {ex}")
            return

        logger.info(f"{auth_method} enabled: {method_enabled.status_code == 204}")

    def create_kv_area(self, name: str) -> None:
        try:
            kv_v2_created = self.client.sys.enable_secrets_engine(
                "kv", path=name, options={"version": 2}
            )
        except InvalidRequest as ex:
            logger.error(f"Fails when try to create kv area: {ex}")
            return
        logger.info(f"kv_v2_created {name}: {kv_v2_created.status_code == 204}")

    def list_secrets(self, area, context=None) -> dict:
        if context is None:
            context = ""
        try:
            response = self.client.secrets.kv.v2.list_secrets(
                mount_point=area, path=context
            )
        except Exception as ex:
            logger.warn(f"Fails when try to get list: {area, context}, ex: {ex}")
            response = {}
        data = response.get("data", {})
        return data.get("keys", {})

    def read_secret(self, area, context) -> dict | None:
        try:
            response = self.client.secrets.kv.v2.read_secret_version(
                mount_point=area, path=context, raise_on_deleted_version=True
            )
        except InvalidPath as ex:
            logger.error(f"Fails when try to get a secret: {ex}")
            return None
        data = response.get("data", {})
        return data.get("data", {})

    def set_kv_secret(self, area: str, context: str, data: dict) -> None:
        self.client.secrets.kv.v2.create_or_update_secret(
            mount_point=area,
            path=context,
            secret=data,
        )
        return None

    def create_userpass(self, username: str, password: str) -> None:
        userpass_created = self.client.auth.userpass.create_or_update_user(
            username="stepa",
            password=password,
            policies=["dev_postgres"],
        )
        logger.info(
            f"userpass {username} created: {userpass_created.status_code == 204}"
        )

    def create_policy(self, area: str, service: str):
        """
        hsl alternative

        path "dev/*" {
            capabilities = ["read", "list"]
        }
        path "dev/postgres/*" {
            capabilities = ["read", "list"]
        }
        path "sys/mounts/" {
            capabilities = ["read", "list"]
        }
        """
        d = {
            "path": {
                'dev/*': {
                    'capabilities': ["read", "list"]
                },
                'dev/postgres/*': {
                    'capabilities': ["read", "list"]
                },
                'sys/mounts/': {
                    'capabilities': ["read", "list"]
                },
            }
        }

        self.client.sys.create_or_update_policy(
            name="dev_postgres",
            policy=d,
        )


if __name__ == "__main__":
    # create root-client for vault
    vault = VaultMaster(url="http://localhost:8200", config_file=Path("services.yaml"))

    # start (pass root token if already initialized else None)
    # vault.start(root_token="hvs.4euW7wnwjgAGJS5L4Tox8iaj")
    vault.start(root_token=None)

    # read secret
    secret = vault.read_secret(area="dev", context="postgres/config")
    logger.info(f"secret: {secret}")
    # list of secrets
    list_of_secrets = vault.list_secrets(area="dev", context=None)
    logger.info(f"list_of_secrets: {list_of_secrets}")
