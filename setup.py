from setuptools import setup, find_packages


setup(
    name='app-validator',
    version='1.0',
    description='Validates open web apps.',
    long_description=open('README.rst').read(),
    author='Matt Basta',
    author_email='me@mattbasta.com',
    url='http://github.com/mattbasta/app-validator',
    license='BSD',
    packages=find_packages(exclude=['tests',
                                    'tests/*',
                                    'extras',
                                    'extras/*']),
    include_package_data=True,
    zip_safe=False,
    install_requires=[p.strip() for p in open('./requirements.txt')
                                              if not p.startswith(('#',
                                                                   '-e'))],
    scripts=["app-validator"],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
