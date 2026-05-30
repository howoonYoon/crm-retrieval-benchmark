PYTHON ?= python

.PHONY: install run eval build-corpus inspect plot clean-results

install:
	$(PYTHON) -m pip install -r requirements.txt

run: eval

eval:
	$(PYTHON) run_eval.py

build-corpus:
	$(PYTHON) src/build_corpus.py

inspect:
	$(PYTHON) src/inspect_corpus.py

plot:
	$(PYTHON) src/plot_results.py

clean-results:
	$(PYTHON) -c "from pathlib import Path; [p.unlink() for p in Path('results').glob('*') if p.is_file()]"
