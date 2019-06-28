import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="django-socksync",
    version="0.0.1",
    author="Forrest Jones",
    author_email="fjones-dev@8bitforest.com",
    description="Easily bind django model data with a websocket client.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/osum4est/django-socksync",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
