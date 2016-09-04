from setuptools import setup
setup(
    name='Micromigrate',
    use_scm_version=True,
    description='Minimal Migration Manager for sqlite',
    packages=[
        'micromigrate',
    ],
    package_data={
        'micromigrate': ['scripts/*.sql'],
    },
    setup_requires=[
        'setuptools_scm',
    ],
    extras_require={
        'inprocess': ['sqlparse'],
    },
)
