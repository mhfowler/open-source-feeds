#!/usr/bin/env bash
mv ~/Desktop/osf/data/log.txt ~/Desktop/log-$(date +%s).txt
rm -f ~/Desktop/osf/data/status.json
rm -f ~/Desktop/osf/data/stage.json
rm -f ~/Desktop/osf/data/uptime.json
rm -rf ~/Desktop/osf/data/workers
rm -rf ~/Desktop/osf/data/posts
rm -rf ~/Desktop/osf/data/screenshots
rm -rf ~/Desktop/osf/data/pdfs
rm -rf ~/Desktop/osf/redis