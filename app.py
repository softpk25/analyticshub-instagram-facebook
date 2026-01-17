import requests
import json
import os
from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from agent import AnalyticsGeneratorAgent, AnalysisEvaluatorAgent

# Load environment variables from .env file
load_dotenv()

# Load Facebook credentials from environment variables (preferred) or fallback to JSON file
access_token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")
page_id = os.getenv("FACEBOOK_PAGE_ID")

if not access_token or not page_id:
    # Fallback to JSON file for backwards compatibility
    try:
        with open('facebook_settings.json') as f:
            data = json.load(f)
            access_token = data.get('page_access_token', access_token)
            page_id = data.get('page_id', page_id)
    except FileNotFoundError:
        print("Warning: Facebook credentials not found in .env or facebook_settings.json")

# Page ID and URL to get post IDs
url = f"https://graph.facebook.com/v18.0/{page_id}/posts?fields=id&limit=10&access_token={access_token}"

# Get posts
response = requests.get(url)
posts = response.json().get("data", [])

# Initialize metrics
reach = 0
impressions = 0
organic_impressions = 0
paid_impressions = 0
likes = 0
comments = 0
shares = 0
reactions = 0

# Loop through each post and fetch metrics
for post in posts:
    post_id = post['id']
    # Basic engagement (likes, comments, shares, reactions, page name)
    fields = "from{name},likes.summary(true),comments.summary(true),shares,reactions.summary(true)"
    engagement_url = f"https://graph.facebook.com/v18.0/{post_id}?fields={fields}&access_token={access_token}"
    engagement = requests.get(engagement_url).json()

    # Insights (reach, impressions, organic, paid)
    metrics = "post_impressions,post_impressions_unique,post_impressions_organic,post_impressions_paid"
    insights_url = f"https://graph.facebook.com/v18.0/{post_id}/insights?metric={metrics}&access_token={access_token}"
    insights = requests.get(insights_url).json()

    # Extract values
    post_reach = 0
    post_impressions = 0
    post_organic_impressions = 0
    post_paid_impressions = 0
    for item in insights.get("data", []):
        if item["name"] == "post_impressions_unique":
            post_reach = item["values"][0]["value"]
        elif item["name"] == "post_impressions":
            post_impressions = item["values"][0]["value"]
        elif item["name"] == "post_impressions_organic":
            post_organic_impressions = item["values"][0]["value"]
        elif item["name"] == "post_impressions_paid":
            post_paid_impressions = item["values"][0]["value"]
    reach += post_reach
    impressions += post_impressions
    organic_impressions += post_organic_impressions
    paid_impressions += post_paid_impressions
    likes += engagement.get("likes", {}).get("summary", {}).get("total_count", 0)
    comments += engagement.get("comments", {}).get("summary", {}).get("total_count", 0)
    shares += engagement.get("shares", {}).get("count", 0)
    reactions += engagement.get("reactions", {}).get("summary", {}).get("total_count", 0)

# Calculate Engagement Rate
engagement_total = likes + comments + shares + reactions
engagement_rate = (engagement_total / reach * 100) if reach > 0 else 0

