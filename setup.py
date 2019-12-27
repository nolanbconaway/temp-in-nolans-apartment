from setuptools import find_packages, setup

setup(
    name="app",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "Flask-Limiter==1.1.0",
        "Flask-SQLAlchemy==2.4.1",
        "Flask==1.1.1",
        "gunicorn==20.0.4",
        "psycopg2-binary==2.8.4",
        "pytz==2019.3",
    ],
    extras_require={"test": ["black==19.10b0", "pydocstyle==5.0.1", "pytest==5.3.2"]},
)
