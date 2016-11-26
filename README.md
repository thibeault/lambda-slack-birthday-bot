# lambda-slack-birthday-bot

A Slack bot (written in Python for Lambda) that sends out birthday messages to people in your channels/team.

This project is self-contained, so if you follow the instructions, it should work out, however, I'm assuming you already 
know lots about AWS. 

## Outline
The short version goes like this:

- Start an fresh vagrant ubuntu virtual or ubuntu EC2 instance
- On the virtual, setup few tools (python*, pip, git, zip, virtualenv)
- Download the repo and all your python dependencies and create the zip file to be upload to lambda
- Get your Slack API Token
- Create the encrypted key in AWS and encrypt your Token
- Create your Lambda function
- Publish the zip file to AWS Lambda & setup your variables 
- Create a CloudWatch Schedule to trigger every days


## Getting setup

This lambda function has a dependency on the Slack Python-client and before uploading to AWS Lambda, you need to make sure to zip dependant modules.

More info about the slackclient module can be found here: [link](https://github.com/slackhq/python-slackclient)

Start a fresh vagrant ubuntu session, if you don't want to just do this on your workstation, you can also just start a t2.micro ubuntu on AWS. 
```
mkdir vagrant-birthday
cd vagrant-birthday
vagrant init ubuntu/trusty64; vagrant up --provider virtualbox
vagrant ssh
```
Now install all of the Tools
```
sudo apt-get update -y
sudo apt-get install python-pip python-dev build-essential -y
sudo apt-get install git -y
sudo apt-get install zip -y
sudo pip install --upgrade pip
sudo pip install --upgrade virtualenv
cd /vagrant/
```
Download my repo or your's
```
git clone https://github.com/thibeault/lambda-slack-birthday-bot.git
cd lambda-slack-birthday-bot/
virtualenv .
source bin/activate
pip install slackclient
```

Great, now you have to zip up all of the files needed for your lambda function to work. Don't forget to update your 
file.json with your team's birthday, don't forget to add few test users with today and tomorrow's date.

```
zip -9 ../lambda-slack-birthday-bot.zip file.json run.py
cd lib/python2.7/site-packages/
zip -9r ../../../../lambda-slack-birthday-bot.zip requests websocket slackclient
```

Most tutorial will ask you to zip everything from the site-packages folder. I tried to only zip the minimum modules for this simple script to work, if you do more with your code, you may need to grab more modules...

Now your lambda function is ready.

##Slack steps
###Get the Slack API Token

Go to your slack custom Integrations for your team. The URL should look something like this: https://<team name>.slack.com/apps/manage/custom-integrations
Add your Bot configuration, once you setup your bot, you should get the API Token (!!! don't save this value in your repo !!!) I will show you how you can store it encrypted in AWS - Key Management Service

###Invite the Bot to the room you want it to post into

In Slack,
- At the top of the channel, click the Channel Settings icon.
- Select Invite team members to join.
- Select your bot

If you don't do this he won't be able to post in your channel.

##AWS steps
###Create the Lambda execution Role
 As you follow the steps in the console to create a role, note the following:

- In Role Name, use a name that is unique within your AWS account (for example, lambda-execution-role).
- In Select Role Type, choose AWS Service Roles, and then choose AWS Lambda. This grants the AWS Lambda service permissions to assume the role.
- In Attach Policy, choose AWSLambdaExecute.
- Create Role

### Create the KMS key to store the token
It's good practice to not store the token within your code. AWS offer a simple way to store encrypted values. Here how 
to do this with aws cli. (Make sure to have your ~/.aws/config	~/.aws/credentials properly setup)

You should run those command from your workstation where you have your aws credential secure. 

I created a sample "key-policy.json" you will need to replace the following values with the ARN of your account
- \<YOUR AWS ACCOUNT NUMBER>
- \<YOUR ADMIN USER ARN>
- \<YOUR Lambda-execution-role ARN>

It basically give you "ADMIN USER" and your lambda function the ability to encrypt/decrypt the key

```
aws kms create-key --region us-east-1 --description 'Token for BirthDay Lambda function' --policy file://key-policy.json
```
Here the output of the call
```
{
    "KeyMetadata": {
        "Origin": "AWS_KMS", 
        "KeyId": "72ae531b-114f-4082-97f5-7929c1234567", 
        "Description": "Token for BirthDay Lambda function2", 
        "Enabled": true, 
        "KeyUsage": "ENCRYPT_DECRYPT", 
        "KeyState": "Enabled", 
        "CreationDate": 1480110712.342, 
        "Arn": "arn:aws:kms:us-east-1:123456789098:key/72ea432b-423f-5643-97f5-7929c8502391", 
        "AWSAccountId": "123456789098"
    }
}
```
Notice the ARN value returned (arn:aws:kms:us-east-1:123456789098:key/72ea432b-423f-5643-97f5-7929c8502391), copy YOUR's and add it to the cli bellow to create an alias-name
```
aws kms create-alias --region us-east-1 --alias-name alias/slackbirthdaytoken --target-key-id <Replace with your key_id ARN>
```

### Encrypt your slack Token
Make sure to update the following values with yours:
- \<Replace with your key_id ARN>
- \<token>
```
aws kms encrypt --key-id <Replace with your key_id ARN> --region us-east-1 --plaintext "<token>" 
```
You will get a JSON object back with the CiphertextBlob. We will need to add this to environment variable to our lambda function.
Should look like this:
```
{
    "KeyId": "arn:aws:kms:us-east-1:123456789098:key/72ea432b-423f-5643-97f5-7929c8502391", 
    "CiphertextBlob": "AQHACEisggtsDJbSubZaM6a91iKXumu3+gW8D3V2xQbJNramxwAAAIkwgYYGCSqGSIb3DQEHBqB5MHcCAQAwcgYJKoZIhvcNAQcBMB4GCWCGSAFlAwQBLjARBAy+DpUJ/AnfYvmGNpYCARCARf+G5wGxqxq9IxOZomAc0gjvplMEU6IVr2OM47cZqGAUuUnIZaIU/Y5VNPAaFpHOYf6todjcKevwPQptSwW9RIxJT0yHkA=="
}
```



###Create the Lambda function

Make sure to replace 
- \<file-path> with the path to your zip created earlier
- \<role-arn> with the arn of the Role you created, should look similar of this: arn:aws:iam::123456789098:role/Lambda-execution-role
- \<your aws cli profile>, this is the profile name in your ~/.aws/credentials where you store your access key id and Secret Access key (don't store this in your git repo)
```
aws lambda create-function \
--region us-east-1 \
--function-name slack-birthday \
--zip-file fileb://<file-path>/lambda-slack-birthday-bot.zip \
--role <role-arn> \
--handler run.lambda_handler \
--runtime python2.7 \
--timeout 3 \
--memory-size 128
```
Should get a response looking like this: 
```
{
    "CodeSha256": "OBOFFNfTeR8tAu/X1yq01xFClgFaFl1JM+2haDVeAhw=", 
    "FunctionName": "slack-birthday", 
    "CodeSize": 1256343, 
    "MemorySize": 128, 
    "FunctionArn": "arn:aws:lambda:us-east-1:123456789098:function:slack-birthday", 
    "Version": "$LATEST", 
    "Role": "arn:aws:iam::123456789098:role/Lambda-execution-role", 
    "Timeout": 3, 
    "LastModified": "2016-11-25T21:09:20.188+0000", 
    "Handler": "run.handler", 
    "Runtime": "python2.7", 
    "Description": "Slack Birthday Bot function"
}
```

### How to update lambda function:
Now since our function is very small, the console allow us to edit it on the web. If you zip everything from the site-packages folder
your zip would be too big to edit online. You would then have to run the following cli to update it.
```
aws lambda update-function-code --function-name slack-birthday --zip-file fileb://lambda-slack-birthday-bot.zip 
```

###Add 2 environments variables to your Lambda function
- Login to your console and go to: Lambda -> Functions -> slack-birthday
- Bellow the code, you should see: Environment variables: Key   -  Value
- Add the kmsEncryptedToken & slackChannel
- click on Save at the top

```
kmsEncryptedToken=\<the value of your CiphertextBlob you got when encrypting your token>
slackChannel=\<The Channel you added your bot>
```

### Test your lambda function
- Login to your console and go to: Lambda -> Functions -> slack-birthday
- Click on Test or Save & Test. This should 
- The function should return the system datetime
```
"2016-11-26 05:49:44.957160"
```
If you updated the file.json with your team members birthdays and today is one of the members birthday, you would see this 
message posted in the channel. You should add 2 member with today and tomorrow in your file for testing...
```
Bonne fete @ted :birthday:. De tout les Snoro :-)
```

### Create your CloudWatch Trigger Schedule
- Login to your console and go to: Lambda -> Functions -> slack-birthday
- Click on "Triggers"
- Click on "Add trigger"
- Click on the box on the left of Lambda
- Select: "CloudWatch Events - Schedule"
- Rule name: Daily
- Rule description: Run Every day
- Schedule expression: rate(1 day)