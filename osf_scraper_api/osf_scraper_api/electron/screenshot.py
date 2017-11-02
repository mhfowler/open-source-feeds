import tempfile
import os
import json

from osf_scraper_api.utilities.fs_helper import load_dict
from osf_scraper_api.electron.make_pdf import make_pdf_job
from osf_scraper_api.utilities.log_helper import _log, _capture_exception
from osf_scraper_api.utilities.osf_helper import get_fb_scraper, paginate_list, wait_for_online
from osf_scraper_api.utilities.fs_helper import file_exists
from osf_scraper_api.utilities.fs_helper import save_file
from osf_scraper_api.settings import ENV_DICT, NUMBER_OF_SCREENSHOT_SWEEPS
from osf_scraper_api.electron.utils import save_current_pipeline, load_current_pipeline, \
    get_screenshot_output_key_from_post
from osf_scraper_api.utilities.selenium_helper import restart_selenium
from osf_scraper_api.utilities.rq_helper import get_all_rq_jobs, enqueue_job


def screenshot_post_helper(post, fb_scraper):
    output_path = get_screenshot_output_key_from_post(post)
    f = tempfile.NamedTemporaryFile(delete=False)
    f.close()
    temp_path = f.name + '.png'
    found_post = fb_scraper.screenshot_post(post=post, output_path=temp_path)
    if found_post:
        image_url = save_file(source_file_path=temp_path, destination=output_path)
        os.unlink(f.name)
        os.unlink(temp_path)
        _log('++ successfuly saved to: `{}`'.format(image_url))
        return True
    else:
        _log('++ no post found at link')
        return False


def screenshot_post(post, fb_scraper):
    try:
        output_path = get_screenshot_output_key_from_post(post)
        if file_exists(output_path):
            _log('++ skipping {}'.format(output_path))
            return
        screenshot_post_helper(post=post, fb_scraper=fb_scraper)
        # if we succeeded, then set num_initializations back to 0
        fb_scraper.num_initializations = 0
    except Exception as e:
        _log('++ encountered error: {}'.format(str(e)))
        wait_for_online()
        if fb_scraper.num_initializations < 3:
            _log('++ retrying attempt {}'.format(fb_scraper.num_initializations))
            fb_scraper.re_initialize_driver()
            return screenshot_post(post=post, fb_scraper=fb_scraper)
        else:
            restart_selenium()
            fb_scraper.re_initialize_driver()
            _log('++ giving up on `{}`'.format(post['link']))
            raise e


def screenshot_job(input_datas, fb_username, fb_password, chronological=False):
    save_current_pipeline(
        pipeline_name='fb_screenshots',
        pipeline_status='running',
        pipeline_params={'chronological': chronological}
    )
    all_posts = []
    posts_to_scrape = []
    num_input_datas = len(input_datas)
    _log('++ enqueuing screenshot jobs for {} files'.format(num_input_datas))
    for index, posts_data in enumerate(input_datas):
        try:
            posts = json.loads(posts_data)
            all_posts += posts
            for post in posts:
                output_key = get_screenshot_output_key_from_post(post=post)
                if file_exists(output_key):
                    pass
                else:
                    posts_to_scrape.append(post)
        except:
            _log('++ failed to load posts for file')
        if not index % 10:
            _log('++ loading posts {}/{}'.format(index, num_input_datas))

    # save the actual posts
    save_current_pipeline(
        pipeline_name='fb_screenshots',
        pipeline_status='running',
        pipeline_params={
            'posts': all_posts,
            'chronological': chronological,
        }
    )
    # start jobs to screenshot the posts in pages
    page_size=100
    pages = paginate_list(mylist=posts_to_scrape, page_size=page_size)
    for sweep_number in range(0, NUMBER_OF_SCREENSHOT_SWEEPS):
        _log('++ enqueing {num_posts} posts in {num_jobs} jobs, #{sweep_number}'.format(
            num_posts=len(posts_to_scrape),
            num_jobs=len(pages),
            sweep_number=sweep_number
        ))
        for index, page in enumerate(pages):
            _log('++ enqueing page {}'.format(index))
            enqueue_job(screenshot_posts,
                              posts=page,
                              fb_username=fb_username,
                              fb_password=fb_password,
                              timeout=3600,
                              )


def screenshot_posts(posts, fb_username, fb_password):
    _log('++ starting screenshot_posts job')
    fb_scraper = get_fb_scraper(fb_username=fb_username, fb_password=fb_password)
    num_posts = len(posts)
    _log('++ preparing to screenshot {} posts'.format(num_posts))
    for index, post in enumerate(posts):
        try:
            _log('++ saving screenshot of post: `{}` {}/{}'.format(post['link'], index, num_posts))
            screenshot_post(post=post, fb_scraper=fb_scraper)
        except Exception as e:
            _capture_exception(e)
    _log('++ finished screenshotting all posts')
    fb_scraper.quit_driver()


def screenshots_post_process():
    _log('++ running post process check for pending screenshot jobs')
    # check if there are any other pending scrape_posts jobs for this user
    rq_jobs = get_all_rq_jobs()

    def filter_fun(job):
        if job.func_name == 'osf_scraper_api.electron.screenshot.screenshot_posts':
            return True
        # otherwise return False
        return False

    pending = filter(filter_fun, rq_jobs)
    # if no pending job found, then screenshot pipeline is complete
    if len(pending) == 0:
        _log('++ screenshot pipeline complete')
        finished_pipeline = load_current_pipeline()
        pipeline_params = finished_pipeline['pipeline_params']
        posts = pipeline_params['posts']
        bottom_crop_pix = pipeline_params.get('bottom_crop_pix', 5)
        chronological = pipeline_params.get('chronological', False)
        enqueue_job(make_pdf_job,
                    posts=posts,
                    chronological=chronological,
                    bottom_crop_pix=bottom_crop_pix,
                    timeout=432000)
    else:
        current_pipeline = load_current_pipeline()
        pipeline_params = current_pipeline['pipeline_params']
        posts = pipeline_params['posts']
        num_processed = 0
        for post in posts:
            screenshot_path = get_screenshot_output_key_from_post(post)
            if os.path.exists(screenshot_path):
                num_processed += 1
        save_current_pipeline(
            pipeline_params=pipeline_params,
            pipeline_name='fb_screenshots',
            pipeline_status='running',
            num_processed=num_processed,
            num_total=len(posts)
        )
        job_logs = []
        for job in rq_jobs:
            j = {
                'id': job.id,
                'started_at': str(job.started_at)
            }
            job_logs.append(j)
        _log('++ found {} pending jobs, continuing screenshots pipeline'.format(
            len(pending),
        ))
