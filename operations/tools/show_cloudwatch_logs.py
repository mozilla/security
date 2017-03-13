#!/usr/bin/python

import sys
import boto3

client = boto3.client('logs')
log_group_name = sys.argv[1]


class Printer():

    def __init__(self):
        self.x = True

    def display(self, line):
        if self.x:
            self.x = False
            print('\033[92m' + self.trim_guid(line.rstrip()) + '\033[0m')
        else:
            self.x = True
            print(self.trim_buid(line.rstrip()))

    def trim_guid(self, line):
        POSITION = 2
        TRIM_LENGTH = 2
        mf = line.split()
        if (len(mf) >= POSITION + 1 and
                len(mf[POSITION]) == 36 and
                mf[POSITION][8] + mf[POSITION][13] +
                mf[POSITION][18] + mf[POSITION][23] == '----'):
            mf[POSITION] = '**' + mf[POSITION][-TRIM_LENGTH:]
            return(' '.join(mf))
        else:
            return(line)


printer = Printer()
log_stream_paginator = client.get_paginator('describe_log_streams')

stream_iterator = [{'logStreams': [{'logStreamName': sys.argv[2]}]}] if len(
    sys.argv) > 2 else log_stream_paginator.paginate(logGroupName=log_group_name)

for stream_page in stream_iterator:
    for log_stream_name in [x['logStreamName']
                            for x
                            in stream_page['logStreams']]:
        # Have to make our own paginator for get_log_events
        # https://github.com/boto/botocore/commit/2bcad3fefc99bfa600b3aa9e40f21cf89bc88f4b
        params = {'logGroupName': log_group_name,
                  'logStreamName': log_stream_name,
                  'startFromHead': True,
                  'startTime': 0}
        last_token = None
        while last_token is None or last_token != params['nextToken']:
            last_token = params['nextToken'] if 'nextToken' in params else None
            response = client.get_log_events(**params)
            params['nextToken'] = response['nextForwardToken']
            for event in response['events']:
                printer.display(event['message'])
