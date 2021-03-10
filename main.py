import sys
import random

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from titlecase import titlecase

arg = sys.argv[1]


def start_session(retries=None, session=None, backoff_factor=0, status_forcelist=(500, 502, 503, 504)):
    session = session or requests.Session()

    if retries:
        retry = Retry(
            total=retries,
            read=retries,
            connect=retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
            method_whitelist=frozenset(['GET', 'POST'])
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)

    session.headers.update({
        'Accept': 'application/json',
        })
    return session


def find_topic_nouns(topic):
    params = {
        'topics': topic,
        'md': 'p',
        'max': 100
    }
    nouns = []

    try_list = [
        {
            'rel_nry': topic,
            'rel_trg': topic,
        },

        {
            'rel_nry': topic,
            'rel_spc': topic,
        },

        {
            'rel_ant': topic,
            'rel_trg': topic
        },

        {
            'rel_spc': topic
        },

        {
            'rel_trg': topic
        },

        {
            'rel_gen': topic
        },
    ]

    random.shuffle(try_list)

    for item in try_list:
        try_params = {}
        try_params.update(params)
        try_params.update(item)
        param_str = params_to_str(try_params)
        print(param_str)
        result = get_word(param_str)

        if result:
            for item in result:
                if ('tags' in item) and ('n' in item.get('tags')):
                    nouns.append(item.get('word'))

    if not nouns:
        param_str = params_to_str(params)
        result = get_word(param_str)

        if result:
            for item in result:
                if ('tags' in item) and ('n' in item.get('tags')):
                    nouns.append(item.get('word'))

    return nouns


def find_adjective(nouns):
    for noun in nouns:
        params = {
            'rel_jjb': noun,
            'md': 'p',
            'max': 100
        }

        param_str = params_to_str(params)
        result = get_word(param_str)

        if not result:
            continue

        random.shuffle(result)

        for item in result:
            if ('tags' in item) and ('adj' in item.get('tags')):
                adj = item.get('word')
                break
        if adj:
            match_noun = noun
            break

    return adj, match_noun


def params_to_str(params: dict):
    param_str = '?' + '&'.join(['='.join([key, str(val)]) for key, val in params.items()])
    return param_str


# API reference: https://www.datamuse.com/api/
def get_word(param_str: str):
    try:
        r = session.get(f'https://api.datamuse.com/words{param_str}')
        r.raise_for_status()

        result = r.json()

        if not result:
            raise ValueError('No results found in Datamuse API')

        return result

    except ValueError as value_error:
        print(value_error)
        return None

    except Exception as error:
        print('Failed getting results from Datamuse API', error)
        return None


if __name__ == '__main__':
    session = start_session()

    nouns = find_topic_nouns(arg)
    random.shuffle(nouns)
    adj, noun = find_adjective(nouns)

    print(titlecase(f'{adj} {noun}'))
