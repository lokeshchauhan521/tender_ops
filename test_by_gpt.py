import requests
import logging
from time import sleep
# from scraper.base.scraper_interface import TenderScraper
 
# class GeMScraper(TenderScraper):
#     BASE_URL = "https://mkp.gem.gov.in/mkp"
#     HEADERS = {
#         "User-Agent": "Mozilla/5.0 (compatible; TenderScraper/1.0)",
#         "Accept": "application/json"
#     }
BASE_URL = "https://mkp.gem.gov.in/mkp"
HEADERS = {
        "User-Agent": "Mozilla/5.0 (compatible; TenderScraper/1.0)",
        "Accept": "application/json"
    }
 
def fetch_list(max_pages=5):
    tender_ids = []
    for page in range(max_pages):
        try:
            response = requests.get(
                f"{BASE_URL}",
                headers=HEADERS,
                params={"page": page, "size": 10, "sort": "createdDate,desc"}
            )
            response.raise_for_status()
            data = response.json()
            if not data.get('content'):
                break
            for t in data['content']:
                tender_ids.append(t['id'])
            sleep(1)  
        except Exception as e:
            logging.error(f"[Page {page}] Failed to fetch tenders: {e}")
            break
    return tender_ids

def fetch_details(self, tender_id):
    try:
        response = requests.get(
            f"{self.BASE_URL}/tender/{tender_id}",
            headers=self.HEADERS
        )
        response.raise_for_status()
        data = response.json()
        return {
            "title": data.get("title"),
            "tender_id": data.get("tenderId"),
            "value": data.get("estimatedValue"),
            "items": data.get("items"),
            "department": data.get("departmentName"),
            "bid_end": data.get("bidEndDate"),
            "category": data.get("itemCategory"),
            "state": data.get("stateName"),
            "buyer_org": data.get("buyerOrganizationName")
        }
    except Exception as e:
        logging.error(f"Failed to fetch tender {tender_id}: {e}")
        return None


fetch_list()
# fetch_details()