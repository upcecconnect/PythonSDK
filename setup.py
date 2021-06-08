import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(
    name='upcpayment',  
    version='0.5.5.7.8.3',
    author="Valentyn Ishchenko",
    author_email="xalikxalik44@gmail.com",
    description="Library for upc services",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/upcecconnect/PythonSDK",
    package_dir={"": "upcpayment"},
    packages=setuptools.find_packages(where="upcpayment"),
    python_requires=">=3.7",
    install_requires=['pyOpenSSL', 'signxml'],
    classifiers=[
         "Programming Language :: Python :: 3",
         "Programming Language :: Python :: 3.7",
         "License :: OSI Approved :: MIT License",
         "Operating System :: OS Independent",
    ],
 )