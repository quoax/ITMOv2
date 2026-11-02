.PHONY: test serve e2e
test:
	python3 -m unittest -v
serve:
	python3 http_server.py
e2e:
	python3 e2e_check.py && echo "Wrote results_e2e.md"
