from setuptools import setup
import re

requirements = ["requests", "aiohttp", "asyncio"]
    
readme = ''
with open("README.md", encoding="utf-8") as f:
    readme = f.read()

with open("GramDB/__init__.py", encoding="utf-8") as f:
    version = re.findall(r"__version__ = \"(.+)\"", f.read())[0]
    
setup(
    name='GramDB',
    author='ishikki-Akabane',
    author_email='ishikkiakabane@outlook.com',
    version=version,
    long_description=readme,
    long_description_content_type="text/markdown",
    url='https://github.com/ishikki-akabane/GramDB',
    download_url="https://github.com/ishikki-akabane/GramDB/releases/latest",
    license='GNU General Public License v3.0',
    classifiers=[
        "Framework :: AsyncIO",
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
        "Natural Language :: English",
        "Operating System :: OS Independent",
        'Programming Language :: Python :: 3.7',
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Build Tools",

    ],
    description='Unlimited Capacity Database For Programming Using Telegram as Database.',
    include_package_data=True,
    keywords=['telegram', 'db', 'database', 'free', 'storage', 'code'],
    install_requires=requirements
)
