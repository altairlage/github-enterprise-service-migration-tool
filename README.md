# Tool for migrating the deprecated Github Enterprise Jenkins service/webhook 

This tool fetches all GHE orgs defined repos deleting the deprecated service and creates a new GitHub webhook on the code repos.

1. Get the list of repos for each GHE org;
1. Define the Jenkins master for each org;
1. For each repo it
	1. Get the deprecated Jenkins service hook (if it exists)
	1. Delete the deprecated Jenkins service hook (if it exists)
	1. Create the new GitHub webhook based on the CJE master
1. Print a list of links for the Jenkins service hooks that couldn´t be deleted (Link direct to the 'Integration and services' page under the repo config page)
1. Print a list of links for the new GitHub webhooks that couldn´t be created (Link direct to the 'Webhooks' page under the repo config page)
