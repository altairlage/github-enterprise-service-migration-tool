// Import Shared libraries
@Library('Pipeline-Helper')
// Import needed classes
import org.my_org.basefunctions.*
import org.my_org.notifications.*


def githubUser = 'jenkins-user'
def gitHubUrl = "https://<Github url>/My-Org/cje-service-migration-tool.git"

branch = "master"
pipelineHelper = new PipelineHelper()
configureParams()

node('my_node'){

    stage("Checkout"){
        dir("files"){
            pipelineHelper.checkOut(gitHubUrl, branch, githubUser)
        }
    }
  
    stage("Stack Clean-Up"){
        dir("files/stack_deletion"){
            sh "python3 migrate-ghe-repo-webhook.py --ghe-token ${gheToken}"
        }
    }
}

def configureParams() {
    properties(
        [
            [
                $class:'ParametersDefinitionProperty',
                parameterDefinitions: [
                    [
                        $class: 'StringParameterDefinition',
                        name: 'gheToken',
                        description: 'Your GitHub Access Token.',
                        defaultValue: ''
                    ]
                ]
            ]
        ]
    )

    try {
        gheToken = "$gheToken"
    } catch (e) {
        gheToken = ""
    }
}
