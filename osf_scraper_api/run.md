# open 3 terminal windows

1. cd /Users/maxfowler/computer/projects/opensourcefeeds/osf_scraper_api; vir osf; PYTHONPATH=$(pwd):$PYTHONPATH python hello_webapp/worker.py osf

2. cd /Users/maxfowler/computer/projects/opensourcefeeds/osf_scraper_api; vir osf; PYTHONPATH=$(pwd):$PYTHONPATH python hello_webapp/scheduler.py

3. cd /Users/maxfowler/computer/projects/opensourcefeeds/osf_scraper_api; vir osf; PYTHONPATH=$(pwd):$PYTHONPATH python hello_webapp/app.py

visit http://127.0.0.1:5002/api/messages/10023/