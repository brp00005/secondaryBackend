#!/usr/bin/env python3
"""Fetch each state page URL and save the full HTML to files in `site_html/`.

Usage:
    python3 scripts/save_state_site_html.py --input output/state_chambers.xlsx
    python3 scripts/save_state_site_html.py          # will crawl officialusa for state links
"""
import argparse
import json
import logging
import os
import random
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse
import urllib.robotparser

import pandas as pd
import requests
from bs4 import BeautifulSoup


BASE_URL = "https://www.officialusa.com/stateguides/chambers/"
DEFAULT_INDEX = os.path.join('site_html', 'index.json')

# Globals used for per-host throttling and robots caching
_host_lock = threading.Lock()
_last_request = {}
_robots_cache = {}


def slugify(text: str) -> str:
    if not text:
        return 'unknown'
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip('-')[:200]


def fetch(url: str, timeout: int = 20) -> str:
    # Legacy simple fetch (kept for backward compatibility). Prefer using
    # `fetch_with_features` which supports caching, throttling, and robots.
    tries = 0
    backoff = 1.0
    headers = {
        'User-Agent': 'site-html-saver/1.0 (+https://example)'
    }
    while tries < 6:
        try:
            r = requests.get(url, timeout=timeout, headers=headers)
            r.raise_for_status()
            return r.text
        except requests.HTTPError as e:
            status = getattr(e.response, 'status_code', None)
            if status == 429:
                logging.warning('429 for %s, backing off %ss', url, backoff)
                time.sleep(backoff)
                backoff *= 2
                tries += 1
                continue
            raise
        except requests.RequestException:
            tries += 1
            logging.warning('Request failed for %s, retrying in %ss', url, backoff)
            time.sleep(backoff)
            backoff *= 2
    raise RuntimeError(f"Failed to fetch {url} after retries")


def load_index(index_path: str) -> dict:
    if not index_path or not os.path.exists(index_path):
        return {}
    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def save_index(index_path: str, index: dict) -> None:
    try:
        os.makedirs(os.path.dirname(index_path) or '.', exist_ok=True)
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logging.warning('Failed to write index %s: %s', index_path, e)


def _get_robot_parser_for(host: str, session: requests.Session):
    with _host_lock:
        rp = _robots_cache.get(host)
        if rp:
            return rp
        rp = urllib.robotparser.RobotFileParser()
        robots_url = f"https://{host}/robots.txt"
        try:
            # use session to read robots.txt to include headers
            r = session.get(robots_url, timeout=10)
            if r.status_code == 200:
                rp.parse(r.text.splitlines())
            else:
                rp = None
        except Exception:
            rp = None
        _robots_cache[host] = rp
        return rp


