import os
from setuptools import setup, find_packages

setup(
    name="logguard-ai",
    version="0.2.0",
    description="Autonomous Incident Response Agent for Python applications",
    long_description=open("README.md", encoding="utf-8").read() if os.path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        "groq",
        "langgraph",
        "pydantic",
        "python-dotenv",
        "pyyaml",
        "plyer",
    ],
    entry_points={
        "console_scripts": [
            "logguard=logguard.cli:main",
        ],
    },
    python_requires=">=3.10",
)
