from setuptools import setup, find_packages

setup(
    name="rag_agent",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pydantic-ai>=0.1.8",
        "openai>=1.15.0",
        "asyncpg>=0.29.0",
        "httpx>=0.27.0",
        "pymupdf>=1.24.0",
        "numpy>=1.26.0",
        "streamlit>=1.32.0",
        "python-dotenv>=1.0.0",
        "psycopg2-binary>=2.9.9",
        "pgvector>=0.2.4",
        "pydantic>=2.5.0",
        "pytest>=7.4.0",
        "requests>=2.31.0",
    ],
    python_requires=">=3.10",
) 