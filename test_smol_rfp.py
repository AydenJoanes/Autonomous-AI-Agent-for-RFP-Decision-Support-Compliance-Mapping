import requests
import json
import time
import os

API_URL = "http://localhost:8011/api/v1/recommendation/analyze-with-report"
OUTPUT_FILE = "smol_rfp_result.json"
REPORT_FILE = "smol_rfp_report.md"

def run_test():
    print(f"Calling API at {API_URL}...")
    
    file_path = r"c:\Emplay-task\RFP_bid\Autonomous-AI-Agent-for-RFP-Decision-Support-Compliance-Mapping\data\sample_rfps\smol_rfp.pdf"
    
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return

    payload = {
        "file_path": file_path
    }
    
    try:
        start_time = time.time()
        print(f"Sending request for {file_path}...")
        response = requests.post(API_URL, json=payload)
        duration = time.time() - start_time
        
        print(f"Request completed in {duration:.2f}s")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Save full JSON output
            with open(OUTPUT_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"Full output saved to {OUTPUT_FILE}")
            
            # Extract and save markdown report
            if 'report_markdown' in data:
                with open(REPORT_FILE, 'w', encoding='utf-8') as f:
                    f.write(data['report_markdown'])
                print(f"Report saved to {REPORT_FILE}")
            
            rec = data.get('recommendation', {})
            print("\n=== Response Summary ===")
            print(f"Recommendation: {rec.get('recommendation')}")
            print(f"Confidence: {rec.get('confidence_score')}")
            print(f"Compliance: {rec.get('compliance_summary', {}).get('overall_compliance')}")
            
        else:
            print("Error Response:")
            print(response.text)
            
    except Exception as e:
        print(f"Exception calling API: {e}")

if __name__ == "__main__":
    run_test()
