# about

this will be a microservice which runs scraping jobs

uses a queue to allow for scaling in the future
 

# Setting up Redis locally on OS X

Install Redis via Homebrew
```
brew install redis
brew services start redis
```

This should start a Redis server running at http://localhost:6739.

# Running the Flask app and RQ worker

```
\# start the Flask app
PYTHONPATH=$(pwd):$PYTHONPATH python hello_webapp/app.py

\# start the RQ worker
PYTHONPATH=$(pwd):$PYTHONPATH python hello_webapp/worker.py

\# start the RQ scheduler (necessary for delaying jobs when retrying)
PYTHONPATH=$(pwd):$PYTHONPATH python hello_webapp/scheduler.py
```
