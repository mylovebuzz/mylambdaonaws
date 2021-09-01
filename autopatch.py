import json
import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timedelta
import time

def lambda_handler(event, context):
    # get parameter from event
    sysname = event['sysname']
    topicarn = event['topicarn']
    instancearray = event['instanceids'].split('|')
    commands = event['commands'].split('|')
    ostype = event['ostype'] 

    subject = '[' + sysname + ']' + ' patch start notification'
    message = 'Dear All,\nwe will install latest patch.\nPlease be noted.\n\nThanks & B. R.'
    sendmail(topicarn, subject, message)
    
    createami(instancearray, 'before patch')
    time.sleep(120)
    if ostype == 'windows':
        installwindowsupdate(instancearray)
    else:
        runcommandonec2(instancearray, commands)

    subject = '[' + sysname + ']' + ' patch end notification'
    message = 'Dear All,\nwe have installed latest patch.\nPlease be noted.\n\nThanks & B. R.'
    sendmail(topicarn, subject, message)

    return 0

def sendmail(topicarn, subject, message):
    client = boto3.client('sns')
    try: 
        response = client.publish(
            TopicArn=topicarn,
            Subject=subject,
            Message=message
        )
        return 0
    except ClientError as e:
        print("Failed to send message")

def createami(instancearray, description):
    ec2client = boto3.client("ec2")

    ec2 = boto3.resource("ec2")
    instances = ec2.instances.filter(InstanceIds=instancearray )
    for instance in instances:
        ami = instance.create_image(
        Description=description,
        Name=getaminame(instance),
        NoReboot=False)
        #print('instance is {0}'.format(instance.id))

def getaminame(instance):
    createdate = (datetime.now() + timedelta(hours=8)).strftime("%Y-%m-%d_%H%M%S")
    return "{0}{1}".format(gettagvalue(instance, 'Name'), createdate)

def gettagvalue(instance, key):
    name = [x['Value'] for x in instance.tags if x['Key'] == key]
    return name[0] if len(name) else ''

def runcommandonec2(instancearray, commands):
    ssmclient = boto3.client('ssm')
    response = ssmclient.send_command(
        InstanceIds=instancearray,
        DocumentName='AWS-RunShellScript',
        Parameters={'commands':commands},
    )
#    print('response is {}'.format(response))
    commandid = response['Command']['CommandId']
    print('command id is {0}'.format(commandid))
    time.sleep(60)
    for instanceid in instancearray:
        output = ssmclient.get_command_invocation(CommandId=commandid, InstanceId=instanceid)
        print('instance id {0} command invocation outout is {1}'.format(instanceid, output))
    return 0

def installwindowsupdate(instancearray):
    ssmclient = boto3.client('ssm')
    response = ssmclient.send_command(
        InstanceIds=instancearray,
        DocumentName='AWS-InstallWindowsUpdates',
        TimeoutSeconds=18000,
        Parameters={'Action':['Install'],'AllowReboot':['True'],},
        CloudWatchOutputConfig={'CloudWatchLogGroupName':'wangxianautopatchloggroup', 'CloudWatchOutputEnabled':True, }
    )
    return 0