# --- Fetch all organic metrics for the dashboard ---
def fetch_facebook_organic_metrics(page_id, access_token):
    # Organic metrics to fetch (from config modal)
    metrics = {
        'reach': 0,
        'impressions': 0,
        'organicImpressions': 0,
        'paidImpressions': 0,
        'likes': 0,
        'comments': 0,
        'shares': 0,
        'videoViews': 0,
        'tenSecondViews': 0,
        'averageWatchTime': 0,
        'videoRetentionRate': 0,
        'websiteClicks': 0,
        'ctaClicks': 0,
        'postSaves': 0,
        'adSpend': 0,
        'adRelevanceScore': 0,
    }
    # Fetch posts for engagement and impressions
    posts_url = f"https://graph.facebook.com/v18.0/{page_id}/posts?fields=id&limit=10&access_token={access_token}"
    posts = requests.get(posts_url).json().get("data", [])
    for post in posts:
        post_id = post['id']
        # Engagement
        fields = "likes.summary(true),comments.summary(true),shares"
        engagement_url = f"https://graph.facebook.com/v18.0/{post_id}?fields={fields}&access_token={access_token}"
        engagement = requests.get(engagement_url).json()
        metrics['likes'] += engagement.get("likes", {}).get("summary", {}).get("total_count", 0)
        metrics['comments'] += engagement.get("comments", {}).get("summary", {}).get("total_count", 0)
        metrics['shares'] += engagement.get("shares", {}).get("count", 0)
        # Impressions/Reach
        insights = "post_impressions,post_impressions_unique,post_impressions_organic,post_impressions_paid"
        insights_url = f"https://graph.facebook.com/v18.0/{post_id}/insights?metric={insights}&access_token={access_token}"
        insights_data = requests.get(insights_url).json()
        for item in insights_data.get("data", []):
            if item["name"] == "post_impressions_unique":
                metrics['reach'] += item["values"][0]["value"]
            elif item["name"] == "post_impressions":
                metrics['impressions'] += item["values"][0]["value"]
            elif item["name"] == "post_impressions_organic":
                metrics['organicImpressions'] += item["values"][0]["value"]
            elif item["name"] == "post_impressions_paid":
                metrics['paidImpressions'] += item["values"][0]["value"]
    # Fetch video metrics (example: first 5 videos)
    videos_url = f"https://graph.facebook.com/v18.0/{page_id}/videos?fields=id&limit=5&access_token={access_token}"
    videos = requests.get(videos_url).json().get("data", [])
    for video in videos:
        video_id = video['id']
        video_fields = "video_insights.metric(total_video_impressions,total_video_views,total_video_10s_views,average_watch_time,video_retention)"
        video_insights_url = f"https://graph.facebook.com/v18.0/{video_id}/insights?metric=total_video_views,total_video_10s_views,average_watch_time,video_retention&access_token={access_token}"
        video_insights = requests.get(video_insights_url).json()
        for item in video_insights.get("data", []):
            if item["name"] == "total_video_views":
                metrics['videoViews'] += item["values"][0]["value"]
            elif item["name"] == "total_video_10s_views":
                metrics['tenSecondViews'] += item["values"][0]["value"]
            elif item["name"] == "average_watch_time":
                metrics['averageWatchTime'] += item["values"][0]["value"]
            elif item["name"] == "video_retention":
                metrics['videoRetentionRate'] += item["values"][0]["value"]
    # Fetch page-level metrics (website clicks, cta clicks, post saves, ad spend, ad relevance score)
    # These may require different endpoints or permissions; placeholders below:
    # metrics['websiteClicks'] = ...
    # metrics['ctaClicks'] = ...
    # metrics['postSaves'] = ...
    # metrics['adSpend'] = ...
    # metrics['adRelevanceScore'] = ...
    return metrics

# Replace the old metrics calculation with the new function
metrics = fetch_facebook_organic_metrics(page_id, access_token)

# Calculate engagementTotal and engagementRate for AI and frontend
metrics['engagementTotal'] = metrics['likes'] + metrics['comments'] + metrics['shares']
metrics['engagementRate'] = round((metrics['engagementTotal'] / metrics['reach'] * 100) if metrics['reach'] > 0 else 0, 2)

# --- Calculate derived metrics ---
# Frequency: Impressions ÷ Reach
metrics['frequency'] = round((metrics['impressions'] / metrics['reach']) if metrics['reach'] > 0 else 0, 2)

# Reach Rate: Reach ÷ Total Followers × 100
# You need to fetch total followers from the Graph API
followers_url = f"https://graph.facebook.com/v18.0/{page_id}?fields=followers_count&access_token={access_token}"
followers_data = requests.get(followers_url).json()
total_followers = followers_data.get('followers_count', 0)
metrics['reachRate'] = round((metrics['reach'] / total_followers * 100) if total_followers > 0 else 0, 2)
metrics['totalFollowers'] = total_followers  # Optionally include for frontend

