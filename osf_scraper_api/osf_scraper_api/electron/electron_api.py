import time
import os
import json

from flask import make_response, jsonify, Blueprint, request, abort

from osf_scraper_api.electron.fb_posts import scrape_fb_posts_job, fb_posts_post_process
from osf_scraper_api.settings import ENV_DICT
from osf_scraper_api.electron.screenshot import screenshot_job, screenshots_post_process
from osf_scraper_api.electron.utils import save_current_pipeline, load_current_pipeline, get_current_friends
from osf_scraper_api.electron.make_pdf import make_pdf_job, make_text_pdf_job
from osf_scraper_api.electron.fb_friends import scrape_fb_friends
from osf_scraper_api.settings import TEMPLATE_DIR
from osf_scraper_api.utilities.log_helper import _log
from osf_scraper_api.utilities.osf_helper import paginate_list, load_last_uptime, convert_js_date_to_datetime
from osf_scraper_api.utilities.rq_helper import enqueue_job, restart_failed_jobs, stop_jobs
from osf_scraper_api.utilities.fs_helper import list_files_in_folder, delete_file
from osf_scraper_api.settings import NUMBER_OF_POST_SWEEPS, MIN_TIME_TO_PIPELINE_CHECK


def get_electron_api_blueprint():
    electron_blueprint = Blueprint('electron_blueprint', __name__, template_folder=TEMPLATE_DIR)

    @electron_blueprint.route('/api/electron/stop/', methods=['GET'])
    def stop_jobs_endpoint():
        stop_jobs()
        # stop running workers
        worker_dir = 'workers'
        worker_files = list_files_in_folder(worker_dir)
        for worker_file in worker_files:
            _log('++ stopping worker: {}'.format(worker_file))
            delete_file(worker_file)
        # log success
        _log('++ successful request to stop current pipeline')
        current_pipeline = load_current_pipeline()
        save_current_pipeline(
            pipeline_name=current_pipeline.get('pipeline_name'),
            pipeline_status='stopped'
        )
        return make_response(jsonify({
            'message': 'ok'
        }), 200)

    @electron_blueprint.route('/api/electron/fb_friends/', methods=['POST'])
    def fb_friends_endpoint():
        _log('++ received request to friends endpoint')
        params = request.get_json()

        required_fields = [
            'fb_username',
            'fb_password',
        ]
        for req_field in required_fields:
            if req_field not in params.keys():
                abort(make_response(jsonify({'message': '{} field is required.'.format(req_field)}), 422))

        save_current_pipeline(
            pipeline_name='fb_friends',
            pipeline_status='running',
            pipeline_params={'fb_username': params['fb_username']}
        )
        enqueue_job(scrape_fb_friends,
            fb_username=params['fb_username'],
            fb_password=params['fb_password'],
            timeout=108000
        )
        return make_response(jsonify({
            'message': 'fb_friend job enqueued'
        }), 200)

    @electron_blueprint.route('/api/electron/fb_posts/', methods=['POST'])
    def fb_posts_endpoint():
        _log('++ received request to posts endpoint')
        params = request.get_json()

        required_fields = [
            'fb_username',
            'fb_password',
            'selected_friends'
        ]
        for req_field in required_fields:
            if req_field not in params.keys():
                abort(make_response(jsonify({'message': '{} field is required.'.format(req_field)}), 422))

        which_pages_setting = params.get('which_pages_setting')
        selected_friends = params.get('selected_friends')
        if which_pages_setting == 'all':
            users = get_current_friends()
        else:
            users = selected_friends

        base_output_folder = os.path.join(ENV_DICT['FS_BASE_PATH'], 'posts')
        now = str(int(time.time()))
        output_folder = os.path.join(base_output_folder, now)
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        before_date = params.get('before_date')
        if before_date:
            before_dt = convert_js_date_to_datetime(before_date)
            before_timestamp = time.mktime(before_dt.timetuple())
        else:
            before_timestamp = None

        after_date = params.get('after_date')
        if after_date:
            after_dt = convert_js_date_to_datetime(after_date)
            after_timestamp = time.mktime(after_dt.timetuple())
        else:
            after_timestamp = None

        scraper_params = {
            'after_timestamp': after_timestamp,
            'before_timestamp': before_timestamp,
            'jump_to_timestamp': before_timestamp # jump to the latest date to save time
        }

        page_size = 50
        pages = paginate_list(mylist=users, page_size=page_size)
        job_ids = []
        if len(pages) > 2:
            num_sweeps = NUMBER_OF_POST_SWEEPS
        else:
            num_sweeps = 1
        for sweep_number in range(0, num_sweeps):
            _log('++ enqueing {num_users} users in {num_jobs} jobs, #{sweep_number}'.format(
                num_users=len(users),
                num_jobs=len(pages),
                sweep_number=sweep_number
            ))
            for index, page in enumerate(pages):
                _log('++ enqueing {} job'.format(index))
                job = enqueue_job(scrape_fb_posts_job,
                    users=page,
                    scraper_params=scraper_params,
                    output_folder=output_folder,
                    fb_username=params['fb_username'],
                    fb_password=params['fb_password'],
                    timeout=5000
                )
                job_ids.append(job.id)
        # save which job_ids are in this stage
        pipeline_params = scraper_params
        pipeline_params['output_folder'] = output_folder
        save_current_pipeline(
            pipeline_name='fb_posts',
            pipeline_status='running',
            pipeline_params=pipeline_params,
            num_total=len(users)
        )
        # finally return 'OK' response
        return make_response(jsonify({
            'message': 'fb_posts job enqueued'
        }), 200)

    @electron_blueprint.route('/api/electron/check_pipeline/', methods=['GET'])
    def check_job_stage_endpoint():
        _log('++ received request to pipeline endpoint')
        pipeline_dict = load_current_pipeline()
        if not pipeline_dict:
            _log('++ no pipeline found')
            return make_response(jsonify({
                'message': 'no pipeline found'
            }), 200)
        pipeline_name = pipeline_dict['pipeline_name']
        restart_failed_jobs()
        time.sleep(2)
        # check how recently docker was restarted, if < 3 minutes... then don't advance stage
        last_uptime = load_last_uptime()
        now = int(time.time())
        total_uptime_seconds = now - last_uptime
        if (total_uptime_seconds < MIN_TIME_TO_PIPELINE_CHECK):
            _log('++ skipping pipeline check due to recent restart')
            return make_response(jsonify({
                'message': 'ok'
            }), 200)
        _log('++ checking whether pipeline is complete')
        if pipeline_name == 'fb_posts':
            _log('++ checking whether posts pipeline is complete')
            fb_posts_post_process()
        elif pipeline_name == 'fb_screenshots':
            _log('++ checking whether screenshots pipeline is complete')
            screenshots_post_process()
        elif pipeline_name in ['fb_friends', 'make_pdf']:
            pass
        else:
            raise Exception('++ invalid pipeline: {}'.format(pipeline_name))
        return make_response(jsonify({
            'message': 'ok'
        }), 200)

    @electron_blueprint.route('/api/electron/pdf/', methods=['POST'])
    def pdf_endpoint():
        params = request.get_json()
        input_datas = params['input_datas']
        fb_username = params['fb_username']
        fb_password = params['fb_password']
        screenshot_posts = params['screenshot_posts']
        chronological = params['chronological']
        if screenshot_posts:
            return fb_screenshots_endpoint(input_datas=input_datas, fb_username=fb_username, fb_password=fb_password, chronological=chronological)
        else:
            all_posts = []
            for input_data in input_datas:
                try:
                    posts = json.loads(input_data)
                    all_posts += posts
                except:
                    _log('++ failed to parse posts file')
            enqueue_job(make_text_pdf_job,
                        posts=all_posts,
                        chronological=chronological,
                        timeout=432000)
            return make_response(jsonify({
                'message': '.txt job enqueued'
            }), 200)

    def fb_screenshots_endpoint(input_datas, fb_username, fb_password, chronological):
        enqueue_job(screenshot_job,
            input_datas=input_datas,
            fb_username=fb_username,
            fb_password=fb_password,
            chronological=chronological,
            timeout = 3600
        )
        return make_response(jsonify({
            'message': 'fb_screenshot job enqueued'
        }), 200)

    @electron_blueprint.route('/api/electron/pdf/', methods=['POST'])
    def make_pdf_endpoint():
        params = request.get_json()
        bottom_crop_pix = params.get('bottom_crop_pix', 5)
        not_chronological = params.get('not_chronological', False)
        _log('++ enqueing make_pdf_job')
        enqueue_job(make_pdf_job,
                    bottom_crop_pix=bottom_crop_pix,
                    not_chronological=not_chronological,
                    timeout=432000)
        return make_response(jsonify({
            'message': 'pdf job enqueued'
        }), 200)

    @electron_blueprint.route('/api/electron/fb_friends/', methods=['GET'])
    def get_fb_friends_endpoint():
        friends = get_current_friends()
        to_return = {
            'friends': friends
        }
        return make_response(jsonify(to_return), 200)

    return electron_blueprint
