import boto3
import time

def lambda_handler(event, context):
    ssmclient = boto3.client('ssm')
    response = ssmclient.send_command(
        InstanceIds=['i-xxxxx',],
        DocumentName='AWS-RunShellScript',
        Parameters={'commands':['/root/sendstartpatchmail.sh',]},
    )
#    print('response is {}'.format(response))
    commandid = response['Command']['CommandId']
    print('command id is {}'.format(commandid))
    time.sleep(5)
    output = ssmclient.get_command_invocation(CommandId=commandid,
        InstanceId='i-xxxxx',
    )
    print('instance id i-xxxxx command invocation outout is {}'.format(output))
    return 0
    