# Impression Share: Your Impressions ÷ Total Available Impressions × 100
# You need to define or fetch total available impressions (placeholder below)
total_available_impressions = metrics['impressions']  # TODO: Replace with real value if available
metrics['impressionShare'] = round((metrics['impressions'] / total_available_impressions * 100) if total_available_impressions > 0 else 0, 2)
metrics['totalAvailableImpressions'] = total_available_impressions  # Optionally include for frontend

# Click-Through Rate: Total Clicks ÷ Impressions × 100
# (Assume websiteClicks as Total Clicks; update if you have a more precise metric)
metrics['clickThroughRate'] = round((metrics['websiteClicks'] / metrics['impressions'] * 100) if metrics['impressions'] > 0 else 0, 2)

# Comment Rate: Comments ÷ Reach × 100
metrics['commentRate'] = round((metrics['comments'] / metrics['reach'] * 100) if metrics['reach'] > 0 else 0, 2)

# Share Rate: Shares ÷ Reach × 100
metrics['shareRate'] = round((metrics['shares'] / metrics['reach'] * 100) if metrics['reach'] > 0 else 0, 2)

# Amplification Rate: Shares ÷ Total Engagements × 100
metrics['amplificationRate'] = round((metrics['shares'] / metrics['engagementTotal'] * 100) if metrics['engagementTotal'] > 0 else 0, 2)

# Applause Rate: Likes ÷ Total Engagements × 100
metrics['applauseRate'] = round((metrics['likes'] / metrics['engagementTotal'] * 100) if metrics['engagementTotal'] > 0 else 0, 2)

# Conversation Rate: Comments ÷ Total Engagements × 100
metrics['conversationRate'] = round((metrics['comments'] / metrics['engagementTotal'] * 100) if metrics['engagementTotal'] > 0 else 0, 2)

# Engagement Rate by Impressions: Total Engagements ÷ Impressions × 100
metrics['engagementByImpressions'] = round((metrics['engagementTotal'] / metrics['impressions'] * 100) if metrics['impressions'] > 0 else 0, 2)

# Conversion Rate: Conversions ÷ Link Clicks × 100
# (Assume ctaClicks as Link Clicks and postSaves as Conversions for placeholder; update as needed)
metrics['conversionRate'] = round((metrics['postSaves'] / metrics['ctaClicks'] * 100) if metrics['ctaClicks'] > 0 else 0, 2)

# Cost Per Click (CPC): Ad Spend ÷ Total Clicks
metrics['costPerClick'] = round((metrics['adSpend'] / metrics['websiteClicks']) if metrics['websiteClicks'] > 0 else 0, 2)

# Cost Per Thousand Impressions (CPM): Ad Spend ÷ Impressions × 1000
metrics['costPerMille'] = round((metrics['adSpend'] / metrics['impressions'] * 1000) if metrics['impressions'] > 0 else 0, 2)

# Save Rate: Post Saves ÷ Reach × 100
metrics['saveRate'] = round((metrics['postSaves'] / metrics['reach'] * 100) if metrics['reach'] > 0 else 0, 2)

# Return on Ad Spend (ROAS): Revenue ÷ Ad Spend × 100
# Placeholder: revenue = 0 (update with real value if available)
revenue = 0
metrics['returnOnAdSpend'] = round((revenue / metrics['adSpend'] * 100) if metrics['adSpend'] > 0 else 0, 2)

# Revenue Per Click: Total Revenue ÷ Total Clicks
metrics['revenuePerClick'] = round((revenue / metrics['websiteClicks']) if metrics['websiteClicks'] > 0 else 0, 2)

# Customer Acquisition Cost (CAC): Ad Spend ÷ New Customers
# Placeholder: new_customers = 0 (update with real value if available)
new_customers = 0
metrics['customerAcquisitionCost'] = round((metrics['adSpend'] / new_customers) if new_customers > 0 else 0, 2)

