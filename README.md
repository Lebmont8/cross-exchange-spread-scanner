# Cross-Exchange Spread Scanner

Compare both directions of a two-venue BTC spread. Check whether the edge survives book depth and taker fees.

## Run locally

Python 3.11+; no dependencies, service accounts, or network calls are required.

~~~sh
python3 serve.py
~~~

Open http://127.0.0.1:8000. Use `--port 8001` if port 8000 is busy.

Change the order size from `0.25` to `0.10` BTC. The thin-book scenario can then be evaluated instead of being rejected for insufficient size.

## How it works

Each snapshot has two synthetic venues. The scanner walks asks for the buy leg and bids for the sell leg at the same size, then applies each venue's taker fee. It compares the resulting edge with the threshold and rejects stale or insufficient quotes. Both directions are evaluated independently.

The figures are estimates, not fills or returns. Real orders are not sent, and the model assumes funds and BTC are already positioned at the two venues. It does not model concurrent execution, transfer delays, or inventory rebalancing.

## Check the result

~~~sh
python3 -B -m unittest -v
curl 'http://127.0.0.1:8000/api/replay?size=0.10&minimum=3&age=1500'
~~~

`fixture.json` is the input, `demo.py` calculates the result, and `serve.py` serves the browser UI and the same result as JSON.
