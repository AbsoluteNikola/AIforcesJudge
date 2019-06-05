import multiprocessing as mp
import subprocess
import requests
import config
import os
from os.path import join

from loguru import logger

from judge import Judge


def run(queue: mp.Queue):
    pool = mp.Pool(initializer=init_process)
    logger.info("Starting process poll...")
    while True:
        data = queue.get()
        if isinstance(data, str) and data == 'die':
            logger.info('time to go out with a bang!')
            return
        pool.apply_async(run_fight, (data, ), callback=res_callback, error_callback=err_callback)


@logger.catch
def run_fight(data, *args, **kwargs):

    # TODO: timeout from request
    j = Judge(
        game=data['game'],
        lang=data['lang'],
        source=data['source'],
        timeout=data['timeout'],
        challenge_id=data['challenge_id'],
        state_par=data['state_par']
    )
    data = j.run()
    requests.post(config.SUBMISSION_RESULT_ENDPOINT, json=data)
    logger.success(f'{data["challenge_id"]} was sent successfully')


def err_callback(exc):
    logger.warning(f'ERROR at Judge \n{exc}')
    # TODO: implement errors check
    pass


def res_callback(res):
    """
    it states here just for fun
    :param res: must be None
    :return:
    """
    pass


def init_process():
    my_wd = f'tmp/{os.getpid()}'
    for path in [f'{my_wd}/first', f'{my_wd}/second']:
        if os.path.exists(path):
            shutil.rmtree(path)
        os.makedirs(path)
        code = subprocess.call(['python3', '-m', 'venv', join(path, 'venv')])
        if code != 0:
            logger.critical(f"Error while creating venv {os.getpid()}")
            exit(1)
    os.chdir(my_wd)
    logger.success(f"init new worker {os.getpid()}")
