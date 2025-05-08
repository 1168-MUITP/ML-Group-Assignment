import cv2
import numpy as np
import pytesseract
from PIL import Image
import io
import re
import datetime
from utils.ai_helper_fixed import analyze_receipt_text, analyze_receipt_image, suggest_category

class OCRProcessor:
    """
    Class for processing receipt images with OCR to extract relevant information
    """
    
    def __init__(self):
        """Initialize the OCR processor"""
        # Config can be extended if needed
        self.config = '--psm 6'  # Assume a single uniform block of text
        self.use_ai = True  # Flag to control whether to use AI for enhanced processing
    
    def preprocess_image(self, image):
        """
        Preprocess the image to improve OCR accuracy
        
        Args:
            image: OpenCV image
            
        Returns:
            Preprocessed image
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply threshold to get black and white image
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        
        # Noise removal
        kernel = np.ones((1, 1), np.uint8)
        opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
        
        return opening
    
    def process_receipt(self, uploaded_file):
        """
        Process the uploaded receipt image and extract relevant information
        
        Args:
            uploaded_file: File uploaded through Streamlit
            
        Returns:
            tuple: (extracted_text, date, merchant, amount, category)
        """
        try:
            # Read image from uploaded file
            file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
            uploaded_file.seek(0)  # Reset file pointer
            image = cv2.imdecode(file_bytes, 1)
            
            # Preprocess the image
            processed_image = self.preprocess_image(image)
            
            # Extract text using pytesseract OCR
            extracted_text = pytesseract.image_to_string(processed_image, config=self.config)
            
            # Default category
            category = None
            
            # Use AI to enhance extraction if flag is set
            if self.use_ai:
                try:
                    # First, try AI analysis on the raw image for best results
                    uploaded_file.seek(0)  # Reset file pointer
                    image_bytes = uploaded_file.read()
                    ai_image_result = analyze_receipt_image(image_bytes)
                    
                    # If image analysis provides good results, use them
                    if ai_image_result.get('merchant') and ai_image_result.get('amount'):
                        # Convert date string to datetime object if available
                        ai_date = None
                        date_str = ai_image_result.get('date')
                        if date_str and isinstance(date_str, str):
                            try:
                                ai_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
                            except:
                                # If date format doesn't match, fallback to extracted date
                                pass
                        
                        return (
                            extracted_text,
                            ai_date,
                            ai_image_result.get('merchant'),
                            ai_image_result.get('amount'),
                            ai_image_result.get('category')
                        )
                    
                    # If image analysis didn't work well, try text analysis
                    ai_text_result = analyze_receipt_text(extracted_text)
                    
                    # Convert date string to datetime object if available
                    ai_date = None
                    date_str = ai_text_result.get('date')
                    if date_str and isinstance(date_str, str):
                        try:
                            ai_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
                        except:
                            # If date format doesn't match, fallback to extracted date
                            pass
                    
                    # Use AI-extracted values if available, otherwise fall back to traditional methods
                    date = ai_date or self.extract_date(extracted_text)
                    merchant = ai_text_result.get('merchant') or self.extract_merchant(extracted_text)
                    amount = ai_text_result.get('amount') or self.extract_amount(extracted_text)
                    category = ai_text_result.get('category')
                    
                    return extracted_text, date, merchant, amount, category
                
                except Exception as e:
                    print(f"AI analysis failed, falling back to traditional methods: {e}")
            
            # Traditional extraction methods (used as fallback)
            date = self.extract_date(extracted_text)
            merchant = self.extract_merchant(extracted_text)
            amount = self.extract_amount(extracted_text)
            
            # If we have a merchant but no category, try to get category suggestion
            if merchant and amount and not category:
                try:
                    category = suggest_category(merchant, amount)
                except:
                    category = None
            
            return extracted_text, date, merchant, amount, category
        
        except Exception as e:
            print(f"Error processing receipt: {e}")
            return "Error processing image", None, None, None, None
    
    def extract_date(self, text):
        """
        Extract date from the OCR text
        
        Args:
            text: Extracted text from OCR
            
        Returns:
            date: Extracted date or None if not found
        """
        # Common date formats
        date_patterns = [
            r'\b(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})\b',  # MM/DD/YYYY or DD/MM/YYYY
            r'\b(\d{1,2})[/\-](\d{1,2})[/\-](\d{2})\b',   # MM/DD/YY or DD/MM/YY
            r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* (\d{1,2}),? (\d{4})\b',  # Month DD, YYYY
            r'\b(\d{1,2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* (\d{4})\b',    # DD Month YYYY
            r'\b(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})\b'    # YYYY/MM/DD
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Process the first match
                match = matches[0]
                
                try:
                    # Different processing depending on the pattern matched
                    if len(match) == 3:
                        if pattern == r'\b(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})\b':
                            # Assume MM/DD/YYYY format (common in US)
                            month, day, year = int(match[0]), int(match[1]), int(match[2])
                            if year < 100:  # Two-digit year
                                year += 2000 if year < 50 else 1900
                            return datetime.date(year, month, day)
                        
                        elif pattern == r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* (\d{1,2}),? (\d{4})\b':
                            # Month name, day, year
                            month_str, day, year = match[0], int(match[1]), int(match[2])
                            month_map = {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6, 
                                         'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12}
                            month = month_map[month_str.lower()[:3]]
                            return datetime.date(year, month, day)
                        
                        elif pattern == r'\b(\d{1,2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* (\d{4})\b':
                            # Day, month name, year
                            day, month_str, year = int(match[0]), match[1], int(match[2])
                            month_map = {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6, 
                                         'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12}
                            month = month_map[month_str.lower()[:3]]
                            return datetime.date(year, month, day)
                        
                        elif pattern == r'\b(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})\b':
                            # YYYY/MM/DD format
                            year, month, day = int(match[0]), int(match[1]), int(match[2])
                            return datetime.date(year, month, day)
                        
                    # Return today's date if parsing fails
                    return datetime.datetime.now().date()
                
                except (ValueError, IndexError):
                    # If date parsing fails, continue to the next pattern
                    continue
        
        # No valid date found
        return None
    
    def extract_merchant(self, text):
        """
        Extract merchant name from the OCR text
        
        Args:
            text: Extracted text from OCR
            
        Returns:
            merchant: Extracted merchant name or None if not found
        """
        # Try to identify the merchant name
        # Merchant name is often at the top of the receipt
        lines = text.strip().split('\n')
        
        # Filter out empty lines
        lines = [line.strip() for line in lines if line.strip()]
        
        if not lines:
            return None
        
        # Check first few lines for potential merchant name
        # Skip lines that appear to be headers or dates
        for i in range(min(3, len(lines))):
            line = lines[i]
            
            # Skip lines that match common patterns for dates, transaction numbers, etc.
            if re.search(r'\b(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})\b', line):  # Date
                continue
            if re.search(r'\b(receipt|invoice|order)\b', line, re.IGNORECASE):  # Receipt/Invoice header
                continue
            if re.search(r'\b(transaction|trans|tr)\s*#?\s*\d+\b', line, re.IGNORECASE):  # Transaction number
                continue
            
            # Use the line as merchant name if it's not too long and doesn't contain typical non-merchant content
            if 2 < len(line) < 50 and not re.search(r'\$\s*\d+\.\d+', line):  # Avoid price lines
                return line
        
        # If we couldn't identify the merchant in the first few lines, use the first non-empty line
        return lines[0] if lines else None
    
    def extract_amount(self, text):
        """
        Extract total amount from the OCR text
        
        Args:
            text: Extracted text from OCR
            
        Returns:
            amount: Extracted amount as string or None if not found
        """
        # Look for lines containing keywords for total
        total_patterns = [
            r'total\s*[:\$]?\s*(\d+\.\d{2})',
            r'amount\s*[:\$]?\s*(\d+\.\d{2})',
            r'subtotal\s*[:\$]?\s*(\d+\.\d{2})',
            r'[\$](\d+\.\d{2})',  # Dollar sign followed by number
            r'(\d+\.\d{2})'       # Any number with decimal point
        ]
        
        # Look for total amount
        for pattern in total_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Use the largest value if multiple matches
                try:
                    amounts = [float(match) for match in matches]
                    return str(max(amounts))
                except (ValueError, TypeError):
                    continue
        
        return None
