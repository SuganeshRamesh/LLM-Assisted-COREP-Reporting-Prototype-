import requests
from bs4 import BeautifulSoup
import os

# Target URL for Own Funds rules (Example)
PRA_RULEBOOK_URL = "https://www.bankofengland.co.uk/prudential-regulation/regulatory-reporting/regulatory-reporting-banking-sector"

def fetch_pra_rules(output_dir="data/rules"):
    """
    Fetches text content from the PRA CRD IV/CRR page as a proxy for the Rulebook.
    Saves it to a text file.
    """
    print(f"Fetching rules from {PRA_RULEBOOK_URL}...")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(PRA_RULEBOOK_URL, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract main content text
        # This is a heuristic; actual structure depends on the specific page
        main_content = soup.find('main') or soup.find('body')
        
        if main_content:
            text = main_content.get_text(separator="\n\n", strip=True)
            
            filename = os.path.join(output_dir, "pra_own_funds_scraped.txt")
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"Source: {PRA_RULEBOOK_URL}\n\n")
                f.write(text)
            
            print(f"Successfully saved rules to {filename}")
            return True
        else:
            print("Could not find main content.")
            return False
            
    except Exception as e:
        print(f"Error scraping rules: {e}")
        # Fallback: Create a dummy file if scraping fails so the app doesn't break
        fallback_file = os.path.join(output_dir, "pra_own_funds_fallback.txt")
        if not os.path.exists(fallback_file):
            with open(fallback_file, "w", encoding="utf-8") as f:
                f.write("Source: Fallback / Mock Data\n\n")
                f.write("Article 26 Common Equity Tier 1 items\n")
                f.write("1. Common Equity Tier 1 items of institutions consist of the following:\n")
                f.write("(a) capital instruments, provided that the conditions laid down in Article 28 or, where applicable, Article 29 are met;\n")
                f.write("(b) share premium accounts related to the instruments referred to in point (a);\n")
                f.write("(c) retained earnings;\n")
                f.write("(d) accumulated other comprehensive income;\n")
                f.write("(e) other reserves;\n")
                f.write("(f) funds for general banking risk.\n")
            print("Created fallback rule file.")
        return False

if __name__ == "__main__":
    fetch_pra_rules()
