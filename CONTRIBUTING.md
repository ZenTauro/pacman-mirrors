# Contributing

Contributions are welcome, and they are greatly appreciated! Every
little bit helps, and credit will always be given.

You can contribute in many ways:

## Types of Contributions

### Report Bugs

Report bugs at [Manjaro Gitlab](https://gitlab.manjaro.org/applications/pacman-mirrors/issues).

If you are reporting a bug, please include:

- Your operating system name and version.
- Any details about your local setup that might be helpful in troubleshooting.
- Detailed steps to reproduce the bug.

### Fix Bugs

Look through the Gitlab issues for bugs. Anything tagged with "bug"
is open to whoever wants to implement it.

### Implement Features

Look through the Gitlab issues for features. Anything tagged with "feature"
is open to whoever wants to implement it.

### Write Documentation

pacman-mirrors could always use more documentation, whether as part of the
official pacman-mirrors docs, in docstrings, or even on the web in blog posts,
articles, and such.

### Translations

Help us to ship pacman-mirrors in your language by helping our translators on [Transifex](https://www.transifex.com/manjarolinux/manjaro-pacman-mirrors/dashboard/).

### Submit Feedback

The best way to send feedback is to file an issue at [Manjaro Gitlab](https://gitlab.manjaro.org/applications/pacman-mirrors/issues).

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

## Get Started!

Ready to contribute? Here's how to set up `pacman-mirrors` for local development.

* Fork the `pacman-mirrors` repo on GitHub.
* Clone your fork locally:
    
```
$ git clone https://gitlab.manjaro.org/your-name-here/pacman-mirrors.git
```
    
* Install your local copy into a virtualenv. Assuming you have [virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/en/latest/) installed, this is how you set up your fork for local development

```    
$ mkvirtualenv pacman-mirrors
$ cd pacman-mirrors/
$ python setup.py develop
```

* Create a branch for local development:

```
$ git checkout -b name-of-your-bugfix-or-feature
```

   Now you can make your changes locally.

* When you're done making changes, check that your changes pass flake8 and the tests:

```
$ flake8 pacman-mirrors tests
$ python setup.py test
```

* To get flake8, just pip install it into your virtualenv (see notes below).
* Commit your changes and push your branch to GitHub:

```
$ git add
$ git commit -m "Your detailed description of your changes."
$ git push origin name-of-your-bugfix-or-feature
```

* Submit a pull request through the GitHub website.

## Test Guidelines

```
make test

```
### Generated Mirrorlist Verification
From experience it is so easy to forget verification of the generated mirrorlists.

As the mirrorlists can be generated in a variety of ways - a list of verifications is presented here.

1. `sudo pacman-mirrors -c all`
2. `sudo pacman-mirrors -f`
3. `sudo pacman-mirrors -c Germany`
4. `sudo pacman-mirrors -c Germany -i`
5. `sudo pacman-mirrors -aP https -c Germany` 
6. `sudo pacman-mirrors -aP https http -c Germany -i`
7. `sudo pacman-mirrors -aP http https -c Germany -i`
8. `sudo pacman-mirrors -aP https http -c Germany`
9. `sudo pacman-mirrors -aP http https -c Germany`

All urls in the mirrorlist **must** end with **$repo/$arch**

## Pull Request Guidelines

Before you submit a pull request, check that it meets these guidelines:

* The pull request should include tests.
* If the pull request adds functionality, the docs should be updated. Put
   your new functionality into a function with a docstring, and add the
   feature to the list in README.md.
* The pull request should work for Python 3.4+, and for PyPy. Check
   https://travis-ci.org/manjaro/pacman-mirrors/pull_requests
   and make sure that the tests pass for all supported Python versions.

## Tips

To run a subset of tests:

```
$ python -m unittest tests.test_pacman_mirrors
```

## Developing environment

* An editor of choice e.g.
   * Visual Studio Code `pacman -Syu code`
   * PyCharm Community `pacman -Syu pycharm-community`
* Pandoc converter `pacman -Syu pandoc`
* Python environment

    ```
    $ git clone https://gitlab.manjaro.org/applications/pacman-mirrors.git
    $ cd pacman-mirrors
    $ sudo pacman -Syu python-virtualenvwrapper
    $ mkvirtualenv pacman-mirrors
    $ python setup.py develop
    $ pip install mkdocs coverage babel flake8 npyscreen transifex-client
    ```

* Remember to `source /usr/bin/virtualenvwrapper.sh` to get the virtualenv CLI
