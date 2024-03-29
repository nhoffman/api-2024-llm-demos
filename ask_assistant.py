#!/usr/bin/env python3

"""Ask an assistant a question

https://platform.openai.com/docs/assistants/tools/knowledge-retrieval
https://cookbook.openai.com/examples/assistants_api_overview_python

Requires the OPENAI_API_KEY environment variable to be set.
"""

import os
import sys
import argparse
from pathlib import Path
import pprint
import time
import json

from openai import OpenAI


def show_json(obj):
    print(json.loads(obj.model_dump_json()))


def wait_on_run(client, run, thread):
    while run.status == "queued" or run.status == "in_progress":
        print(f'{run.status}')
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id,
        )
        time.sleep(0.5)
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

    thread = client.beta.threads.create()
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role='user',
        content=args.question,
    )

    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id,
    )

    run = wait_on_run(client, run, thread)

    messages = client.beta.threads.messages.list(
        thread_id=thread.id, order="asc", after=message.id
    )
    show_json(messages)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

