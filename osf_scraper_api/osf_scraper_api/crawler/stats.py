from osf_scraper_api.utilities.fs_helper import file_exists, list_files_in_folder
from osf_scraper_api.crawler.utils import get_user_from_user_file, get_posts_folder
from osf_scraper_api.utilities.fb_helper import fetch_friends_of_user


def get_stats(user):

    posts_folder = get_posts_folder()
    user_files = list_files_in_folder(posts_folder)
    users = []
    for user_file in user_files:
        username = get_user_from_user_file(user_file=user_file, input_folder=posts_folder)
        users.append(username)

    friends = fetch_friends_of_user(user)

    num_processed = 0
    for friend in friends:
        if friend in users:
            num_processed += 1

    print 'processed {} of {}'.format(num_processed, len(friends))


if __name__ == '__main__':
    get_stats('maxhfowler')