def fetch_with_features(url: str, session: requests.Session, index: dict, index_path: str,
                        respect_robots: bool = True, min_seconds_per_host: float = 1.0,
                        max_retries: int = 6, max_backoff: int = 60) -> dict:
    """Fetch URL with robots, conditional GET and per-host throttling.

    Returns dict: {'status': 'ok'|'not_modified'|'error', 'content': str or None, 'etag':..., 'last_modified':...}
    """
    parsed = urlparse(url)
    host = parsed.netloc

    # robots.txt check
    if respect_robots and host:
        rp = _get_robot_parser_for(host, session)
        if rp and not rp.can_fetch(session.headers.get('User-Agent', '*'), url):
            return {'status': 'error', 'error': 'disallowed_by_robots'}

    # per-host throttle
    with _host_lock:
        last = _last_request.get(host)
        now = time.time()
        if last:
            wait = min_seconds_per_host - (now - last)
            if wait > 0:
                time.sleep(wait)
        _last_request[host] = time.time()

    headers = {'User-Agent': session.headers.get('User-Agent', 'site-html-saver/1.0')}
    # conditional GET
    meta = index.get(url, {})
    if meta.get('etag'):
        headers['If-None-Match'] = meta.get('etag')
    if meta.get('last_modified'):
        headers['If-Modified-Since'] = meta.get('last_modified')

    tries = 0
    backoff_base = 1.0
    while tries < max_retries:
        try:
            r = session.get(url, headers=headers, timeout=30)
            if r.status_code == 304:
                # not modified
                index.setdefault(url, {})
                index[url]['last_fetched'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
                save_index(index_path, index)
                return {'status': 'not_modified', 'content': None, 'etag': meta.get('etag'), 'last_modified': meta.get('last_modified')}
            r.raise_for_status()
            etag = r.headers.get('ETag')
            last_mod = r.headers.get('Last-Modified')
            index.setdefault(url, {})
            index[url].update({'etag': etag, 'last_modified': last_mod, 'last_fetched': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())})
            save_index(index_path, index)
            return {'status': 'ok', 'content': r.text, 'etag': etag, 'last_modified': last_mod}
        except requests.HTTPError as e:
            status = getattr(e.response, 'status_code', None)
            if status == 429:
                tries += 1
                sleep = min(max_backoff, backoff_base * (2 ** tries)) * random.uniform(0.5, 1.5)
                logging.warning('429 for %s, backing off %.1fs', url, sleep)
                time.sleep(sleep)
                continue
            return {'status': 'error', 'error': str(e)}
        except requests.RequestException as e:
            tries += 1
            sleep = min(max_backoff, backoff_base * (2 ** tries)) * random.uniform(0.5, 1.5)
            logging.warning('Request failed for %s (%s), retrying in %.1fs', url, e, sleep)
            time.sleep(sleep)
            continue
    return {'status': 'error', 'error': f'failed_after_retries'}


def parse_state_links(html: str, base: str) -> list:
    soup = BeautifulSoup(html, 'html.parser')
    links = set()
    for a in soup.find_all('a', href=True):
        href = a['href'].strip()
        if '/stateguides/chambers/' in href:
            full = urljoin(base, href)
            if full.rstrip('/') == base.rstrip('/'):
                continue
            if full.endswith('/'):
                full = full[:-1]
            text = a.get_text(strip=True) or full.split('/')[-1]
            links.add((text, full))
    results = []
    seen = set()
    for text, url in links:
        if url in seen:
            continue
        seen.add(url)
        results.append({'state': text, 'url': url})
    return results


def load_input(input_path: str) -> list:
    if not input_path:
        return []
    if input_path.lower().endswith('.csv'):
        df = pd.read_csv(input_path)
    else:
        df = pd.read_excel(input_path)
    rows = []
    for _, r in df.iterrows():
        state = r.get('state') or r.get('State') or ''
        url = r.get('url') or r.get('URL') or r.get('Url')
        if isinstance(url, str) and url:
            rows.append({'state': str(state), 'url': str(url)})
    return rows


def discover_states_from_officialusa() -> list:
    html = fetch(BASE_URL)
    return parse_state_links(html, BASE_URL)


def save_html_for_entry(entry: dict, out_dir: str, delay: float = 1.0) -> dict:
    state = entry.get('state') or ''
    url = entry.get('url')
    try:
        html = fetch(url)
    except Exception as e:
        logging.warning('Failed fetching %s: %s', url, e)
        return {'state': state, 'url': url, 'filename': '', 'error': str(e)}
    # build filename
    name = slugify(state) or slugify(urlparse(url).path.replace('/', '-'))
    filename = f"{name}.html"
    path = os.path.join(out_dir, filename)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    time.sleep(delay)
    return {'state': state, 'url': url, 'filename': filename, 'error': ''}


def extract_plain_text(html: str) -> str:
    soup = BeautifulSoup(html, 'html.parser')
    # remove script/style
    for s in soup(['script', 'style', 'noscript']):
        s.decompose()
    text = soup.get_text(separator='\n')
    # normalize whitespace
    lines = [ln.strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]
    return '\n'.join(lines)


