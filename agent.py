from crewai import Agent, Task, Crew
import openai
import os
from dotenv import load_dotenv
import json

# Load environment variables from .env file
load_dotenv()

# Get OpenAI API key from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables. Please set it in .env file.")
openai.api_key = OPENAI_API_KEY

REQUIRED_INSIGHT_KEYS = [
    "engagementRateInsight",
    "reachInsight",
    "breakdownInsight",
    "summaryInsight"
]

# --- Agent 1: Analytics Generator ---
class AnalyticsGeneratorAgent(Agent):
    def __init__(self):
        super().__init__(
            name="AnalyticsGeneratorAgent",
            role="AI Analytics Generator",
            goal="Generate actionable, crisp, and relevant Facebook analytics insights based on provided metrics.",
            backstory="You are an expert marketing analyst specializing in social media analytics. Your job is to turn raw Facebook metrics into clear, actionable insights."
        )

    def generate_analytics(self, metrics: dict, feedback: str = None) -> dict:
        if feedback:
            prompt = f"""You are a marketing analyst. Given the following Facebook metrics and evaluator feedback, generate improved, crisp, actionable insights.\n\nYou MUST return a valid JSON object with exactly these four keys: engagementRateInsight, reachInsight, breakdownInsight, summaryInsight.\n\n\n\nMetrics: {json.dumps(metrics)}\n\nEvaluator Feedback: {feedback}\n\nRespond ONLY with valid JSON using double quotes for all keys and string values. Do not use single quotes. Do not include any text before or after the JSON."""
        else:
            prompt = f"""You are a marketing analyst. Given the following Facebook metrics, generate crisp, actionable insights.\n\nYou MUST return a valid JSON object with exactly these four keys: engagementRateInsight, reachInsight, breakdownInsight, summaryInsight.\n\nMetrics: {json.dumps(metrics)}\n\nRespond ONLY with valid JSON using double quotes for all keys and string values. Do not use single quotes. Do not include any text before or after the JSON."""
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.7
        )
        content = response.choices[0].message.content.strip()
        try:
            insights = json.loads(content)
        except Exception:
            insights = {}
        # Ensure all required keys are present
        for key in REQUIRED_INSIGHT_KEYS:
            if key not in insights:
                insights[key] = "AI did not generate this insight."
        # Remove any extra keys
        insights = {k: insights[k] for k in REQUIRED_INSIGHT_KEYS}
        return insights

# --- Agent 2: Analysis Evaluator ---
class AnalysisEvaluatorAgent(Agent):
    def __init__(self):
        super().__init__(
            name="AnalysisEvaluatorAgent",
            role="AI Analytics Evaluator",
            goal="Evaluate the quality and actionability of Facebook analytics insights and provide constructive feedback if needed.",
            backstory="You are a senior marketing strategist with a critical eye for insight quality. You ensure that all analytics are clear, actionable, and valuable."
        )

    def evaluate(self, metrics: dict, analysis: dict) -> dict:
        prompt = f"""You are a senior marketing strategist. Evaluate the following AI-generated Facebook analytics insights for quality, clarity, actionability, and professional English language. The insights must be in clear, standard English (not Pig Latin or any other code/language). If the analysis is not in clear English, or is otherwise insufficient, provide feedback.\n\nThe analysis MUST be a JSON object with exactly these four keys: engagementRateInsight, reachInsight, breakdownInsight, summaryInsight.\n\nMetrics: {json.dumps(metrics)}\n\nAnalysis: {json.dumps(analysis)}\n\nIf the analysis is sufficient, in clear English, and all four keys are present, respond with {{"status": "pass", "final_analysis": analysis}}.\nIf not, provide feedback in the following JSON structure: {{"status": "feedback", "feedback": "..."}}. Do NOT revise the analysis yourself. Respond ONLY with valid JSON using double quotes for all keys and string values. Do not use single quotes. Do not include any text before or after the JSON."""
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            temperature=0.7
        )
        content = response.choices[0].message.content.strip()
        try:
            result = json.loads(content)
        except Exception:
            result = {"status": "error", "raw": content}
        return result

# --- CrewAI Orchestration Example ---
def run_agentic_analysis(metrics: dict, max_loops: int = 3):
    generator = AnalyticsGeneratorAgent()
    evaluator = AnalysisEvaluatorAgent()
    feedback = None
    analysis = None
    for _ in range(max_loops):
        analysis = generator.generate_analytics(metrics, feedback)
        evaluation = evaluator.evaluate(metrics, analysis)
        if evaluation.get('status') == 'pass':
            return evaluation['final_analysis'], None
        elif evaluation.get('status') == 'feedback':
            feedback = evaluation.get('feedback')
        else:
            # Error or unexpected response
            return analysis, evaluation.get('raw')
    # If max loops reached without pass
    return analysis, f"Max feedback loops reached. Last feedback: {feedback}"

# --- Example Usage ---
if __name__ == "__main__":
    # Example metrics (replace with real data as needed)
    sample_metrics = {
        "reach": 10000,
        "engagementRate": 5.2,
        "likes": 300,
        "comments": 50,
        "shares": 20,
        "engagementTotal": 370
    }
    final_analysis, feedback = run_agentic_analysis(sample_metrics)
    print("Final Analysis:", json.dumps(final_analysis, indent=2))
    if feedback:
        print("\nFeedback:", feedback) 