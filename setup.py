import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()


def read_requirements(file):
    with open(file, "r") as f:
        return f.read().split()


install_requires = read_requirements("requirements.txt")
test_require = read_requirements("requirements-test.txt")
extras = {
    'test': test_require
}

setuptools.setup(
    name="krbticket",
    use_scm_version=True,
    author="Kazuhiro Suzuki",
    author_email="ksauzzmsg@gmail.com",
    description="Kerberos Ticket Manager",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ksauzz/krbticket",
    packages=setuptools.find_packages(),
    setup_requires=['setuptools_scm'],
    install_requires=install_requires,
    tests_require=test_require,
    extras_require=extras,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX",
    ],
)
