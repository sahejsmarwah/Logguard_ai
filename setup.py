from setuptools import setup, find_packages

setup(
    name="logguard-ai",
    version="0.1.0",
    description="Autonomous Incident Response Agent",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "langchain",
        "langchain-openai",
        "langgraph",
        "pydantic",
        "python-dotenv",
        "groq"
    ],
    entry_points={
        "console_scripts": [
            "logguard=logguard.guard:run_guard",
        ],
    },
    python_requires=">=3.8",
)
