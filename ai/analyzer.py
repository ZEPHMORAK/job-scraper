"""
ai/analyzer.py — Extract the real problem and goal from a job description using GPT-4o.
"""
from ai._client import chat


def analyze_job(description: str, title: str = "") -> dict:
    """
    Analyze a job/lead description to extract the core problem, goal, and ideal solution.
    Returns: {problem, goal, ideal_solution, pain_points}
    """
    try:
        prompt = _load_prompt("analyzer")
        text = chat(
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Job Title: {title}\n\nDescription:\n{description}"}
            ],
            temperature=0.3,
            max_tokens=400,
        )
        return _parse_analysis(text)
    except Exception as e:
        print(f"[AI/Analyzer] Error: {e}")
        return {
            "problem": description[:200],
            "goal": title,
            "ideal_solution": "Custom automation solution",
            "pain_points": [],
        }


def _parse_analysis(text: str) -> dict:
    """Parse structured output from GPT into a dict."""
    result = {"problem": "", "goal": "", "ideal_solution": "", "pain_points": []}
    current = None
    for line in text.splitlines():
        line = line.strip()
        if line.upper().startswith("PROBLEM:"):
            current = "problem"
            result["problem"] = line.split(":", 1)[1].strip()
        elif line.upper().startswith("GOAL:"):
            current = "goal"
            result["goal"] = line.split(":", 1)[1].strip()
        elif line.upper().startswith("IDEAL SOLUTION:"):
            current = "ideal_solution"
            result["ideal_solution"] = line.split(":", 1)[1].strip()
        elif line.upper().startswith("PAIN POINTS:"):
            current = "pain_points"
        elif current == "pain_points" and line.startswith("-"):
            result["pain_points"].append(line.lstrip("- "))
        elif current and line:
            if current == "pain_points":
                result["pain_points"].append(line)
            else:
                result[current] += " " + line
    return result


def _load_prompt(name: str) -> str:
    import os
    path = os.path.join(os.path.dirname(__file__), "..", "prompts", f"{name}.txt")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "You are a helpful business analyst."
