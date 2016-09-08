# -*- coding: utf-8 -*-

import pkg_resources

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'sphinx.ext.intersphinx',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix of source filenames.
source_suffix = '.rst'

# The encoding of source files.
# source_encoding = 'utf-8-sig'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = u'Micromigrate'
copyright = u'2014-*, Ronny Pfannschmidt'

# The full version, including alpha/beta/rc tags.
release = pkg_resources.get_distribution("Micromigrate").version
version = '.'.join(release.split('.')[:2])

exclude_patterns = []

pygments_style = 'sphinx'
html_theme = 'haiku'
html_static_path = ['_static']

intersphinx_mapping = {'http://docs.python.org/': None}
