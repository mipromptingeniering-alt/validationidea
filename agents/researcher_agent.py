import requests
import json
import os
from datetime import datetime, timedelta

def scrape_hacker_news():
    """Scrape Hacker News front page"""
    try:
        url = "https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage=30"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        trends = []
        for hit in data.get('hits', [])[:10]:
            trends.append({
                'title': hit.get('title', ''),
                'url': hit.get('url', ''),
                'points': hit.get('points', 0)
            })
        
        return trends
    except Exception as e:
        print(f"Error scraping HN: {e}")
        return []

def scrape_github_trending():
    """Scrape GitHub trending repositories"""
    try:
        url = "https://api.github.com/search/repositories?q=stars:>1000+pushed:>2026-01-01&sort=stars&order=desc&per_page=20"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        repos = []
        for item in data.get('items', [])[:10]:
            repos.append({
                'name': item.get('name', ''),
                'description': item.get('description', ''),
                'stars': item.get('stargazers_count', 0),
                'language': item.get('language', '')
            })
        
        return repos
    except Exception as e:
        print(f"Error scraping GitHub: {e}")
        return []

def analyze_trends(hn_data, gh_data):
    """Analyze and extract top trends"""
    trends = {
        'timestamp': datetime.now().isoformat(),
        'hacker_news_top': [item['title'] for item in hn_data[:5]],
        'github_trending': [f"{item['name']} ({item['language']})" for item in gh_data[:5]],
        'tech_stack_2026': [
            'Next.js 15',
            'React 19',
            'Supabase',
            'Vercel AI SDK',
            'Tailwind CSS',
            'TypeScript',
            'Astro 5',
            'Cloudflare Workers'
        ]
    }
    
    return trends

def save_to_cache(trends):
    """Save trends to cache file"""
    os.makedirs('data', exist_ok=True)
    cache_file = 'data/research_cache.json'
    
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(trends, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Research cache guardado: {len(trends.get('hacker_news_top', []))} tendencias HN, {len(trends.get('github_trending', []))} repos GitHub")

def is_cache_valid():
    """Check if cache is valid (< 48 hours old)"""
    cache_file = 'data/research_cache.json'
    
    if not os.path.exists(cache_file):
        return False
    
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        timestamp = datetime.fromisoformat(data.get('timestamp', ''))
        age = datetime.now() - timestamp
        
        return age < timedelta(hours=48)
    except Exception:
        return False

def run():
    """Main research agent execution"""
    print("🔍 Agente Investigador iniciado...")
    
    if is_cache_valid():
        print("✅ Cache válido, saltando investigación")
        return
    
    print("📡 Scraping Hacker News...")
    hn_data = scrape_hacker_news()
    
    print("📡 Scraping GitHub Trending...")
    gh_data = scrape_github_trending()
    
    print("📊 Analizando tendencias...")
    trends = analyze_trends(hn_data, gh_data)
    
    save_to_cache(trends)
    print("✅ Agente Investigador completado")

if __name__ == "__main__":
    run()
