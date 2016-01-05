HYPOTHESIS_PROFILE=slow

SOURCES=flask_generic_views tests examples scripts setup.py

test:
	py.test

release:
	python scripts/release.py

format:
	isort -rc $(SOURCES)
	find $(SOURCES) -name '*.py' | xargs pyformat --in-place

lint:
	flake8 $(SOURCES) --exclude=_compat.py

ci:
	tox -- --hypothesis-profile=$(HYPOTHESIS_PROFILE)

docs:
	$(MAKE) -C docs html

.PHONY: test ci docs