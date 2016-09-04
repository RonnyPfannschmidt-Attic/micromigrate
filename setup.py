from setuptools import setup
setup(
    name='Micromigrate',
    get_version_from_scm=True,
    description='Minimal Migration Manager for sqlite',
    packages=[
        'micromigrate',
    ],
    setup_requires=[
        'setuptools_scm',
    ],
    extras_require={
        'inprocess': ['sqlparse'],
    },
)
