"""
Choy News Bot - Setup script for package installation.
"""

from setuptools import setup, find_packages

setup(
    name="choynews",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "python-dotenv",
        "feedparser",
        "pytz",
        "requests",
        "python-telegram-bot",
        "numpy",
        "timezonefinder",
        "sgmllib3k"
    ],
    author="Shanchoy Noor",
    author_email="shanchoyzone@gmail.com",
    description="A Telegram bot that provides daily news, cryptocurrency market data, and weather information",
    keywords="news, telegram, bot, cryptocurrency, weather",
    python_requires=">=3.6",
    scripts=[
        "bin/choynews",
        "bin/utils/update_coinlist.py"
    ],
    entry_points={
        "console_scripts": [
            "choynews=bin.choynews:main"
        ]
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Communications :: Chat",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content :: News/Diary",
    ],
    include_package_data=True,
    zip_safe=False,
    project_urls={
        "Documentation": "https://github.com/username/choynews/docs",
        "Source": "https://github.com/username/choynews",
        "Tracker": "https://github.com/username/choynews/issues",
    },
)
