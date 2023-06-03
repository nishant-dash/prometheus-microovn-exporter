"""Configuration loader."""
import sys
from collections import OrderedDict
from logging import getLogger
from typing import Any, Dict, Union

import confuse


class ConfigMeta(type):
    """Singleton metaclass for the Config."""

    _instance = None

    def __new__(cls, *args: Any, **kwargs: Any) -> type:  # pylint: disable=C0204
        if not cls._instance:
            cls._instance = super(ConfigMeta, cls).__new__(cls, *args, **kwargs)
            cls._instance.config = confuse.Configuration("PrometheusMicroovnExporter", __name__)
        return cls._instance


class Config(metaclass=ConfigMeta):
    """Configuration class for PrometheusMicroovnExporter."""

    config: confuse.Configuration = None

    def __init__(self, args: Union[Dict, None] = None) -> None:
        """Initialize the config class."""
        if not self.config:
            self.config = confuse.Configuration("PrometheusMicroovnExporter", __name__)

        self.logger = getLogger(__name__)

        if args:
            self.config.set_args(args, dots=True)

        self.validate_config_options()

    def validate_config_options(self) -> None:
        """Validate the configuration values against a template."""
        template = {
            "exporter": OrderedDict(
                [
                    ("port", confuse.Choice(range(0, 65536), default=9999)),
                    ("collect_interval", int),
                ]
            ),
            "microovn_cluster": OrderedDict([("path", str),]),
            # "microovn_services": OrderedDict(
            #     [
            #         ("path", str),
            #         ("central", str),
            #         ("chassis", str),
            #         ("switch", str),
            #         ("daemon", str),
            #     ]
            # ),
            "microovn_certs": OrderedDict(
                [
                    ("server", str),
                    ("cluster", str),
                ]
            ),
            "ovn_cluster": OrderedDict([("path", str),]),
            "ovn_certs": OrderedDict(
                [
                    ("server", str),
                    ("cluster", str),
                ]
            ),
            # "mode": confuse.Choice(("microovn", "ovn"), default="microovn"),
            "mode": str, 
            "debug": bool,
        }

        try:
            self.config.get(template)
            self.config["mode"].as_choice(["microovn", "ovn"])
            self.config["microovn_cluster"]['path'].as_filename()
            self.config["ovn_cluster"]['path'].as_filename()
            self.logger.info("Configuration parsed successfully")
        except (
            KeyError,
            confuse.ConfigTypeError,
            confuse.ConfigValueError,
            confuse.NotFoundError,
        ) as err:
            self.logger.error("Error parsing configuration values: %s", err)
            sys.exit(1)

    def get_config(self, section: Union[Dict, None] = None) -> confuse.Configuration:
        """Return the config."""
        if section:
            return self.config[section]

        return self.config
