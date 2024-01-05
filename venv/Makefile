#
# build venv: cd venv; make
# update deps: $EDITOR requirements.in; make
# update tools: make pkgup

EXE := progname
PYBASE := python3.9

venv: bin/python3 bin/pip-compile bin/$(EXE)

bin/python3:
	$(PYBASE) -m venv --symlinks .

bin/$(EXE): requirements.txt
	bin/pip-sync -q
	@# $(EXE) might not have changed as a result of sync, so it would
	@# re-sync every time if we didn't update its timestamp
	touch bin/$(EXE)

requirements.txt compile: requirements.in
	bin/pip-compile -q requirements.in

bin/pip-compile pkgup:
	bin/pip3 install -q -U pip wheel setuptools pip-tools

clean:
	rm -rf bin include lib lib64 pyvenv.cfg

rebuild: clean venv

.PHONY: venv pkgup compile clean rebuild
