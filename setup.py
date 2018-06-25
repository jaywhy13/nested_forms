from setuptools import setup

setup(name='nested_forms',
      version='0.2',
      description='An example Django app that shows how to do nested forms',
      url='http://github.com/jaywhy13/nested_forms',
      author='Jean-Mark Wright',
      author_email='jeanmark.wright@gmail.com',
      license='MIT',
      packages=[
            'nest', 
            'nested_forms', 
            'nest.templatetags', 
            'nest.management.commands'],
      package_data={
            'nest' : ['templates/*.html', 'static/**/*.js']
      },
      install_requires = [
            'Django>=1.5.5,<=2.0.0',
            'django-crispy-forms>=1.4.0',
      ],
      zip_safe=False)
