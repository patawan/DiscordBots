#!/usr/bin/env python3
import os
import aws_cdk as cdk
from heathbot.heathbot_stack import HeathbotStack


app = cdk.App()
HeathbotStack(
    scope=app,
    construct_id="HeathbotStack",
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"), region=os.getenv("CDK_DEFAULT_REGION")
    ),
)

app.synth()
