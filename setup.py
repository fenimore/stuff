import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="stuff",
    version="0.0.1",
    author="Fenimore Love",
    author_email="exorable.ludos@gmail.com",
    description="A small program",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/fenimore/stuff",
    packages=setuptools.find_packages(),
    install_requires=[
        "requests",
        "attr",
        "beautifulsoup4",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
