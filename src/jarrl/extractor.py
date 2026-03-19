def extract_article(url: str) -> dict:
    from newspaper import Article as NewspaperArticle

    article = NewspaperArticle(url)
    article.download()
    article.parse()
    return {
        "title": article.title,
        "description": article.meta_description or article.text[:280] or None,
        "published_at": article.publish_date,
    }
