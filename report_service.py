import bleach

def generate_report(data):
    title = bleach.clean(data.get("title", "Untitled Report"))

    summary = f"AI-generated summary for {title}"

    overview = (
        "This report provides a structured analysis based on input data "
        "processed through the AI service."
    )

    key_items = [
        "Input received and validated",
        "Processing completed successfully",
        "Structured JSON output generated"
    ]

    recommendations = [
        "Improve input data quality",
        "Enhance model training dataset",
        "Integrate Groq AI for smarter insights"
    ]

    return {
        "title": title,
        "summary": summary,
        "overview": overview,
        "key_items": key_items,
        "recommendations": recommendations
    }