# Cost Per Acquisition (CPA): Ad Spend ÷ Conversions
# (Assume postSaves as Conversions for placeholder; update as needed)
metrics['costPerAcquisition'] = round((metrics['adSpend'] / metrics['postSaves']) if metrics['postSaves'] > 0 else 0, 2)

# Bid Efficiency: Actual CPC ÷ Max Bid × 100
# Placeholder: actual_cpc = costPerClick, max_bid = 1 (update as needed)
actual_cpc = metrics['costPerClick']
max_bid = 1  # TODO: Replace with real max bid if available
metrics['bidEfficiency'] = round((actual_cpc / max_bid * 100) if max_bid > 0 else 0, 2)

# Audience Saturation: Reach ÷ Audience Size × 100
# Use total_followers as audience size for a Facebook page
metrics['audienceSaturation'] = round((metrics['reach'] / total_followers * 100) if total_followers > 0 else 0, 2)

# Daily Budget Utilization: Daily Spend ÷ Daily Budget × 100
# Placeholder: daily_spend = adSpend, daily_budget = 1 (update as needed)
daily_spend = metrics['adSpend']
daily_budget = 1  # TODO: Replace with real daily budget if available
metrics['dailyBudgetUtilization'] = round((daily_spend / daily_budget * 100) if daily_budget > 0 else 0, 2)

# Optimization Score: (Quality Ranking + Engagement Ranking + Conversion Ranking) ÷ 3
# Placeholder: quality_ranking = 0, engagement_ranking = 0, conversion_ranking = 0 (update as needed)
quality_ranking = 0
engagement_ranking = 0
conversion_ranking = 0
metrics['optimizationScore'] = round(((quality_ranking + engagement_ranking + conversion_ranking) / 3) if 3 > 0 else 0, 2)

# Learning Efficiency: Conversions During Learning ÷ Total Conversions × 100
# Placeholder: conversions_during_learning = 0 (update as needed)
conversions_during_learning = 0
metrics['learningEfficiency'] = round((conversions_during_learning / metrics['postSaves'] * 100) if metrics['postSaves'] > 0 else 0, 2)

# Incremental ROAS: (Campaign Revenue - Baseline Revenue) ÷ Ad Spend
# Placeholder: campaign_revenue = 0, baseline_revenue = 0 (update as needed)
campaign_revenue = 0
baseline_revenue = 0
metrics['incrementalROAS'] = round(((campaign_revenue - baseline_revenue) / metrics['adSpend']) if metrics['adSpend'] > 0 else 0, 2)

# Video Completion Rate: Completed Views ÷ Total Video Views × 100
# (Assume tenSecondViews as Completed Views and videoViews as Total Video Views for placeholder)
metrics['videoCompletionRate'] = round((metrics['tenSecondViews'] / metrics['videoViews'] * 100) if metrics['videoViews'] > 0 else 0, 2)

# Video Engagement Rate: Video Engagements ÷ Video Views × 100
# Placeholder: video_engagements = likes + comments + shares (for video posts only, if available)
video_engagements = metrics['likes'] + metrics['comments'] + metrics['shares']  # TODO: Replace with video-specific engagements if available
metrics['videoEngagementRate'] = round((video_engagements / metrics['videoViews'] * 100) if metrics['videoViews'] > 0 else 0, 2)

# Video CTR: Video Clicks ÷ Video Impressions × 100
# Placeholder: video_clicks = websiteClicks, video_impressions = impressions (update if you have video-specific data)
metrics['videoCTR'] = round((metrics['websiteClicks'] / metrics['impressions'] * 100) if metrics['impressions'] > 0 else 0, 2)

