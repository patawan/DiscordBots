import random


def change_schedule(event, context):
    wait_seconds = random.randint(0, 86400)
    return wait_seconds
