from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_events as events,
    aws_events_targets as event_targets,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
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

        # lambda function to change wait timer of sfn
        heathbot_schedule_lambda = _lambda.Function(
            scope=self,
            id="schedule-lambda",
            function_name="heathbot-schedule",
            code=_lambda.Code.from_asset(path="heathbot/lambda/schedule_change/"),
            handler="schedule_change.change_schedule",
            runtime=_lambda.Runtime.PYTHON_3_8,
            role=heathbot_lambda_role,
            memory_size=(128),
            timeout=Duration.minutes(3),
        )

        # lambda function posts heathcliff comic
        heathbot_post_lambda = _lambda.DockerImageFunction(
            scope=self,
            id="heathbot-lambda",
            function_name="heathbot-post",
            code=_lambda.DockerImageCode.from_image_asset(
                directory="heathbot/lambda/bot_post/"
            ),
            role=heathbot_lambda_role,
            memory_size=(1024),
            timeout=Duration.minutes(15),
        )

        start_execution = tasks.LambdaInvoke(
            scope=self,
            id="start-execution",
            lambda_function=heathbot_schedule_lambda,
            # Lambda's result is in the attribute wait_time
            output_path="$.wait_seconds",
        )

        wait_x = sfn.Wait(
            scope=self, id="wait-time", time=sfn.WaitTime.seconds_path("$.wait_seconds")
        )

        heathbot_post = tasks.LambdaInvoke(
            scope=self,
            id="heathbot-post",
            lambda_function=heathbot_post_lambda,
        )

        sfn_definition = start_execution.next(wait_x).next(heathbot_post)

        heathbot_sfn = sfn.StateMachine(
            scope=self,
            id="heathbot-sfn",
            definition=sfn_definition,
        )

        # schedule sfn
        # runs at midnight AZ time every day
        triggering_sfn_rule = events.Rule(
            scope=self,
            id="schedule-sfn-rule",
            schedule=events.Schedule.cron(minute="0", hour="07"),
            targets=[
                event_targets.SfnStateMachine(
                    machine=heathbot_sfn, role=heathbot_sfn.role
                )
            ],
        )
