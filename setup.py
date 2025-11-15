from setuptools import setup

setup(
    name="kid3-tag-copy",
    version="1.0",
    py_modules=["kid3_tag_copy"],
    install_requires=["PySide6"],
    entry_points={
        "console_scripts": [
            "kid3-tag-copier=kid3_tag_copy:main",
        ],
    },
)
