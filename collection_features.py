#!/usr/bin/env python3

"""Use the function-calling API to extract features from specimen
descriptions.

Requires the AZURE_OPENAI_API_KEY environment variable to be set.
"""

import sys
import argparse
import netrc
from functools import partial
import json
import os
import pprint
from itertools import islice
from operator import itemgetter
from pathlib import Path

import lxml.html
from jinja2 import Template

# import pandas as pd

from openai import OpenAI, AzureOpenAI


html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Minimal HTML5 Template with Table</title>
</head>
<body>
    <table border="1" style="border-collapse: collapse;">
        <thead>
          <tr>
            {% for key in keys %}
            <th>{{ key }}</th>
            {% endfor %}
          </tr>
        <tbody>
        {% for row in rows %}
          <tr>
            {% for key in keys %}
            <td>{{ row[key] }}</td>
            {% endfor %}
          </tr>
          {% endfor %}
       </tbody>
    </table>
</body>
</html>
"""

functions = [
    {
        'name': 'extract_collection_details',
        'description': """Extract details about specimens and
             container types for clinical laboratory teting from a
             collection description. Containers are often identified
             by color. Examples of onsite locations include UW-MT,
             UWMC, HMC. Provide an empty string for missing values.""",
        'parameters': {
            'type': 'object',
            'properties': {
                'specimen_type': {
                    'type': 'string',
                    'enum': ['blood', 'arterial blood', 'venous blood',
                             'cord blood', 'urine', 'stool', 'fluid', 'other'],
                    'description': 'The type of specimen.'
                },
                'onsite_preferred': {
                    'type': 'string',
                    'description': """The preferred type of
                        container for onsite locations or if location
                        is not specified. Do not include blood volume."""
                },
                'offsite_preferred': {
                    'type': 'string',
                    'description': """The preferred type of container
                        for other locations and clinics. Leave blank
                        if location is not specified. Do not include
                        blood volume."""
                },
                'acceptable': {
                    'type': 'string',
                    'description': """Acceptable container types for
                        onsite locations or if location is not
                        specified. Do not include blood volume."""
                },
                'pediatric': {
                    'type': 'string',
                    'description': """Description of pediatric specimens."""
                },
                'unacceptable': {
                    'type': 'string',
                    'description': """Unacceptable specimens."""
                },
                'notes': {
                    'type': 'string',
                    'description': """Any additional notes or information."""
                },
            },
            'required': ['specimen_type', 'onsite_preferred'],
        }
    }
]


def get_response(client, text, model="gpt-3.5-turbo-1106"):

    azure_deployments = {
        'gpt-3.5-turbo-1106': 'gpt-35-turbo-1106',
        'gpt-4-1106-preview': 'gpt-4-1106-preview',
    }

    try:
        response = client.chat.completions.create(
            model = azure_deployments[model],
            messages = [{'role': 'user', 'content': text}],
            functions = functions,
            function_call = 'auto'
        )

        return json.loads(
            response.choices[0].message.function_call.arguments)
    except Exception as e:
        print(f"Error: {e}")
        print(text)
        return {}


def clean_html(text: str) -> str:
    """Remove HTML tags from text."""
    output = lxml.html.fromstring(text).text_content()
    return output.replace('\r', '\n')


def get_features(client: str, mnemonic: str, text: str,
                 model: str, cache_dir: Path,
                 use_cache: bool = True):
    cache_file = cache_dir / f"{mnemonic}-{model}.json"
    if cache_file.exists():
        return json.loads(cache_file.read_text())
    else:
        details = get_response(client, text, model)
        # don't cache empty results
        if use_cache and details:
            with open(cache_file, "w") as f:
                json.dump(details, f)

        return details


def main(arguments):

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('infile', help="jsonl input file",
                        type=argparse.FileType())
    parser.add_argument('-n', '--column-name', default='text',
                        help="Name of column containing text")
    parser.add_argument('-o', '--outfile', type=argparse.FileType('w'),
                        help="Output file")
    parser.add_argument('-d', '--cache-dir', default='cache',
                        help="Directory to store cached results")
    parser.add_argument('-r', '--max-rows', type=int, default=None,
                        help="Maximum number of rows to process")
    parser.add_argument('-m', '--model', default='gpt-3.5-turbo-1106',
                        choices=['gpt-3.5-turbo-1106', 'gpt-4-1106-preview'],
                        help="Model to use for the assistant")
    parser.add_argument('--no-cache', action='store_false', dest='use_cache',
                        default=True, help="Don't cache results in files")

    args = parser.parse_args(arguments)

    # assume api key defined in environment as AZURE_OPENAI_API_KEY
    client = AzureOpenAI(
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        api_version="2024-02-15-preview",
        azure_endpoint="https://openai.dlmp.uw.edu",
    )

    cache_dir = Path(args.cache_dir)
    cache_dir.mkdir(exist_ok=True, parents=True)

    sort_keys = ['dept_name', 'specimen_type', 'onsite_preferred']
    missing_features = {k: '' for k in sort_keys}

    text_cache = {}
    rows = []
    for line in islice(args.infile.readlines(), args.max_rows):
        if line.strip():
            d = json.loads(line)

            ok = {'LI', 'CKMAC', 'OBGPP1', 'C3', 'PSA', 'PG', 'FTDIL',
                  'GENTAP', 'TROPIG', 'VPA', 'BMPICR', 'BMP'}
            ok = {'BMP', 'BMPICR'}

            if d['mnemonic'] not in ok:
                continue

            d.update(missing_features)
            text = clean_html(d['collection'])
            print(d['mnemonic'], d['name'])

            text_flat = ' '.join(text.split())
            if text_flat in text_cache:
                print(f"Using cached value for {d['mnemonic']}")
                details = text_cache[text_flat]
            else:
                details = get_features(
                    client,
                    mnemonic=d['mnemonic'],
                    text=text,
                    model=args.model,
                    cache_dir=cache_dir,
                    use_cache=args.use_cache,
                )
                text_cache[text_flat] = details

        rows.append(dict(d, **details))

    keys = list(d.keys())[1:] + list(functions[0]['parameters']['properties'].keys())

    if args.outfile:
        rows.sort(key=itemgetter(
            'dept_name', 'specimen_type', 'onsite_preferred'))
        args.outfile.write(
            Template(html_template).render(keys=keys, rows=rows))


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

