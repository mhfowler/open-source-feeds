import os
import urllib

from osf_scraper_api.electron.utils import save_current_pipeline, load_current_pipeline, \
    convert_to_host_path, load_posts_from_folder, get_image_output_key_from_url
from osf_scraper_api.utilities.log_helper import _log
from osf_scraper_api.utilities.fs_helper import file_exists, save_file


def download_images_job(posts_folder):
    save_current_pipeline(
        pipeline_name='download_images',
        pipeline_status='running',
        pipeline_params={'posts_folder': posts_folder},
    )
    posts = load_posts_from_folder(posts_folder)
    all_images = []
    for post in posts:
        content = post['content']
        images = content.get('images')
        for image in images:
            all_images.append(image)
    _log('++ downloading {} images'.format(len(all_images)))
    for image_url in all_images:
        image_output_key = get_image_output_key_from_url(image_url)
        if file_exists(image_output_key):
            _log('++ skipping {}'.format(image_url))
        else:
            urllib.urlretrieve(image_url, "temp.jpg")
            _log('++ saving {} to {}'.format(image_url, image_output_key))
            save_file("temp.jpg", image_output_key)
    _log('++ download image job complete')
    save_current_pipeline(
        pipeline_name='download_images',
        pipeline_status='finished',
        pipeline_message=posts_folder
    )