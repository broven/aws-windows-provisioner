# 一键获取 AWS 凭证


## cloudshell


```bash
U="winaws-user-$(date +%s)" && aws iam create-user --user-name $U >/dev/null 2>&1 && aws iam put-user-policy --user-name $U --policy-name WinAWS-Policy --policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":["ec2:*","cloudformation:*"],"Resource":"*"},{"Effect":"Allow","Action":["iam:PassRole"],"Resource":"*","Condition":{"StringEquals":{"iam:PassedToService":"cloudformation.amazonaws.com"}}}]}' >/dev/null 2>&1 && K=$(aws iam create-access-key --user-name $U) && echo "AWS_ACCESS_KEY_ID=$(echo $K | jq -r .AccessKey.AccessKeyId)" && echo "AWS_SECRET_ACCESS_KEY=$(echo $K | jq -r .AccessKey.SecretAccessKey)" && echo "AWS_DEFAULT_REGION=us-east-1"
```
