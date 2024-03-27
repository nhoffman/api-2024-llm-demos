#!/usr/bin/env python3

"""Create an OpenAI assistant

https://platform.openai.com/docs/assistants/tools/knowledge-retrieval
"""

import os
import sys
import argparse
from pathlib import Path
import pprint

from openai import OpenAI


def main(arguments):

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('name', help="Name of the assistant")
    parser.add_argument(
        '-f', '--filenames', nargs='+',
        help="One or more files to associate with the assistant")
    parser.add_argument('-m', '--model', default='gpt-3.5-turbo',
                        choices=['gpt-3.5-turbo', 'gpt-4-turbo-preview'],
                        help="Model to use for the assistant")

    args = parser.parse_args(arguments)
    client = OpenAI()

    asst_name = f'{args.name}_{args.model}'

    existing_files = {f.filename: f for f in client.files.list(purpose='assistants')}

    file_ids = []
    for fname in args.filenames:
        if fname in existing_files:
            print(f"File {fname} already uploaded")
            file_ids.append(existing_files[fname].id)
        else:
            print(f"Uploading {fname}")
            uploaded = client.files.create(
                file=open(fname, "rb"),
                purpose='assistants'
            )
            file_ids.append(uploaded.id)

    existing_assistants = {a.name: a for a in client.beta.assistants.list()}
    if asst_name in existing_assistants:
        print(f"Assistant {asst_name} already exists")
        assistant = client.beta.assistants.retrieve(
            assistant_id=existing_assistants[asst_name].id)
    else:
        print(f"Creating assistant {asst_name}")
        assistant = client.beta.assistants.create(
            name=asst_name,
            instructions="""You are a chatbot answering questions
            about the provided files. Use your knowledge base to best
            respond to queries. Avoid providing reponses that are not
            based on your knowledge base.""",
            model=args.model,
            tools=[{"type": "retrieval"}],
            file_ids=file_ids
        )

    pprint.pprint(assistant.model_dump())


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

