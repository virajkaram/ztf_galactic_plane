import setuptools

setuptools.setup(

    name="ztf_galactic_plane",
    version="0.0.1",
    author="Viraj Karambelkar",
    long_description_content_type="text/markdown",
    license="MIT",
    packages=setuptools.find_packages(),
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires='>=3.7',
    install_requires=[
        "pathlib",
        "pandas",
        "astropy",
        "penquins @ git+https://github.com/virajkaram/penquins.git@skymap_queries ",
        "matplotlib",
        "requests",
    ],
    package_data={
    }
)

