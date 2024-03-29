#!/usr/bin/env python3

"""Ask an assistant a question

https://platform.openai.com/docs/assistants/tools/knowledge-retrieval
https://cookbook.openai.com/examples/assistants_api_overview_python

Requires the OPENAI_API_KEY environment variable to be set.

TODO: streaming.
See https://medium.com/@hawkflow.ai/openai-streaming-assistants-example-77e53ca18fb4
"""

import os
import sys
import argparse
from pathlib import Path
import pprint
import time

from openai import OpenAI


def pretty_print(messages):
    print("# Messages")
    for m in messages:
        print(f"{m.role}: {m.content[0].text.value}")
    print()


def submit_message(client, assistant_id, thread, user_message):
    client.beta.threads.messages.create(
        thread_id=thread.id, role="user", content=user_message
    )
    return client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id,
    )

def get_response(client, thread):
    return client.beta.threads.messages.list(thread_id=thread.id, order="asc")


def create_thread_and_run(client, assistant_id, user_input):
    thread = client.beta.threads.create()
    run = submit_message(client, assistant_id, thread, user_input)
    return thread, run


def wait_on_run(client, run, thread, delay=0.5):
    while run.status == "queued" or run.status == "in_progress":
        print(f'{run.status}')
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id,
        )
        time.sleep(delay)
    return run


def main(arguments):

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('name', help="Name of the assistant", nargs='?')
    parser.add_argument('-m', '--model', default='gpt-3.5-turbo',
                        choices=['gpt-3.5-turbo', 'gpt-4-turbo-preview'],
                        help="Model to use for the assistant")
    parser.add_argument('-q', '--question', help="Question to ask")

    args = parser.parse_args(arguments)
    client = OpenAI()

    assistants = {a.name: a for a in client.beta.assistants.list()}
    if args.name is None or args.question is None:
        print(parser.format_help())
        print("Assistants:", list(assistants.keys()))
        return

    assistant = client.beta.assistants.retrieve(
        assistant_id=assistants[args.name].id)

    thread, run = create_thread_and_run(client, assistant.id, args.question)
    run = wait_on_run(client, run, thread)
    pretty_print(get_response(client, thread))


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