# Average Percentage Viewed: Average Watch Time ÷ Video Duration × 100
# Placeholder: video_duration = 1 (update with real average video duration if available)
video_duration = 1  # TODO: Replace with real average video duration if available
metrics['averagePercentageViewed'] = round((metrics['averageWatchTime'] / video_duration * 100) if video_duration > 0 else 0, 2)

# --- AI Agentic Analysis Integration ---
import sys
try:
    print("[DEBUG] Running Generator agent...", file=sys.stderr)
    generator = AnalyticsGeneratorAgent()
    evaluator = AnalysisEvaluatorAgent()
    ai_analysis, ai_feedback = None, None
    max_loops = 3
    feedback = None
    for loop in range(max_loops):
        ai_analysis = generator.generate_analytics(metrics, feedback)
        print(f"[DEBUG] Generator agent completed (loop {loop+1}).", file=sys.stderr)
        print("[DEBUG] Running Analyzer agent...", file=sys.stderr)
        evaluation = evaluator.evaluate(metrics, ai_analysis)
        print(f"[DEBUG] Analyzer findings: {evaluation if evaluation else 'Analysis passed.'}", file=sys.stderr)
        if evaluation.get('status') == 'pass':
            for k, v in ai_analysis.items():
                metrics[k] = v
            print("[DEBUG] Agentic analysis successful. Insights written to JSON.", file=sys.stderr)
            ai_feedback = None
            break
        elif evaluation.get('status') == 'feedback':
            feedback = evaluation.get('feedback')
            ai_feedback = evaluation
            print("[DEBUG] Analyzer requested revision. Retrying...", file=sys.stderr)
            continue
        else:
            print("[DEBUG] Unexpected analyzer response. Writing last result.", file=sys.stderr)
            for k, v in ai_analysis.items():
                metrics[k] = v
            ai_feedback = evaluation
            break
    else:
        print("[DEBUG] Max feedback loops reached. Writing last result.", file=sys.stderr)
        for k, v in ai_analysis.items():
            metrics[k] = v
    if ai_feedback and isinstance(ai_feedback, dict) and ai_feedback.get('status') == 'feedback':
        metrics['ai_analysis_feedback'] = ai_feedback
except Exception as e:
    for k in ["engagementRateInsight", "reachInsight", "breakdownInsight", "summaryInsight"]:
        metrics[k] = f"AI agentic analysis failed: {str(e)}"
    print(f"[DEBUG] Agentic analysis failed: {str(e)}", file=sys.stderr)

# Remove test key if present
metrics.pop('hi', None)

with open('fb_metrics.json', 'w') as f:
    json.dump(metrics, f, indent=2)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI()

# Add favicon handling
@app.get('/favicon.ico')
async def get_favicon():
    favicon_path = os.path.join(BASE_DIR, 'static', 'favicon.ico')
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path)
    else:
        from fastapi.responses import Response
        return Response(status_code=204)

# Allow all origins (for local development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (HTML, JS, CSS, etc.)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_index():
    return FileResponse("static/FB-Analytics-Dashboard.html")

@app.get("/papi/facebook-metrics")
def get_facebook_metrics(demo: bool = False):
    try:
        if demo:
            with open(os.path.join(BASE_DIR, 'static', 'dummydata.json')) as f:
                return json.load(f)
        else:
            if not access_token or not page_id:
                return JSONResponse(
                    content={"error": "Facebook credentials not found"}, 
                    status_code=500
                )
            
            # Fetch fresh metrics
            metrics = fetch_facebook_organic_metrics(page_id, access_token)
            
            # Always return JSON response
            return JSONResponse(content=metrics)
            
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JSONResponse(
            content={"error": str(e)}, 
            status_code=500
        )

# Add a specific endpoint for demo data
@app.get("/dummydata.json")
def get_demo_data():
    try:
        with open(os.path.join(BASE_DIR, 'static', 'dummydata.json')) as f:
            return json.load(f)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# Uncomment below to run the FastAPI app directly
if __name__ == "__main__":
     import uvicorn
     uvicorn.run(app, host="localhost", port=8888)