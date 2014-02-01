from setuptools import setup

if __name__ == '__main__':
    setup(
        name='Micromigrate',
        get_version_from_scm=True,
        description='Minimal Migration Manager for sqlite',
        packages=[
            'micromigrate',
        ],
        setup_requires=[
            'hgdistver',
        ],
    )
