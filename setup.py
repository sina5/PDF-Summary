import sys
from setuptools import setup, find_packages

with open('requirements.txt') as f:
    INSTALL_REQUIRES = [l.strip() for l in f.readlines() if l]


try:
    import pytextrank
except ImportError:
    print('pytextrank is required during installation')
    sys.exit(1)

try:
    import tqdm
except ImportError:
    print('tqdm is required during installation')
    sys.exit(1)

try:
    import spacy
except ImportError:
    print('Spacy is required during installation')
    sys.exit(1)

try:
    import scispacy
except ImportError:
    print('SciSpacy is required during installation')
    sys.exit(1)


setup(name='pdfsum',
      version='0.1.0',
      description='',
      author='Sina Fathi-Kazerooni',
      packages=find_packages(),
      install_requires=INSTALL_REQUIRES,
      author_email='sina@sinafathi.com',
      )