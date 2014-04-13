# Copyright (c) 2014, Riverbank Computing Limited
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.


PYTHON=python3
PYTHON2=python

.PHONY: default develop develop-uninstall upload wheel sdist doc clean

default:
	@echo "Specify develop, develop-uninstall, upload, wheel, sdist, doc or clean"

develop: VERSION pyqtdeploy/version.py
	$(PYTHON) setup.py develop

develop-uninstall:
	$(PYTHON) setup.py develop --uninstall

upload: clean VERSION pyqtdeploy/version.py
	$(PYTHON2) build.py changelog
	$(PYTHON) setup.py bdist_wheel sdist
	twine upload -r pypi dist/*

wheel: clean VERSION pyqtdeploy/version.py
	$(PYTHON2) build.py changelog
	$(PYTHON) setup.py bdist_wheel

sdist: clean doc
	$(PYTHON2) build.py changelog
	$(PYTHON) setup.py sdist

doc: VERSION
	mkdir -p doc/_build
	$(MAKE) -C doc html

clean:
	rm -f ChangeLog* VERSION MANIFEST pyqtdeploy/version.py
	rm -rf build dist pyqtdeploy.egg-info
	rm -rf doc/_build doc/html doc/doctrees
	find . -depth -name __pycache__ -exec rm -rf {} \;

VERSION:
	$(PYTHON2) build.py -o VERSION version

pyqtdeploy/version.py:
	$(PYTHON2) build.py -o pyqtdeploy/version.py pyversion
