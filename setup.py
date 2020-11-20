import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="nauron",
    version="0.0.1",
    author="University of Tartu",
    author_email="ping@tartunlp.ai",
    description="Python library for deploying scalable NLP web services.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/TartuNLP/nauron",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Framework :: Flask"
    ],
    license='GPLv3',
    install_requires=[
        'pika>=1.1.0',
        'flask>=1.1.2',
        'flask-restful>=0.3.8',
        'flask-cors>=3.0.9',
        'dataclasses>=0.7; python_version < "3.7.0"'
    ]
)