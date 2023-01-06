import datetime
from textwrap import dedent
import sys
import re

from redmail import EmailSender

import pytest

from convert import remove_extra_lines, payloads_to_dict
from getpass import getpass, getuser
from platform import node

from convert import remove_email_extra, remove_email_content_id, prune_generated_headers

import platform
PYTHON_VERSION = sys.version_info
IS_PY37 = sys.version_info < (3, 8)

def test_date():
    format = "%a, %d %b %Y %H:%M:%S -0000"
    email = EmailSender(host=None, port=1234)

    before = datetime.datetime.now(datetime.timezone.utc)
    msg = email.get_message(sender="me@example.com", subject="Some email")
    after = datetime.datetime.now(datetime.timezone.utc)
    date_strings = re.findall(r'(?<=Date: ).+', str(msg))
    assert len(date_strings) == 1
    for dt_string in date_strings:
    
        # Validate the Date fits to the format
        datetime.datetime.strptime(dt_string, format)

        # It should not take longer than second to generate the email
        assert dt_string in (before.strftime(format), after.strftime(format))

@pytest.mark.parametrize("sender,domain", 
    [
        pytest.param("me@example.com", "@example.com", id="With domain"),
        pytest.param(None, f"@{platform.node()}", id="Without domain"),
    ]
)
def test_message_id(sender, domain):
    email = EmailSender(host=None, port=1234)
    msg = email.get_message(sender=sender, subject="Some email")
    msg2 = email.get_message(sender=sender, subject="Some email")

    message_ids = re.findall(r'(?<=Message-ID: ).+', str(msg))
    assert len(message_ids) == 1
    message_id = message_ids[0]

    # [0-9]{{12}}[.][0-9]{{5}}[.][0-9]{{20}}
    assert bool(re.search(fr'<[0-9.]+{domain}>', message_id))

    # Check another email has not the same Message-ID
    message_id_2 = re.findall(r'(?<=Message-ID: ).+', str(msg2))[0]
    assert message_id != message_id_2

def test_cc_bcc():
    email = EmailSender(host=None, port=1234)
    msg = email.get_message(sender="me@example.com", subject="Some email", cc=['you@example.com'], bcc=['he@example.com', 'she@example.com'])
    msg = prune_generated_headers(str(msg))
    assert remove_email_content_id(msg) == dedent("""
    From: me@example.com
    Subject: Some email
    Cc: you@example.com
    Bcc: he@example.com, she@example.com
    Message-ID: <<message_id>>
    Date: <date>

    """)[1:]
