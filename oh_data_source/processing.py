from collections import OrderedDict
from datetime import timedelta
import json
import zipfile

import arrow


def arrow_time(timestamp):
    arrow_compat_timestamp = '{}.{}'.format(timestamp[0:-6], timestamp[-6:])
    return arrow.get(arrow_compat_timestamp)


def load_search_data(takeout_zipfile):
    takeoutfile = zipfile.ZipFile(takeout_zipfile.datafile)
    timestamps = []
    queries_by_timestamp = {}
    for filename in takeoutfile.namelist():
        if filename.startswith('Takeout/Searches/'):
            with takeoutfile.open(filename) as f:
                filedata = b''
                for line in f:
                    filedata += line
                data = json.loads(filedata.decode('utf-8'))
                for query in data['event']:
                    timestamp = query['query']['id'][0]['timestamp_usec']
                    timestamps.append(timestamp)
                    queries_by_timestamp[timestamp] = query['query']['query_text']
    return queries_by_timestamp, timestamps


def search_string_to_data(inputstring, search_string='words'):
    if search_string == 'full':
        return [inputstring]
    else:
        return inputstring.split(' ')


def process_search_data(queries_by_timestamp, timestamps,
                        granularity='hour', search_string='words'):

    by_time = OrderedDict()

    if granularity == 'raw':
        for timestamp in timestamps:
            search_data = search_string_to_data(
                queries_by_timestamp[timestamp], search_string=search_string)
            search_counts = {}
            for word in search_data:
                if word in search_counts:
                    search_counts[word] += 1
                else:
                    search_counts[word] = 1
            by_time[arrow_time(timestamp).isoformat()] = search_counts

    else:
        start = arrow_time(timestamps[0]).floor(granularity)
        window_start = start
        now = arrow.get()

        n = 0
        while window_start < now:
            window_span = window_start.span(granularity)
            search_counts = {}
            try:
                while (arrow_time(timestamps[n]) > window_span[0] and
                       arrow_time(timestamps[n]) < window_span[1]):
                    search_data = search_string_to_data(
                        queries_by_timestamp[timestamps[n]], search_string)
                    for word in search_data:
                        if word in search_counts:
                            search_counts[word] += 1
                        else:
                            search_counts[word] = 1
                    n += 1
            except IndexError:
                pass
            by_time[window_start.isoformat()] = search_counts
            kwargs_timedelta = {granularity + 's': 1}
            window_start = window_start + timedelta(**kwargs_timedelta)

    return by_time
