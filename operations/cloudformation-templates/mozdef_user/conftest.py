import pytest

def pytest_addoption(parser):
    parser.addoption(
        "--environment",
        choices=['prod', 'qa'],
        default="prod")

@pytest.fixture
def config(request):
    environments = {
        'prod': {
            "BackupBucketName": "mozdefes2backups",
            "BlocklistBucketName": "mozilla_infosec_blocklist",
            "IPSpaceBucketName": "mozilla-ipspace",
            "InfosecQueueArn": "arn:aws:sqs:us-west-1:656532927350:infosec_mozdef_events",
            "NubisQueueArn": "arn:aws:sqs:us-west-1:656532927350:nubis_events_prod",
            "FxaQueueArn": "arn:aws:sqs:us-west-2:361527076523:fxa-customs-prod",
            "source_arn": "arn:aws:iam::656532927350:user/mozdef"
            # "source_arn": "arn:aws:iam::656532927350:user/mozdef-gene-testuser"
        },
        'qa': {
            "BackupBucketName": "mozdefes2backups",
            "BlocklistBucketName": "mozilla_infosec_blocklist",
            "IPSpaceBucketName": "MISSINGmozdef-gen2-privateIssue147",
            "InfosecQueueArn": "arn:aws:sqs:us-west-1:656532927350:infosec_mozdef_events_non_prod",
            "NubisQueueArn": "arn:aws:sqs:us-west-1:656532927350:nubis_events_non_prod",
            "FxaQueueArn": "arn:aws:sqs:us-west-2:361527076523:fxa-customs-prod",
            "source_arn": "arn:aws:iam::656532927350:user/mozdef"

        }
    }
    environment = request.config.getoption("--environment")
    return environments[environment]