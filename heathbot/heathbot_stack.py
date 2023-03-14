from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_events as events,
    aws_events_targets as event_targets,
)
from constructs import Construct
import configparser


class HeathbotStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        config = configparser.ConfigParser()
        config.read("heathbot/config.ini")
        # The code that defines your stack goes here

        # create iam role for running lambdas
        heathbot_lambda_role = iam.Role(
            scope=self,
            id="heathbot-lambda-role",
            role_name="heathbot-lambda-role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AWSLambda_FullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                ),
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "SecretsManagerReadWrite"
                ),
            ],
        )

        # lambda function posts heathcliff comic
        heathbot_lambda = _lambda.DockerImageFunction(
            scope=self,
            id="heathbot-lambda",
            code=_lambda.DockerImageCode.from_image_asset(directory="heathbot/lambda/"),
            role=heathbot_lambda_role,
            memory_size=(1024),
            timeout=Duration.minutes(15),
        )

        # # lambda on cron to post daily
        modeling_lambda_rule = events.Rule(
            scope=self,
            id="modeling-lambda-rule",
            schedule=events.Schedule.cron(minute="0", hour="14"),
            targets=[event_targets.LambdaFunction(handler=heathbot_lambda)],
        )
