import os
from urllib.parse import urldefrag, urlparse
from crawl4ai import (
    AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode,
    MemoryAdaptiveDispatcher
)

def create_output_directory():
    if not os.path.exists('crawlOutput'):
        os.makedirs('crawlOutput')

def get_safe_filename(url):
    parsed = urlparse(url)
    path = parsed.path.strip('/').replace('/', '_')
    domain = parsed.netloc.replace('.', '_')
    return f"crawlOutput/{domain}_{path or 'index'}.md"

def save_content_to_file(url, content):
    filename = get_safe_filename(url)
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(content)

async def crawl_recursive_batch(start_urls, max_depth=3, max_concurrent=10, page_limit=20):
    create_output_directory()

    browser_config = BrowserConfig(headless=True, verbose=False)
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        exclude_external_links=True,
        stream=False
    )
    dispatcher = MemoryAdaptiveDispatcher(
        memory_threshold_percent=70.0,
        check_interval=1.0,
        max_session_permit=max_concurrent
    )

    visited = set()
    pages_crawled = 0
    total_char_count = 0
    saved_files = []

    def normalize_url(url):
        return urldefrag(url)[0].rstrip('/') + '/'

    base_url = normalize_url(start_urls[0])

    def is_subpath_of_base(url):
        return normalize_url(url).startswith(base_url)

    current_urls = set([normalize_url(u) for u in start_urls if is_subpath_of_base(u)])

    async with AsyncWebCrawler(config=browser_config) as crawler:
        for depth in range(max_depth):
            if pages_crawled >= page_limit:
                break

            urls_to_crawl = [
                url for url in current_urls
                if url not in visited and is_subpath_of_base(url)
            ]

            if not urls_to_crawl:
                break

            remaining = page_limit - pages_crawled
            urls_to_crawl = urls_to_crawl[:remaining]

            results = await crawler.arun_many(
                urls=urls_to_crawl,
                config=run_config,
                dispatcher=dispatcher
            )

            next_level_urls = set()

            for result in results:
                norm_url = normalize_url(result.url)
                visited.add(norm_url)
                pages_crawled += 1

                if result.success:
                    markdown_content = result.markdown or ""
                    total_char_count += len(markdown_content)
                    save_content_to_file(result.url, markdown_content)
                    saved_files.append(get_safe_filename(result.url))

                    for link in result.links.get("internal", []):
                        next_url = normalize_url(link["href"])
                        if next_url not in visited and is_subpath_of_base(next_url):
                            next_level_urls.add(next_url)

            current_urls = next_level_urls

    return {
        "pages_crawled": pages_crawled,
        "total_chars": total_char_count,
        "saved_files": saved_files
    }
