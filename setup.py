from setuptools import setup

setup(
    name="kid3-tag-copier",
    version="1.0",
    py_modules=["kid3_tag_copier"],
    install_requires=["PySide6"],
    entry_points={
        "console_scripts": [
            "kid3-tag-copier=kid3_tag_copier:main",
        ],
    },
)
