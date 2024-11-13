from setuptools import setup, find_packages

setup(
    name="hexaa_business_scraper",
    version="0.1.3",
    description="A web scraping library and API for Google Maps",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Dilawaiz Khan",
    author_email="dilawaizkhan08@gmail.com",
    url="https://github.com/dilawaizkhan08/Google_Maps_Scraper.git",  # Replace with your GitHub repo URL
    packages=find_packages(),
    install_requires=[
        "flask",
        "flask_cors",
        "playwright",
        "pandas"
    ],
    entry_points={
        'console_scripts': [
            'hexaa_business_scraper=main:main',
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
