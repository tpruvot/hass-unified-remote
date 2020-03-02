"Define and parse remote definitions"
from custom_components.unified_remote.cli.yaml_parser import yaml_load


class Remotes:
    def __init__(self, yaml_path="remotes.yml"):
        yaml_data = yaml_load(yaml_path)
        self.__types = None
        self.__remotes = None
        if yaml_data is None:
            raise FileNotFoundError()
        else:
            self.__types = self.__type_parser(yaml_data)
            self.__remotes = self.__remote_parser(yaml_data)

    def __type_parser(self, yaml_data: dict):
        types = yaml_data.get("types")
        if types is None:
            types = dict()
        return types

    def __remote_validator(self, remote: dict):
        assert "id" in remote.keys()
        assert "type" in remote.keys() or remote["controls"] != []

    def get_remote(self, name):
        return self.__remotes.get(name)

    def __append_remote_type(self, remotes):
        if remotes is None:
            raise Exception(
                "None remotes was parsed, please check your remotes.yml file"
            )
        for name, remote in remotes.items():
            if "controls" not in remote.keys():
                remote["controls"] = list()
            remote_type = remote.get("type")
            if remote_type is not None:
                type_params = self.__types.get(remote_type)
                if type_params is not None:
                    type_controls = type_params.get("controls")
                    if type_controls is not None:
                        for control in type_controls:
                            remote["controls"].append(control)
            try:
                self.__remote_validator(remote)
            except AssertionError:
                raise AssertionError(f'Invalid parsing for remote "{name}"')

    def __remote_parser(self, yaml_data: dict):
        yaml_remotes = yaml_data.get("remotes")
        self.__append_remote_type(yaml_remotes)
        return yaml_remotes
