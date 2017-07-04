from hello_settings import friend_dir, DATA_DIR
import os
import re


raw_friend_dir = os.path.join(DATA_DIR, 'raw_friends')

def clean_friends_data():
    files = [f for f in os.listdir(raw_friend_dir) if os.path.isfile(os.path.join(raw_friend_dir, f))]
    for fname in files:
        friend_usernames = set([])
        f_path = os.path.join(raw_friend_dir, fname)
        print('cp: {}'.format(f_path))
        with open(f_path, 'r') as f:
            for line in f:
                match = re.match('friend\: https\:\/\/www\.facebook\.com/(\S+)\?.*\n', line)
                if match:
                    username = match.group(1)
                    friend_usernames.add(username)
                    print('++ found {}'.format(username))
                else:
                    print('xx: failed on {}'.format(line))
        o_path = os.path.join(friend_dir, fname)
        with open(o_path, 'w') as o_file:
            for friend in friend_usernames:
                o_file.write(friend + '\n')

if __name__ == '__main__':
    clean_friends_data()