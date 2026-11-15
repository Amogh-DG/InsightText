import csv
import os
import random
from datetime import datetime, timedelta

TEMPLATES = {
    "Billing": [
        "Charged twice for my monthly subscription plan",
        "Why did my price go up without any prior notice?",
        "Refund still not received after 10 business days",
        "Unexpected fee appeared on my credit card statement",
        "Cannot cancel my renewal from account settings",
        "Invoice receipt not sent after successful payment",
        "Disputed unauthorized recurring charge on my card",
        "Discount voucher was not applied at final checkout",
        "Overcharged for data add-on package this month",
        "Billing address cannot be verified on the payment portal",
        "Double deduction happened during subscription upgrade",
        "Charged after canceling trial period yesterday"
    ],
    "Delivery": [
        "Package arrived two days late and missing items",
        "Box was heavily damaged but item was intact inside",
        "Tracking status has not updated in five business days",
        "Driver marked package delivered but nothing at my door",
        "Courier threw the package over the front fence roughly",
        "Delivery address was correct but package sent elsewhere",
        "Express shipping paid for but arrived via standard mail",
        "Scheduled delivery window was missed without notification",
        "Package arrived soaking wet in the rain without plastic wrap",
        "Delivery driver was extremely polite and arrived early",
        "Wrong product was delivered inside the sealed package",
        "Shipment delayed due to transit hub sorting backlog"
    ],
    "Product quality": [
        "App crashes whenever I export large analytical reports",
        "Love the new dashboard layout and responsive navigation",
        "Battery drains extremely fast while using the mobile app",
        "Search filter gives zero results even with exact keywords",
        "Material quality feels noticeably cheaper than advertised",
        "Button gets stuck and does not click smoothly",
        "Screen resolution looks blurry on external high-res monitors",
        "Software update caused slow loading and stuttering lag",
        "Build quality exceeded my expectations for this price",
        "Device overheats significantly after fifteen minutes of usage",
        "Dark mode layout looks sleek and easy on the eyes",
        "Audio crackles intermittently on left headphone speaker"
    ],
    "Support": [
        "Support never replied to my urgent priority ticket",
        "Agent was friendly and resolved my issue within minutes",
        "Transferred between four representatives without any resolution",
        "Live chat agent abruptly disconnected mid-conversation",
        "Help desk provided clear step-by-step guidance",
        "Waited on phone hold for forty-five minutes before giving up",
        "Customer service representative was courteous and helpful",
        "Automated bot loops in circles without answering questions",
        "Support ticket was closed without fixing the reported bug",
        "Knowledge base documentation is outdated and missing screenshots",
        "Very swift email support response on Sunday morning",
        "Support agent showed great patience with troubleshooting steps"
    ]
}

MODIFIERS = [
    "",
    " Please look into this as soon as possible.",
    " Extremely frustrated with this experience.",
    " Very satisfied overall with this service.",
    " Could someone contact me regarding this?",
    " This needs to be resolved immediately.",
    " Thank you for your continued assistance.",
    " Hoping for a fast turnaround.",
    " This is the third time this happened.",
    " Appreciate the team effort on this."
]

def generate_sample_dataset(output_path: str = "storage/datasets/support_tickets_q3.csv", count: int = 500):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    start_date = datetime(2026, 1, 15)
    records = []
    
    categories = list(TEMPLATES.keys())
    
    for i in range(count):
        cat = categories[i % len(categories)]
        template = random.choice(TEMPLATES[cat])
        modifier = random.choice(MODIFIERS)
        text = f"{template}{modifier}".strip()
        
        days_offset = random.randint(0, 50)
        hours_offset = random.randint(0, 23)
        minutes_offset = random.randint(0, 59)
        created_at = start_date + timedelta(days=days_offset, hours=hours_offset, minutes=minutes_offset)
        
        records.append({
            "feedback_text": text,
            "category": cat,
            "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S")
        })
        
    records.sort(key=lambda x: x["created_at"])
    
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["feedback_text", "category", "created_at"])
        writer.writeheader()
        writer.writerows(records)
        
    return output_path

if __name__ == "__main__":
    generate_sample_dataset()
