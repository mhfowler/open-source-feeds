FROM ubuntu:trusty
RUN echo "deb http://ppa.launchpad.net/mozillateam/firefox-next/ubuntu trusty main" > /etc/apt/sources.list.d//mozillateam-firefox-next-trusty.list
RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys CE49EC21
RUN apt-get update
RUN apt-get install -y curl firefox xvfb python-pip
RUN pip install selenium
RUN curl -L https://github.com/mozilla/geckodriver/releases/download/v0.17.0/geckodriver-v0.17.0-linux64.tar.gz | tar xz -C /usr/local/bin
ADD day1 /root/day1
ADD xvfb.init /etc/init.d/xvfb
RUN chmod +x /etc/init.d/xvfb
RUN update-rc.d xvfb defaults
ENV PYTHONPATH=/root/day1/:$PYTHONPATH
CMD (service xvfb start; export DISPLAY=:10; python /root/day1/day1/web_fetch.py)