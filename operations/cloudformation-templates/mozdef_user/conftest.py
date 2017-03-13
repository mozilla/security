import pytest

ENVIRONMENTS = {
    'prod': {
        "BackupBucketName": "mozdefes2backups",
        "NewProdBackupBucketName": "mozdef-prod-es2-backups",
        "BlocklistBucketName": "mozilla_infosec_blocklist",
        "IPSpaceBucketName": "mozilla-ipspace",
        "InfosecQueueArn": "arn:aws:sqs:us-west-1:656532927350:infosec_mozdef_events",
        "MIGQueueArn": "arn:aws:sqs:us-west-2:371522382791:mig-log-sqs",
        "NubisQueueArn": "arn:aws:sqs:us-west-1:656532927350:nubis_events_prod",
        "FxaQueueArn": "arn:aws:sqs:us-west-2:361527076523:fxa-customs-prod",
        "source_arn": "arn:aws:iam::371522382791:user/mozdef/mozdef-prod"
    },
    'qa': {
        "BackupBucketName": "mozdefes2backups",
        "NewProdBackupBucketName": "inapplicable-temporary-bucket-name-see-bug1346391",
        "BlocklistBucketName": "mozilla_infosec_blocklist",
        "IPSpaceBucketName": "mozilla-ipspace",
        "InfosecQueueArn": "arn:aws:sqs:us-west-1:656532927350:infosec_mozdef_events_non_prod",
        "MIGQueueArn": "arn:aws:sqs:us-west-2:656532927350:mig-log-sqs",
        "NubisQueueArn": "arn:aws:sqs:us-west-1:656532927350:nubis_events_non_prod",
        "FxaQueueArn": "arn:aws:sqs:us-west-2:361527076523:fxa-customs-prod",
        "source_arn": "arn:aws:iam::656532927350:user/mozdef/mozdef-qa"
    }
}

ENVIRONMENT_CHOICES = ['prod', 'qa']

def pytest_addoption(parser):
    parser.addoption(
        "--environment",
        choices=ENVIRONMENT_CHOICES,
        default=ENVIRONMENT_CHOICES[0])

@pytest.fixture
def config(request):
    environment = request.config.getoption("--environment")
    result = ENVIRONMENTS[environment]
    result['environment_name'] = environment
    result['environment_name_list'] = ENVIRONMENT_CHOICES
    result['all_environments'] = ENVIRONMENTS
    return result
