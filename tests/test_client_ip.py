"""Client IP propagation from Caddy: X-Forwarded-For counts only from a trusted proxy peer (fail closed)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'ui'))

from client_ip import client_ip_from  # noqa: E402

GATEWAY = '172.18.0.1'                     # the Docker gateway the host's Caddy connects through


def test_the_last_hop_is_used_only_from_a_trusted_peer():
    assert client_ip_from(GATEWAY, '203.0.113.9', '172.18.0.1') == ('203.0.113.9', 'forwarded')
    assert client_ip_from(GATEWAY, '198.51.100.1, 203.0.113.9', '172.18.0.0/16') == ('203.0.113.9', 'forwarded')
    assert client_ip_from(GATEWAY, '2001:db8::1', '172.18.0.1') == ('2001:db8::1', 'forwarded')


@pytest.mark.parametrize('peer, forwarded, trusted, source', [
    ('203.0.113.50', '1.2.3.4', '172.18.0.1', 'untrusted_peer'),       # a direct client cannot spoof the header
    (GATEWAY, '1.2.3.4', None, 'no_trusted_proxies'),                  # not configured: nothing forwarded
    (GATEWAY, '1.2.3.4', '', 'no_trusted_proxies'),
    (GATEWAY, '1.2.3.4', 'not-a-network', 'invalid_trusted_proxies'),
    (None, '1.2.3.4', '172.18.0.1', 'no_peer'),                        # Streamlit gives None for localhost
    (GATEWAY, None, '172.18.0.1', 'no_forwarded_ip'),
    (GATEWAY, '1.2.3.4, evil', '172.18.0.1', 'no_forwarded_ip'),
])
def test_anything_else_forwards_no_ip(peer, forwarded, trusted, source):
    assert client_ip_from(peer, forwarded, trusted) == (None, source)
