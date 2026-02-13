from urllib.parse import urlparse, urlunparse


def update_subdomain(url, subdomain):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    new_netloc = f"{subdomain}.{domain}"
    new_url = urlunparse(parsed_url._replace(netloc=new_netloc))
    return new_url


def extract_subdomain(url):
    parsed_url = urlparse(url)
    domain_with_subdomain = parsed_url.hostname
    parts = domain_with_subdomain.split(".")
    if len(parts) > 1:
        return parts[0]
    return None
