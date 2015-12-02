import boto3

client = boto3.client('logs')
log_groups = client.describe_log_groups(
    logGroupNamePrefix='/aws/lambda/')['logGroups']
for log_group in log_groups:
    streams = client.describe_log_streams(
        logGroupName=log_group['logGroupName'])['logStreams']
    for stream in streams:
        events = client.get_log_events(
            logGroupName=log_group['logGroupName'],
            logStreamName=stream['logStreamName'])['events']
        for event in events:
            print(event['message'])
