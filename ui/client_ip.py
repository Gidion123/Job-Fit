"""Client IP propagation from Caddy to the internal API (per-IP pseudonym, rate limits and live ticket)."""
from __future__ import annotations

import ipaddress


def client_ip_from(peer: str | None, forwarded_for: str | None, trusted: str | None) -> tuple[str | None, str]:
    """(browser IP or None, source label) for the API's per-IP pseudonym, limits and live ticket.

    X-Forwarded-For is used only when the TCP peer of this Streamlit connection (``st.context.ip_address``,
    which Streamlit takes from the socket, not from headers) is a trusted proxy listed in
    ``JOBFIT_TRUSTED_PROXIES`` (comma-separated IPs or CIDRs, e.g. the Docker gateway Caddy connects
    through). The last hop is the one the trusted proxy appended. Anything else returns None (fail
    closed: the API then gives no live ticket). The label never contains an IP.
    """
    networks = []
    for item in (trusted or '').split(','):
        if item.strip():
            try:
                networks.append(ipaddress.ip_network(item.strip(), strict=False))
            except ValueError:
                return None, 'invalid_trusted_proxies'
    if not networks:
        return None, 'no_trusted_proxies'
    try:
        peer_ip = ipaddress.ip_address((peer or '').strip())
    except ValueError:
        return None, 'no_peer'
    if not any(peer_ip in net for net in networks):
        return None, 'untrusted_peer'
    try:
        return str(ipaddress.ip_address((forwarded_for or '').split(',')[-1].strip())), 'forwarded'
    except ValueError:
        return None, 'no_forwarded_ip'