def combined_contains_state(combined_path: str, state_url: str) -> bool:
    if not combined_path or not os.path.exists(combined_path):
        return False
    try:
        with open(combined_path, 'r', encoding='utf-8') as f:
            data = f.read()
        return str(state_url) in data
    except Exception:
        return False


def state_is_fully_logged(state_url: str, chambers_path: str) -> bool:
    """Return True if the chambers sheet contains entries for this state's `source` and
    none of those entries have an empty `chamber_url` field.
    """
    if not chambers_path or not os.path.exists(chambers_path):
        return False
    try:
        if chambers_path.lower().endswith('.csv'):
            df = pd.read_csv(chambers_path)
        else:
            # try to read the 'chambers_detailed' sheet if present
            xls = pd.read_excel(chambers_path, sheet_name=None)
            if 'chambers_detailed' in xls:
                df = xls['chambers_detailed']
            else:
                # concat all sheets
                df = pd.concat(xls.values(), ignore_index=True)
    except Exception:
        return False
    if 'source' not in df.columns:
        return False
    df_src = df[df['source'].astype(str) == str(state_url)]
    if df_src.empty:
        return False
    # consider fully logged when none of the rows for this source have empty chamber_url
    if 'chamber_url' in df_src.columns:
        # treat NaN or empty string as missing
        missing = df_src['chamber_url'].isna() | (df_src['chamber_url'].astype(str).str.strip() == '')
        return not missing.any()
    # if chamber_url column not present, use presence of any rows as indicator
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', '-i', default='')
    parser.add_argument('--chambers', '-c', default='output/state_chambers_detailed.xlsx',
                        help='path to chambers sheet (xlsx or csv) to check logged chambers')
    parser.add_argument('--outdir', '-o', default='site_html')
    parser.add_argument('--mode', choices=['html', 'text'], default='html',
                        help='save full html per-state (html) or extract plain text and combine (text)')
    parser.add_argument('--combined', default=os.path.join('site_html', 'all_plans.txt'),
                        help='when --mode text, write combined output here')
    parser.add_argument('--index', default=DEFAULT_INDEX, help='path to index json for caching')
    parser.add_argument('--respect-robots', action='store_true', help='respect robots.txt')
    parser.add_argument('--min-seconds-per-host', type=float, default=1.0, help='minimum seconds between requests to same host')
    parser.add_argument('--stale-days', type=int, default=0, help='skip re-fetching pages fetched within N days (0=always)')
    parser.add_argument('--workers', '-w', type=int, default=4)
    parser.add_argument('--delay', '-d', type=float, default=1.0)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    os.makedirs(args.outdir, exist_ok=True)

    # load or init index cache
    index = load_index(args.index)

    entries = []
    if args.input:
        if os.path.exists(args.input):
            logging.info('Loading input file %s', args.input)
            entries = load_input(args.input)
        else:
            logging.warning('Input path %s not found, will discover via officialusa', args.input)

    if not entries:
        logging.info('Discovering state pages from officialusa')
        entries = discover_states_from_officialusa()

    if not entries:
        logging.error('No state URLs found; exiting')
        return

    results = []
    # prepare a requests.Session for reuse
    session = requests.Session()
    session.headers.update({'User-Agent': 'site-html-saver/1.0 (+https://example)', 'Connection': 'keep-alive'})

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {}
        for e in entries:
            name = slugify(e.get('state') or '') or slugify(urlparse(e.get('url')).path.replace('/', '-'))
            filename = f"{name}.html"
            path = os.path.join(args.outdir, filename)
            # skipping logic
            if args.mode == 'html':
                skip_check = os.path.exists(path) and state_is_fully_logged(e.get('url'), args.chambers)
            else:
                skip_check = combined_contains_state(args.combined, e.get('url')) and state_is_fully_logged(e.get('url'), args.chambers)
            # stale-days check
            if skip_check and args.stale_days > 0:
                meta = index.get(e.get('url'), {})
                last = meta.get('last_fetched')
                if last:
                    try:
                        last_ts = time.mktime(time.strptime(last, '%Y-%m-%dT%H:%M:%SZ'))
                        if (time.time() - last_ts) < (args.stale_days * 86400):
                            # fresh enough, keep skipping
                            pass
                        else:
                            skip_check = False
                    except Exception:
                        skip_check = False
            if skip_check:
                logging.info('Skipping %s (already saved and chambers logged)', e.get('url'))
                results.append({'state': e.get('state'), 'url': e.get('url'), 'filename': filename, 'text': '' , 'error': ''})
                continue
            futures[ex.submit(fetch_with_features, e.get('url'), session, index, args.index,
                               args.respect_robots, args.min_seconds_per_host)] = (e, filename)
        for fut in as_completed(futures):
            e, filename = futures[fut]
            try:
                r = fut.result()
            except Exception as exc:
                logging.warning('Task failed for %s: %s', e.get('url'), exc)
                results.append({'state': e.get('state'), 'url': e.get('url'), 'filename': filename, 'text': '', 'error': str(exc)})
                continue
            if r.get('status') == 'error':
                results.append({'state': e.get('state'), 'url': e.get('url'), 'filename': filename, 'text': '', 'error': r.get('error')})
                continue
            if args.mode == 'html':
                # write per-state html when fetched
                if r.get('status') == 'ok' and r.get('content'):
                    path = os.path.join(args.outdir, filename)
                    try:
                        with open(path, 'w', encoding='utf-8') as f:
                            f.write(r.get('content'))
                    except Exception as exc:
                        logging.warning('Failed writing %s: %s', path, exc)
                        results.append({'state': e.get('state'), 'url': e.get('url'), 'filename': filename, 'text': '', 'error': str(exc)})
                        continue
                    time.sleep(args.delay)
                results.append({'state': e.get('state'), 'url': e.get('url'), 'filename': filename, 'text': '', 'error': ''})
            else:
                # text mode: if not_modified, we may skip; if ok, extract and append
                if r.get('status') == 'ok' and r.get('content'):
                    try:
                        text = extract_plain_text(r.get('content'))
                    except Exception as exc:
                        logging.warning('Failed extracting text for %s: %s', e.get('url'), exc)
                        results.append({'state': e.get('state'), 'url': e.get('url'), 'filename': filename, 'text': '', 'error': str(exc)})
                        continue
                    results.append({'state': e.get('state'), 'url': e.get('url'), 'filename': filename, 'text': text, 'error': ''})
                else:
                    # not modified or empty content
                    results.append({'state': e.get('state'), 'url': e.get('url'), 'filename': filename, 'text': '', 'error': ''})

    # write combined text file when in text mode
    if args.mode == 'text':
        os.makedirs(os.path.dirname(args.combined) or '.', exist_ok=True)
        appended = 0
        with open(args.combined, 'a', encoding='utf-8') as combined_f:
            for r in results:
                if r.get('error'):
                    continue
                # skip entries that had empty text (e.g., skipped earlier or not_modified)
                if not r.get('text'):
                    continue
                # avoid duplicating by checking if URL already present in combined file
                if combined_contains_state(args.combined, r.get('url')):
                    continue
                combined_f.write('\n===== SOURCE: ' + r.get('url', '') + ' =====\n')
                combined_f.write('\n')
                combined_f.write(r.get('text', '') + '\n')
                appended += 1
        logging.info('Appended %d entries to %s', appended, args.combined)

    # persist final index state
    save_index(args.index, index)
    logging.info('Index saved to %s', args.index)

    # write index file
    idx_path = os.path.join(args.outdir, 'index.csv')
    df = pd.DataFrame(results)
    df.to_csv(idx_path, index=False)
    logging.info('Saved %d pages to %s (index: %s)', df.shape[0], args.outdir, idx_path)


if __name__ == '__main__':
    main()
