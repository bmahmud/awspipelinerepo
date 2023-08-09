 
mh-cloud-codepipeline-awsaccountmgr_deploy.ps1
# aws sso login --profile govsharedprod-w
# Reference: https://docs.aws.amazon.com/cli/latest/reference/cloudformation/deploy/index.html
aws cloudformation deploy `
    --profile govsharedprod-w `
    --stack-name mh-cloud-codepipeline-awsaccountmgr `
    --template-file mh-cloud-codepipeline-awsaccountmgr.yaml `
    --capabilities CAPABILITY_NAMED_IAM