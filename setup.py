from setuptools import setup, find_packages

setup(
    name="crypto_twitter_bot",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "python-dotenv==1.0.0",
        "anthropic==0.8.1",
        "openai==1.3.7",
        "requests==2.31.0",
        "ccxt==4.1.13",
        "schedule==1.2.1",
        "tweepy==4.14.0",
        "websockets==11.0.3",
        "loguru==0.7.2"
    ],
    python_requires=">=3.8",
) 