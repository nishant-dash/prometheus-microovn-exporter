"""Set up prometheus_juju_exporter python module cli scripts."""

from setuptools import setup

with open("README.md", encoding="utf-8") as f:
    readme = f.read()

with open("LICENSE", encoding="utf-8") as f:
    project_license = f.read()

setup(
    name="prometheus_microovn_exporter",
    use_scm_version={"local_scheme": "node-and-date"},
    description="collects and exports microovn service status and metrics",
    long_description=readme,
    author="Nishant Dash",
    url="https://github.com",
    license=project_license,
    packages=["prometheus_microovn_exporter"],
    package_data={"prometheus_microovn_exporter": ["config_default.yaml"]},
    entry_points={
        "console_scripts": [
            "prometheus-microovn-exporter=prometheus_microovn_exporter.cli:main",
        ]
    },
    setup_requires=["setuptools_scm"],
)
