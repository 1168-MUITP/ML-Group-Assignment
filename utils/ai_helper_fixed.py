import json
import os
import base64
from openai import OpenAI

# The newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# Do not change this unless explicitly requested by the user
MODEL = "gpt-4o"

# Initialize OpenAI client with API key from environment
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def analyze_receipt_text(text):
    """
    Use OpenAI to analyze receipt text and extract key information.
    
    Args:
        text: Raw text extracted from the receipt image
        
    Returns:
        dict: Dictionary containing extracted date, merchant, amount, and suggested category
    """
    default_result = {
        "date": None,
        "merchant": None,
        "amount": None,
        "category": None
    }
    
    try:
        if not text:
            return default_result
            
        prompt = f"""
        Analyze the following receipt text and extract these fields:
        1. Date (in YYYY-MM-DD format)
        2. Merchant or store name
        3. Total amount (only the number)
        4. Suggested category (choose from: Groceries, Dining, Transportation, Entertainment, Utilities, Shopping, Healthcare, Education, Travel, Other)

        Receipt text:
        {text}

        Respond with JSON in this format:
        {{
            "date": "YYYY-MM-DD",
            "merchant": "store name",
            "amount": "123.45",
            "category": "category"
        }}
        
        If you cannot find a specific field, use null for that field.
        """

        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        if content and isinstance(content, str):
            return json.loads(content)
        return default_result
    
    except Exception as e:
        print(f"Error analyzing receipt with OpenAI: {e}")
        return default_result

def suggest_category(merchant_name, amount):
    """
    Suggest a category based on the merchant name and transaction amount.
    
    Args:
        merchant_name: Name of the merchant
        amount: Transaction amount
        
    Returns:
        str: Suggested category
    """
    try:
        if not merchant_name:
            return "Other"
            
        prompt = f"""
        Based on the merchant name "{merchant_name}" and transaction amount ${amount},
        suggest the most appropriate expense category from the following options:
        - Groceries
        - Dining
        - Transportation
        - Entertainment
        - Utilities
        - Shopping
        - Healthcare
        - Education
        - Travel
        - Other
        
        Respond with only the category name.
        """

        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=20
        )
        
        content = response.choices[0].message.content
        if content and isinstance(content, str):
            category = content.strip()
            
            # Ensure the response is one of our valid categories
            valid_categories = ["Groceries", "Dining", "Transportation", "Entertainment", 
                               "Utilities", "Shopping", "Healthcare", "Education", "Travel", "Other"]
            
            if category in valid_categories:
                return category
        
        return "Other"
    
    except Exception as e:
        print(f"Error suggesting category with OpenAI: {e}")
        return "Other"

def analyze_receipt_image(image_bytes):
    """
    Analyze a receipt image directly using OpenAI's vision capabilities.
    
    Args:
        image_bytes: Raw image bytes
        
    Returns:
        dict: Dictionary containing extracted date, merchant, amount, and suggested category
    """
    default_result = {
        "date": None,
        "merchant": None,
        "amount": None,
        "category": None
    }
    
    try:
        if not image_bytes:
            return default_result
            
        # Convert image bytes to base64
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        prompt = """
        This is an image of a receipt. Please extract and return the following information:
        1. Date (in YYYY-MM-DD format)
        2. Merchant or store name
        3. Total amount (only the number)
        4. Suggested category (choose from: Groceries, Dining, Transportation, Entertainment, Utilities, Shopping, Healthcare, Education, Travel, Other)
        
        Respond with JSON in this format:
        {
            "date": "YYYY-MM-DD", 
            "merchant": "store name", 
            "amount": "123.45",
            "category": "category"
        }
        
        If you cannot find a specific field, use null for that field.
        """

        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                        }
                    ]
                }
            ],
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        if content and isinstance(content, str):
            return json.loads(content)
        return default_result
    
    except Exception as e:
        print(f"Error analyzing receipt image with OpenAI: {e}")
        return default_result

def generate_spending_insights(expense_data):
    """
    Generate insights about spending patterns from expense data.
    
    Args:
        expense_data: Dictionary with spending data by category and over time
        
    Returns:
        str: Insights about spending patterns
    """
    try:
        if not expense_data:
            return "No expense data available to generate insights."
            
        # Convert expense data to JSON string
        expense_json = json.dumps(expense_data)
        
        prompt = f"""
        Analyze the following expense data and provide 3-4 concise, actionable insights about spending patterns.
        Focus on identifying notable trends, outliers, and potential areas for saving money.
        
        Expense data:
        {expense_json}
        
        Provide insights in bullet point format, with each point being concise and specific.
        """

        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300
        )
        
        content = response.choices[0].message.content
        if content and isinstance(content, str):
            return content.strip()
        return "Unable to generate insights."
    
    except Exception as e:
        print(f"Error generating insights with OpenAI: {e}")
        return "Unable to generate spending insights at this time."