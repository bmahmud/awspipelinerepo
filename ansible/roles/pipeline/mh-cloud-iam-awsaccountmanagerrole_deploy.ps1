# aws sso login --profile govpayerroot-w
# Reference: https://docs.aws.amazon.com/cli/latest/reference/cloudformation/deploy/index.html
aws cloudformation deploy `
    --profile govpayerroot-w `
    --stack-name mh-cloud-iam-awsaccountmanagerrole `
    --template-file mh-cloud-iam-awsaccountmanagerrole.yaml `
    --capabilities CAPABILITY_NAMED_IAM