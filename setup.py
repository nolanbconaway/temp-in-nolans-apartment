from setuptools import find_packages, setup

setup(
    name="app",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "click==8.1.3",
        "commonmark==0.9.1",
        "Deprecated==1.2.13",
        "Flask==2.2.5",
        "Flask-Limiter==2.6.3",
        "Flask-SQLAlchemy==2.5.1",
        "gevent==21.12.0",
        "greenlet==1.1.3",
        "importlib-metadata==4.12.0",
        "itsdangerous==2.1.2",
        "Jinja2==3.1.2",
        "limits==2.7.0",
        "MarkupSafe==2.1.1",
        "packaging==21.3",
        "psycopg2-binary==2.9.3",
        "Pygments==2.13.0",
        "pymemcache==3.5.2",
        "pyparsing==3.0.9",
        "pytz==2022.2.1",
        "rich==12.5.1",
        "sqlalchemy==1.4.41",
        "typing-extensions==4.3.0",
        "Werkzeug==2.2.3",
        "wrapt==1.14.1",
        "zipp==3.8.1",
        "zope.event==4.5.0",
        "zope.interface==5.4.0",
    ],
    extras_require={"test": ["black==22.8.0", "pytest==7.1.3"]},
)
