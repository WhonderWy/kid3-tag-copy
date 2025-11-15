from setuptools import setup

setup(
    name="kid3-tag-copy",
    version="1.0.0",
    license="MIT",
    license_expression="MIT",
    description="Copy tags between audio files using Kid3",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    author="WhonderWy",
    url="https://github.com/WhonderWy/kid3-tag-copy",
    packages=["kid3_tag_copy"],
    scripts=["kid3-tag-copy.py"],
    install_requires=[
        "pyside6",
    ],
    extras_require={
        "system": [
            "kid3-cli",  # System-level dependency that you need to install separately
        ],
    },
    entry_points={
        "console_scripts": [
            "kid3-tag-copy = kid3_tag_copy.kid3_tag_copy:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
