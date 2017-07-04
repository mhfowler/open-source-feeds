from hello_settings import SECRETS_DICT, DATA_DIR, friend_dir, posts_dir, get_posts_file_path, get_friends_file_path
import os
import json
import datetime
import webbrowser
import random


def show_posts_from_friends(username):
    friends_file_path = get_friends_file_path(username)
    friends_data = {}
    posts_not_found = []
    all_posts = []
    with open(friends_file_path, 'r') as f:
        for line in f:
            friend_username = line.replace('\n', '')
            posts_file_path = get_posts_file_path(friend_username)
            if not os.path.isfile(posts_file_path):
                posts_not_found.append(friend_username)
                continue
            with open (posts_file_path, 'r') as posts_file:
                friend_posts = []
                for post in posts_file:
                    post_dict = json.loads(post)
                    friend_posts.append(post_dict)
                    all_posts.append(post_dict)
                friends_data[friend_username] = friend_posts
    for uname in posts_not_found:
        print('++ posts not found for: {}'.format(uname))
    for f_username, posts in friends_data.items():
        # filter(lambda post: datetime.datetime.fromtimestamp(post['date'].day == 9), posts)
        print('{username}: {num_posts}'.format(username=f_username, num_posts=len(posts)))
    # totals
    print('total number of posts: {}'.format(len(all_posts)))
    for post in all_posts:
        post['datetime'] = datetime.datetime.fromtimestamp(int(post['date']))
    for day in range(0, 20):
        day_posts = filter(lambda post: post['datetime'].day == day, all_posts)
        print('num posts on {}: {}'.format(day, len(list(day_posts))))
    # show posts on the day after the election
    election_posts = list(filter(lambda post: post['datetime'].day == 9, all_posts))
    random.shuffle(election_posts)
    for post in election_posts:
        link = post['link']
        webbrowser.open_new_tab(link)
        input('next?')




if __name__ == '__main__':
    username = 'maximusfowler'
    show_posts_from_friends(username=username)