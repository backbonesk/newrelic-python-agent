// Grab will no longer be supported in jenkins-dsl 1.36, we currently use 1.35
@Grab('org.yaml:snakeyaml:1.17')
import org.yaml.snakeyaml.Yaml
import newrelic.jenkins.extensions

String organization = 'python-agent'
String repoGHE = 'python_agent'
String repoFull = "${organization}/${repoGHE}"
String testSuffix = "__docker-test"
String slackChannel = '#python-agent'

def yaml = new Yaml()
List<String> disabledList = yaml.load(readFileFromWorkspace('jenkins/test-pipeline-config.yml')).disable

def getPacknsendTests = {
    // Get list of lists. Each item represents a single test. For example:
    // [framework_django_tox.ini__docker_test, tests/framework_django/tox.ini, true]
    // Where the first item is the name of the test, the second is the path to
    // the tox file relative to the job's workspace, and the third is if the
    // test is disabled or not.
    def packnsendTestsList = []
    new File("${WORKSPACE}/tests").eachDir() { dir ->
        String dirName = dir.getName()
        dir.eachFileMatch(~/tox.*.ini/) { toxFile ->
            String toxName = toxFile.getName()
            String toxPath = "tests/${dirName}/${toxName}"
            String testName = "${dirName}_${toxName}_${testSuffix}"
            String disable = toxPath in disabledList
            def test = [testName, toxPath, disable]
            packnsendTestsList.add(test)
        }
    }
    packnsendTestsList
}


use(extensions) {
    def packnsendTests = getPacknsendTests()

    view('PY_Tests', 'Test jobs',
         "(_PYTHON-AGENT-DOCKER-TESTS_)|(.*${testSuffix})|(oldstyle.*)")

    multiJob('_PYTHON-AGENT-DOCKER-TESTS_') {
        description('Perform full suite of tests on Python Agent')
        logRotator { numToKeep(10) }
        triggers { cron('H 10 * * *') }
        label('py-ec2-linux')
        publishers {
            extendedEmail('python-agent-dev@newrelic.com')
        }

        parameters {
            stringParam('GIT_REPOSITORY_BRANCH', 'develop',
                        'Branch in git repository to run test against.')
            stringParam('AGENT_FAKE_COLLECTOR', 'false',
                        'Whether fake collector is used or not.')
            stringParam('AGENT_PROXY_HOST', '',
                        'URI for location of proxy. e.g. http://proxy_host:proxy_port')
        }

        steps {
            phase('tox-tests', 'COMPLETED') {
                for (test in packnsendTests) {
                    job(test[0]) {
                        killPhaseCondition('NEVER')
                    }
                }
            }
        }

        slack(slackChannel){
            notifySuccess true
        }
    }

    // create all packnsend base tests
    packnsendTests.each { testName, toxPath, disableTest ->
        baseJob(testName) {
            label('py-ec2-linux')
            repo(repoFull)
            branch('${GIT_REPOSITORY_BRANCH}')

            configure {
                description("Run tox file ${toxPath}")
                logRotator { numToKeep(10) }
                blockOnJobs('.*-Reset-Nodes')

                wrappers {
                    timeout {
                        // abort if time is > 500% of the average of the
                        // last 3 builds, or 60 minutes
                        elastic(500, 3, 60)
                        abortBuild()
                    }
                }

                parameters {
                    stringParam('GIT_REPOSITORY_BRANCH', 'develop',
                                'Branch in git repository to run test against.')
                    stringParam('AGENT_FAKE_COLLECTOR', 'true',
                                'Whether fake collector is used or not.')
                    stringParam('AGENT_PROXY_HOST', '',
                                'URI for location of proxy. e.g. http://proxy_host:proxy_port')
                }

                steps {
                    environmentVariables {
                        env('NEW_RELIC_DEVELOPER_MODE', '${AGENT_FAKE_COLLECTOR}')
                        env('NEW_RELIC_PROXY_HOST', '${AGENT_PROXY_HOST}')
                        // dogestry creds
                        env('AWS_ACCESS_KEY_ID', '${NR_DOCKER_DEV_ACCESS_KEY_ID}')
                        env('AWS_SECRET_ACCESS_KEY', '${NR_DOCKER_DEV_SECRET_ACCESS_KEY}')
                        env('DOCKER_HOST', 'unix:///var/run/docker.sock')
                    }
                    shell('./jenkins/prep_node_for_test.sh')
                    shell("./docker/packnsend run tox -c ${toxPath}")
                }
            }
        }
    }

    ['develop', 'master', 'pullrequest'].each { jobType ->
        jaasBaseJob("oldstyle-tests-${jobType}") {
            label('py-ec2-linux')
            description('Run the old style tests (i.e. ./tests.sh)')
            logRotator { numToKeep(10) }
            blockOnJobs('.*-Reset-Nodes')

            wrappers {
                timeout {
                    // abort if time is > 500% of the average of the
                    // last 3 builds, or 60 minutes
                    elastic(500, 3, 60)
                    abortBuild()
                }
            }

            if (jobType == 'pullrequest') {
                repositoryPR(repoFull)
                triggers {
                    // run for all pull requests
                    pullRequest {
                        permitAll(true)
                        useGitHubHooks()
                    }
                }
            }
            else {
                repository(repoFull, jobType)
                triggers {
                    // trigger on push to develop/master
                    githubPush()
                }
            }

            steps {
                environmentVariables {
                    env('DOCKER_HOST', 'unix:///var/run/docker.sock')
                }
                shell('./jenkins/prep_node_for_test.sh')
                shell('./build.sh')
                shell('./docker/packnsend run /data/tests.sh')
            }

            slackQuiet(slackChannel) {
                notifySuccess true
            }
        }
    }
}
