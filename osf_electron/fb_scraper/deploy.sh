#!/usr/bin/env bash
rm -f "Open Source Feeds.zip"
rm -rf "Open Source Feeds"
echo "++ packaging electron app"
electron-packager ./ --platform=darwin --arch=x64 --prune --overwrite
echo "++ copying to Open Source Feeds"
mkdir -p "Open Source Feeds"
cp -r "Open Source Feeds-darwin-x64/Open Source Feeds.app/" "Open Source Feeds/Open Source Feeds.app/"
cp Instructions.txt "Open Source Feeds/Instructions.txt"
echo "++ creating zip file"
zip -r "Open Source Feeds.zip" "Open Source Feeds"
echo "++ uploading to s3"
aws s3 cp "Open Source Feeds.zip" "s3://opensourcefeeds/downloads/Open Source Feeds.zip" --profile osf