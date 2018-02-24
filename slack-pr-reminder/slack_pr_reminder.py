from datetime import datetime
import requests
from github import Github
import yaml


with open('config.yaml') as f:
    config = yaml.load(f)

github = Github(config['github_access_token'])


def get_slack_username(user):
    if user in config['users']:
        return '@' + config['users'][user]
    return user


def get_pull_requests():
    pull_requests_by_repo = [get_pull_requests_for_repo(repo) for repo in config['repositories']]
    pull_requests = [pr for repo in pull_requests_by_repo for pr in repo]
    return pull_requests


def get_pull_requests_for_repo(repo_name):
    repo = github.get_repo(repo_name)
    pull_requests = repo.get_pulls()
    return list(pull_requests)


def format_message(pull_requests):
    count = len(pull_requests)
    if count == 1:
        msg = 'There is *1* pull request waiting for review: '
    else:
        msg = 'There are *' + str(count) + '* pull requests waiting for review: '
    msg += '\n'
    msg += ''.join(format_pull_request(pr) for pr in pull_requests)
    return msg


def format_pull_request(pull_request):
    review_requests = list(pull_request.get_reviewer_requests())
    reviewers_list = ', '.join(get_slack_username(r.login) for r in review_requests)
    
    age = (datetime.now() - pull_request.created_at).days
    if age == 0:
        emoji = ' :new:'
    elif age >= 14:
        emoji = ':bangbang:'
    elif age >= 7:
        emoji = ':exclamation:'
    else:
        emoji = ''

    result = '\n* {2} <{0}|{1}> by _{3}_'.format(pull_request.html_url, pull_request.title, emoji, pull_request.user.name)
    
    if reviewers_list:
        if len(review_requests) == 1:
            result += '. Reviewer: ' + reviewers_list
        else:
            result += '. Reviewers: ' + reviewers_list
    
    return result


def send_to_slack(message):
    payload = {
        'text': message,
        'icon_emoji': ':mailbox_with_mail:',
        'username': 'Pull Request Reminder',
        'link_names': '1'
    }
    response = requests.post(config['slack_webhook_url'], json=payload)


def send_reminder():
    pull_requests = get_pull_requests()
    if not pull_requests:
        return
    message = format_message(pull_requests)
    print(message)
    send_to_slack(message)


if __name__ == '__main__':
    send_reminder()
