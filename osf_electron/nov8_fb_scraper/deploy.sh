#!/usr/bin/env bash
rm -f "Facebook Scraper.zip"
rm -rf "Facebook Scraper"
echo "++ packaging electron app"
electron-packager ./ --platform=darwin --arch=x64 --prune --overwrite
echo "++ copying to Facebook Scraper"
mkdir -p "Facebook Scraper"
cp -r "Facebook Scraper-darwin-x64/Facebook Scraper.app/" "Facebook Scraper/Facebook Scraper.app/"
cp Instructions.txt "Facebook Scraper/Instructions.txt"
echo "++ creating zip file"
zip -r "Facebook Scraper.zip" "Facebook Scraper"
echo "++ uploading to s3"
aws s3 cp "Facebook Scraper.zip" "s3://opensourcefeeds/downloads/Facebook Scraper.zip" --profile osf