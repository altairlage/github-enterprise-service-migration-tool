import requests
import json
import argparse
import logging

parser = argparse.ArgumentParser()
parser.add_argument(
    '--ghe-token', '-gt',
    type=str,
    required=True,
    help='GitHub Access token'
)

github_api_url = "https://<my_github_server>/api/v3"

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

# Substring exclusion. Repos containing these subs will not have hooks migrated
prefixes = ['-aws', '-deploy', '-infra']

ghe_orgs = [
    'My-git-org',
    'My-git-org2'
]

creation_failures = []
deletion_failures = []


def main():
    args = parser.parse_args()
    ghe_access_token = args.ghe_token

    global headers
    headers = {'Authorization': 'token ' + ghe_access_token, 'Accept': 'application/vnd.github.loki-preview+json'}

    for org in ghe_orgs:
        logging.info("\n\n\n\n")
        logging.info("============================== STARTING MIGRATION FOR ORG {} SERVICES ==============================".format(org))
        cje_master = get_cje_master_by_org(org)
        logging.info("**** CJE Master for org {}: {}".format(org, cje_master))

        repo_list = get_code_repos_list(org)
        logging.info("**** Org {} repo list:".format(org))
        logging.info(repo_list)
        
        migrate_jenkins_hooks(cje_master, org, repo_list)
        logging.info("============================== FINISHED MIGRATION FOR ORG {} SERVICES ==============================".format(org))

    logging.info("\n\n")
    logging.info("============================================= ERRORS: =============================================\n")
    
    logging.info("\n")
    logging.info("---- The following repos must have CJE service deleted manually:")
    for repo_link in deletion_failures:
        logging.info("- {}".format(repo_link))

    logging.info("\n\n")
    logging.info("---- The following repos must have GHE webhook created manually:")
    for repo_link in creation_failures:
        logging.info("- {}".format(repo_link))


def get_cje_master_by_org(org):
    if org == 'MyOrg':
        return 'my-jenkins-master'
    else:
        return 'my-other-jenkins-master'


def get_code_repos_list(org_name):
    global headers

    pull_url = github_api_url + "/orgs/" + org_name + "/repos"
    payload = {
        "type": "all"
    }

    repo_list = []
    pull_response = requests.get(pull_url, headers=headers, json=payload)
    response_json = pull_response.json()
    
    for item in response_json:
        if not any(substring in item['name'] for substring in prefixes):
            repo_list.append(item["name"])
    
    while 'next' in pull_response.links.keys():
        pull_response = requests.get(pull_response.links['next']['url'], headers=headers, json=payload)
        response_json = pull_response.json()
        for item in response_json:
            if not any(substring in item['name'] for substring in prefixes):
                repo_list.append(item["name"])
    
    return repo_list


def migrate_jenkins_hooks(cje_master, org, repo_list):
    for repo in repo_list:
        logging.info("\n\n")
        logging.info("---- Migrating CJE service in repo {}/{} ----".format(org, repo))

        hook_id = get_cje_repo_webhook(org, repo)
        if hook_id > 0:
            delete_cje_service(org, repo, hook_id)
        else:
            logging.info("CJE/GHE service hook not found for repo {}/{}. Skipping CJE service deletion.".format(org, repo))
        
        if(ghe_webhook_exists(cje_master, org, repo) is False):
            create_repo_webhook(cje_master, org, repo)
        else:
            logging.info("New GitHub webhook already exist in repo {}/{}. Skipping new webhook creation.".format(org, repo))


def print_json(json_obj):
    logging.info(json.dumps(json_obj, indent=4))


def get_cje_repo_webhook(org, repo_name):
    global headers

    hooks_url = github_api_url + "/repos/{}/{}/hooks".format(org, repo_name)
    hooks_response = requests.get(hooks_url, headers=headers)
    response_json = hooks_response.json()
    
    if  len(response_json) > 0:
        logging.info("Searching for CJE/GHE service hook for repo {}/{}:".format(org, repo_name))
        for item in response_json:
            if item['name'] == 'jenkinsgit' and item['type'] == 'Repository' and item['config']['jenkins_url']:
                logging.info("CJE/GHE service hook found for repo {}. Hook id: {}".format(repo_name, item['id']))
                return item['id']
    
    return 0


def delete_cje_service(org, repo_name, hook_id):
    global headers

    logging.info("Deleting hook for repo {}, hook id: {}".format(repo_name, hook_id))

    delete_url = github_api_url + "/repos/{}/{}/hooks/{}".format(org, repo_name, hook_id)
    delete_reponse = requests.delete(delete_url, headers=headers)
    if delete_reponse.status_code in [200, 204]:
        logging.info("Deleted hook for repo {}, hook id: {} with success!".format(repo_name, hook_id))
        return True

    logging.info("Error deleting hook for repo {}, hook id: {}! Delete it manually.".format(repo_name, hook_id))
    deletion_failures.append("https://<Github url>/{}/{}/settings/installations".format(org, repo_name))
    return False
    

def ghe_webhook_exists(cje_master, org, repo_name):
    global headers

    hooks_url = github_api_url + "/repos/{}/{}/hooks".format(org, repo_name)
    hooks_response = requests.get(hooks_url, headers=headers)
    response_json = hooks_response.json()
    hook_exists = False

    if  len(response_json) > 0:
        logging.info("Checking if new GitHub Webhook already exists in repo {}/{}:".format(org, repo_name))
        
        for item in response_json:
            hook_url = "https://<Github url>/{}/git/notifyCommit?url=https://<Github url>/{}/{}".format(cje_master, org, repo_name)
            if item['name'] == 'web' and item['config']['url'] == hook_url:
                hook_exists = True
    
    return hook_exists


def create_repo_webhook(cje_master, org, repo_name):
    global headers

    payload = {
        "name": "web",
        "active": True,
        "events": [
            "push"
        ],
        "config": {
            "url": "https://<Github url>/{}/git/notifyCommit?url=https://<Github url>/{}/{}".format(
                cje_master, org, repo_name
            ),
            "content_type": "json",
            "insecure_ssl": "0"
        }
    }

    logging.info("Creating webhook for repo {}/{}".format(org, repo_name))

    hooks_url = github_api_url + "/repos/{}/{}/hooks".format(org, repo_name)
    hooks_response = requests.post(hooks_url, headers=headers, json=payload)
    
    if(hooks_response.status_code in [200, 201]):
        logging.info("Webhook for repo {}/{} - Created with success!".format(org, repo_name))
        return True
    else:
        logging.info("Webhook for repo {}/{} - Error during creation! Create manually!".format(org, repo_name))
        creation_failures.append("https://<Github url>/{}/{}/settings/hooks".format(org, repo_name))
        return False

        
if __name__ == '__main__':
    main()
