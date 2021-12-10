import setuptools

with open("README.md", "r") as rm:
    long_description = rm.read()
    
setuptools.setup(
    name="covid-dashboard-noconnor",
    version="0.1",
    author="Nick O'Connor",
    author_email="no294@exeter.ac.uk",
    description="A dashboard listing details and news about COVID-19 in the UK",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/nickoc294/UKCOVIDDashboard.git",
    packages=setuptools.find_packages(),
    classifiers=[
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    ],
    python_requires='>=3.9',
    )
