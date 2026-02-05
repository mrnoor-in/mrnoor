from setuptools import setup

setup(
    name="mrnoor",
    version="1.0.0",
    py_modules=["mrnoor"],
    install_requires=["requests"],
    entry_points={
        "console_scripts": [
            "mrnoor=mrnoor:main"
        ]
    },
    author="Mr Noor",
    description="Live age calculator & social media username/stats checker",
    url="https://mrnoor.in",
    license="MIT",
)
