from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from app.services.gmail_service import get_unread_emails
from app.config import Settings

@tool
def summarize_unread_emails() -> str:
    """
    Fetch unread emails and provide a summary using an LLM.
    Returns a text summary of the unread emails.
    """
    try:
        emails = get_unread_emails()
        if not emails:
            return "No unread emails found."
        
        # Prepare email text for summarization
        email_texts = [
            f"From: {email['from']}\nSubject: {email['subject']}\nBody: {email['body'][:500]}..."
            for email in emails
        ]
        
        combined_text = "\n\n---\n\n".join(email_texts)
        prompt = f"Summarize the following emails in a natural, concise way for a personal assistant briefing:\n\n{combined_text}"

        settings = Settings()
        if not settings.openrouter_api_key:
            return "OpenRouter API key not configured, cannot summarize."

        llm = ChatOpenAI(
            model=settings.openrouter_model,
            temperature=0,
            openai_api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url
        )
        
        response = llm.invoke(prompt)
        return f"Found {len(emails)} unread emails. Summary:\n{response.content}"

    except Exception as e:
        return f"Error summarizing emails: {str(e)}"
