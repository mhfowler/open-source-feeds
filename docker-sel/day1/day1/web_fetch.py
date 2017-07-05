from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from hello_settings import SECRETS_DICT, DATA_DIR, friend_dir, posts_dir, get_posts_file_path, get_friends_file_path
import datetime
import os
import re
import time
import json
import random

usr = SECRETS_DICT['FB_USERNAME']
pwd = SECRETS_DICT['FB_PASSWORD']
print 'usr: {}'.format(usr)

BASE_URL = 'https://www.facebook.com'


def get_friends(driver, user):
    url = '{}/{}/friends'.format(BASE_URL, user)
    print('++ getting friends for {}'.format(url))
    driver.get(url)
    time.sleep(1)
    # scroll the page a few times
    found_end = False
    prev_num_friends = 0
    j = 0
    for i in range(0, 200):
        # print('++ scrolling')
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        friends = driver.find_elements_by_css_selector('.fsl a')
        num_friends = len(friends)
        if num_friends == prev_num_friends:
            j += 1
        prev_num_friends = num_friends
        if j > 3:
            break

    friends = driver.find_elements_by_css_selector('.fsl a')
    print '++ num friends found: {}'.format(len(friends))
    friend_file = os.path.join(friend_dir, user + '.txt')
    open1 = open(friend_file, 'w')
    with open1 as f:
        for friend in friends:
            friend_link = friend.get_attribute('href')
            match = re.match('https\:\/\/www\.facebook\.com/(\S+)\?.*', friend_link)
            if match:
                username = match.group(1)
                f.write(username + '\n')
                # print('++ found {}'.format(username))
            else:
                pass
                # print('xx: failed on {}'.format(friend_link))


def fb_get_posts(driver, user):
    url = '{}/{}'.format(BASE_URL, user)
    print('++ getting posts for {}'.format(url))
    driver.get(url)
    time.sleep(4)
    # posts = driver.find_elements_by_css_selector('.userContentWrapper')

    # scroll the page a few times
    for i in range(0, 4):
        print('++ scrolling')
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)

    posts = driver.find_elements_by_css_selector('a._5pcq')
    posts_after_election = []
    for post in posts:
        post_link = post.get_attribute('href')
        post_content = post.get_attribute('innerHTML')
        match = re.match('.*data-utime="(\d+)"', post_content)
        if match:
            timestamp = int(match.group(1))
            d = datetime.datetime.fromtimestamp(timestamp)
            # cutoff_date = datetime.date(month=11, day=1, year=2016)
            if d.month > 10 and d.year == 2016:
                posts_after_election.append({
                    'link': post_link,
                    'date': timestamp
                })
        else:
            pass
            # print('xx: failed to match: {}'.format(post_content))
        # print(post_content)
        # print('href: {}'.format(post_link))
        # print('************')
    return posts_after_election


def get_usernames_from_friends_file(input_path):
    with open(input_path, 'r') as file:
        friend_usernames = set([])
        for line in file:
            username = line.replace('\n', '')
            friend_usernames.add(username)
    return friend_usernames


def get_friends_posts(driver, input_path):
    friend_usernames = get_usernames_from_friends_file(input_path)
    for friend in friend_usernames:
        posts_file_path = os.path.join(posts_dir, friend + '.txt')
        if not os.path.exists(posts_file_path):
            with open(posts_file_path, 'w') as f:
                posts_after_election = fb_get_posts(driver=driver, user=friend)
                for post in posts_after_election:
                    f.write(json.dumps(post) + '\n')


def get_friends_of_friends(username):
    friends_file_path = get_friends_file_path(username)
    friends = list(get_usernames_from_friends_file(friends_file_path))
    random.shuffle(friends)
    for uname in friends:
        c_friend_file_path = get_friends_file_path(uname)
        if not os.path.exists(c_friend_file_path):
            driver = webdriver.Firefox()
            fb_login(driver)
            time.sleep(4)
            try:
                get_friends(driver=driver, user=uname)
            except:
                print('++ failed to get friends for {}'.format(uname))
            driver.quit()
        # for username in friend_usernames:
        #     get_friends_of_friends(driver=driver, username=username)


def get_posts_from_all_users(driver):
    driver = webdriver.Firefox()
    fb_login(driver)
    time.sleep(4)
    friends_files = os.listdir(friend_dir)
    for friend_file in friends_files:
        friend_path = os.path.join(friend_dir, friend_file)
        get_friends_posts(driver=driver, input_path=friend_path)
    driver.quit()


def fb_login(driver):
    # or you can use Chrome(executable_path="/usr/bin/chromedriver")
    print '++ logging into facebook'
    driver.get("http://www.facebook.org")
    time.sleep(1)
    assert "Facebook" in driver.title
    elem = driver.find_element_by_id("email")
    elem.send_keys(usr)
    elem = driver.find_element_by_id("pass")
    elem.send_keys(pwd)
    elem.send_keys(Keys.RETURN)


if __name__ == '__main__':

    print '++ running web_fetch.py'
    driver = webdriver.Firefox()
    fb_login(driver)
    get_friends(driver=driver, user='maxhfowler')
    driver.close()
