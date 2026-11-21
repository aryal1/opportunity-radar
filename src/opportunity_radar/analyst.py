import os


def analyze_dataset(dataset: dict) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Add OPENAI_API_KEY to .env to enable AI analysis.")
    from openai import OpenAI

    response = OpenAI(api_key=api_key).responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        instructions=("You are a skeptical analyst exploring business opportunities in Poland. "
                      "Use only evidence in the supplied public dataset metadata. Separate observed facts from "
                      "hypotheses, cite exact metadata, identify who may benefit, a testable opportunity, and "
                      "uncertainties. If evidence is weak, say so. Do not invent findings."),
        input=f"Title: {dataset['title']}\nPublisher: {dataset['organization']}\nCategory: {dataset['category']}\nDescription: {dataset['description']}\nKeywords: {', '.join(__import__('json').loads(dataset['keywords']))}",
    )
    return response.output_text
