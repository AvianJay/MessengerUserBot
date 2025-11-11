from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="messenger-userbot",
    version="1.0.0",
    author="AvianJay",
    description="A Python library for creating Messenger bots using Selenium",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/AvianJay/MessengerUserBot",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "selenium",
        "webdriver-manager",
        "requests",
    ],
    extras_require={
        "server": ["flask"],
        "ai": ["g4f"],
        "image": ["Pillow"],
    },
)
