#!/usr/bin/env python3
import psycopg2
from psycopg2.extras import RealDictCursor

def test_profile_search():
    try:
        conn = psycopg2.connect('postgresql://postgres:123456@localhost:5432/postgres')
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print("Testing search for galvanized profiles...")
        
        # Search for steel/iron product codes (should be in 72xx-73xx range)
        print("\n1. Checking for steel/iron products (72xx-73xx):")
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM m_classifier_hs1 
            WHERE cs_code LIKE '72%' OR cs_code LIKE '73%'
        """)
        steel_count = cursor.fetchone()['count']
        print(f"   Found {steel_count} steel/iron codes")
        
        if steel_count > 0:
            cursor.execute("""
                SELECT cs_code, cs_fullname 
                FROM m_classifier_hs1 
                WHERE cs_code LIKE '72%' OR cs_code LIKE '73%'
                LIMIT 10
            """)
            steel_samples = cursor.fetchall()
            print("   Sample steel codes:")
            for row in steel_samples:
                print(f"     {row['cs_code']} -> {row['cs_fullname'][:60]}...")
        
        # Test the exact search that should work for "оцинкованный профиль"
        print("\n2. Testing different search terms:")
        
        search_terms = [
            "профиль",
            "оцинкованный", 
            "металлический",
            "гипсокартон",
            "сталь"
        ]
        
        for term in search_terms:
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM m_classifier_hs1 
                WHERE LOWER(cs_fullname) LIKE %s
            """, (f'%{term.lower()}%',))
            
            count = cursor.fetchone()['count']
            print(f"   '{term}': {count} matches")
            
            if count > 0 and count < 10:
                cursor.execute("""
                    SELECT cs_code, cs_fullname 
                    FROM m_classifier_hs1 
                    WHERE LOWER(cs_fullname) LIKE %s
                    LIMIT 3
                """, (f'%{term.lower()}%',))
                
                examples = cursor.fetchall()
                for ex in examples:
                    print(f"      {ex['cs_code']} -> {ex['cs_fullname'][:50]}...")
        
        # Check what codes the user search "Оцинкованный профиль для гипсокартона" returns
        print("\n3. Testing actual search algorithm:")
        
        # Simulate the bot's search process
        query = "оцинкованный профиль для гипсокартона"
        words = query.lower().split()
        
        print(f"   Query: '{query}'")
        print(f"   Words: {words}")
        
        # Test full-text search (what the bot uses)
        cursor.execute("""
            SELECT cs_code, cs_fullname,
                   ts_rank(to_tsvector('russian', cs_fullname),
                          plainto_tsquery('russian', %s)) as rank
            FROM m_classifier_hs1
            WHERE to_tsvector('russian', cs_fullname) @@ plainto_tsquery('russian', %s)
            ORDER BY rank DESC
            LIMIT 10
        """, (query, query))
        
        fts_results = cursor.fetchall()
        print(f"   Full-text search found: {len(fts_results)} results")
        for res in fts_results:
            print(f"      {res['cs_code']} (rank: {res['rank']:.3f}) -> {res['cs_fullname'][:50]}...")
        
        # Test partial matching (fallback method)
        if len(fts_results) == 0:
            print("   No full-text results, testing partial matching...")
            
            # Test individual words that should match
            for word in ['оцинкованный', 'профиль']:
                cursor.execute("""
                    SELECT cs_code, cs_fullname
                    FROM m_classifier_hs1
                    WHERE LOWER(cs_fullname) LIKE %s
                    LIMIT 5
                """, (f'%{word}%',))
                
                word_results = cursor.fetchall()
                print(f"   '{word}' found: {len(word_results)} results")
                for res in word_results:
                    print(f"      {res['cs_code']} -> {res['cs_fullname'][:60]}...")
        
        # Test what should be the correct codes for galvanized profiles
        print("\n4. Looking for what SHOULD match galvanized drywall profiles:")
        cursor.execute("""
            SELECT cs_code, cs_fullname
            FROM m_classifier_hs1
            WHERE (LOWER(cs_fullname) LIKE '%профил%' AND LOWER(cs_fullname) LIKE '%сталь%')
               OR (LOWER(cs_fullname) LIKE '%профил%' AND LOWER(cs_fullname) LIKE '%метал%')
               OR (LOWER(cs_fullname) LIKE '%профил%' AND cs_code LIKE '73%')
            LIMIT 10
        """)
        
        should_match = cursor.fetchall()
        print(f"   Steel profiles that should match: {len(should_match)}")
        for res in should_match:
            print(f"      ✅ {res['cs_code']} -> {res['cs_fullname']}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_profile_search() 