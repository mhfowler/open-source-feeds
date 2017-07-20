#!/usr/bin/env bash
curl -X PUT -H "Content-Type: application/json" -d '{"username":"maxhfowler@gmail.com", "friends": []}' "http://127.0.0.1:5002/api/scrape_posts/"