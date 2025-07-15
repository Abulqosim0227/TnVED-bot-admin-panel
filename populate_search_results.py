#!/usr/bin/env python3
import psycopg2
from psycopg2.extras import RealDictCursor
import random

def populate_search_results():
    """Populate search_results table with realistic data from actual queries and TNVED codes"""
    try:
        conn = psycopg2.connect('postgresql://postgres:123456@localhost:5432/postgres')
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print('🔄 Adding realistic search results from actual queries...')
        
        # Clear existing sample data
        cursor.execute('DELETE FROM search_results')
        print('🗑️ Cleared existing search results')
        
        # Get some real queries from usage_logs
        cursor.execute("""
            SELECT DISTINCT user_id, query, created_at
            FROM usage_logs 
            WHERE query IS NOT NULL AND TRIM(query) != ''
            ORDER BY created_at DESC
            LIMIT 15
        """)
        real_queries = cursor.fetchall()
        print(f'📋 Found {len(real_queries)} real queries to process')
        
        results_added = 0
        
        # Process each query and find matching TNVED codes
        for query_data in real_queries:
            user_id = query_data['user_id']
            query_text = query_data['query']
            timestamp = query_data['created_at']
            
            print(f'🔍 Processing query: "{query_text[:30]}..."')
            
            # Extract key words from the query for matching
            query_lower = query_text.lower()
            search_terms = []
            
            # Common search terms that might match TNVED descriptions
            if 'профиль' in query_lower or 'profile' in query_lower:
                search_terms.append('%профил%')
            if 'металл' in query_lower or 'metal' in query_lower:
                search_terms.append('%металл%')
            if 'сталь' in query_lower or 'steel' in query_lower:
                search_terms.append('%сталь%')
            if 'труб' in query_lower or 'pipe' in query_lower:
                search_terms.append('%труб%')
            if 'оцинков' in query_lower:
                search_terms.append('%оцинков%')
            if 'гипсокартон' in query_lower:
                search_terms.append('%гипсокартон%')
            
            # If no specific terms found, use first few characters
            if not search_terms:
                first_word = query_lower.split()[0] if query_lower.split() else query_lower[:5]
                if len(first_word) >= 3:
                    search_terms.append(f'%{first_word}%')
            
            matches = []
            
            # Try to find matching TNVED codes
            for term in search_terms:
                cursor.execute("""
                    SELECT cs_code, cs_fullname
                    FROM m_classifier_hs1
                    WHERE LOWER(cs_fullname) LIKE %s
                    ORDER BY cs_code
                    LIMIT 4
                """, (term,))
                
                term_matches = cursor.fetchall()
                if term_matches:
                    matches.extend(term_matches)
                    break  # Use first successful match
            
            # If no matches found, get some random steel/metal codes
            if not matches:
                cursor.execute("""
                    SELECT cs_code, cs_fullname
                    FROM m_classifier_hs1
                    WHERE cs_code LIKE '72%' OR cs_code LIKE '73%'
                    ORDER BY RANDOM()
                    LIMIT 4
                """)
                matches = cursor.fetchall()
            
            if matches:
                # Use the first match as main result
                main_match = matches[0]
                main_code = main_match['cs_code']
                main_desc = main_match['cs_fullname']
                main_accuracy = random.uniform(0.85, 0.98)
                
                # Prepare insert data
                insert_data = {
                    'user_id': user_id,
                    'query': query_text,
                    'main_code': main_code,
                    'main_description': main_desc[:500],  # Limit length
                    'main_accuracy': round(main_accuracy, 3),
                    'search_timestamp': timestamp,
                    'total_results_found': len(matches),
                    'language': 'ru'
                }
                
                # Add similar results if available
                if len(matches) >= 2:
                    insert_data.update({
                        'similar_1_code': matches[1]['cs_code'],
                        'similar_1_description': matches[1]['cs_fullname'][:500],
                        'similar_1_accuracy': round(main_accuracy - 0.05, 3)
                    })
                
                if len(matches) >= 3:
                    insert_data.update({
                        'similar_2_code': matches[2]['cs_code'],
                        'similar_2_description': matches[2]['cs_fullname'][:500],
                        'similar_2_accuracy': round(main_accuracy - 0.10, 3)
                    })
                    
                if len(matches) >= 4:
                    insert_data.update({
                        'similar_3_code': matches[3]['cs_code'],
                        'similar_3_description': matches[3]['cs_fullname'][:500],
                        'similar_3_accuracy': round(main_accuracy - 0.15, 3)
                    })
                
                # Insert the search result
                columns = list(insert_data.keys())
                placeholders = [f'%({col})s' for col in columns]
                
                cursor.execute(f"""
                    INSERT INTO search_results ({', '.join(columns)})
                    VALUES ({', '.join(placeholders)})
                """, insert_data)
                
                results_added += 1
                print(f'✅ Added result: "{query_text[:20]}..." -> {main_code}')
            else:
                print(f'❌ No TNVED codes found for: "{query_text[:30]}..."')
        
        # Commit all changes
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f'🎉 Successfully added {results_added} realistic search results!')
        return True
        
    except Exception as e:
        print(f'❌ Error populating search results: {e}')
        return False

if __name__ == "__main__":
    populate_search_results() 