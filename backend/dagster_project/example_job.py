from dagster import job, op

@op
def say_hello():
    return "Hello, Dagster!"

@job
def hello_job():
    say_hello()
