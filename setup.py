from setuptools import find_packages, setup

setup(
    name="django-common-utils",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "common": [
            "templates/*.html",
            "static/*",
            "static/**/*",
        ],
    },
)
