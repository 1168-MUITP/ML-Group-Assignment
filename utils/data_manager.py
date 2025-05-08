import pandas as pd
import os
from datetime import datetime
import csv

class ExpenseDataManager:
    """
    Class for managing expense data storage and retrieval
    """
    
    def __init__(self, file_path):
        """
        Initialize the data manager with a file path for storing expenses
        
        Args:
            file_path: Path to the CSV file for storing expenses
        """
        self.file_path = file_path
        self.df = pd.DataFrame(columns=['Date', 'Merchant', 'Amount', 'Category', 'Notes'])
        
        # Create the data directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    def load_data(self):
        """
        Load expense data from the CSV file if it exists
        """
        try:
            if os.path.exists(self.file_path) and os.path.getsize(self.file_path) > 0:
                self.df = pd.read_csv(self.file_path, parse_dates=['Date'])
            else:
                # Create an empty dataframe if the file doesn't exist
                self.df = pd.DataFrame(columns=['Date', 'Merchant', 'Amount', 'Category', 'Notes'])
        except Exception as e:
            print(f"Error loading data: {e}")
            # Create a fresh dataframe if there's an error
            self.df = pd.DataFrame(columns=['Date', 'Merchant', 'Amount', 'Category', 'Notes'])
    
    def save_data(self):
        """
        Save the current expense data to the CSV file
        """
        try:
            # Create the data directory if it doesn't exist
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            
            # Convert date objects to string for storage
            df_to_save = self.df.copy()
            
            # Save the dataframe to CSV
            df_to_save.to_csv(self.file_path, index=False)
        except Exception as e:
            print(f"Error saving data: {e}")
    
    def add_expense(self, date, merchant, amount, category, notes=""):
        """
        Add a new expense to the dataframe
        
        Args:
            date: Date of the expense
            merchant: Merchant name
            amount: Expense amount
            category: Expense category
            notes: Additional notes (optional)
        """
        # Create a new row
        new_expense = {
            'Date': date,
            'Merchant': merchant,
            'Amount': amount,
            'Category': category,
            'Notes': notes
        }
        
        # Add the new expense to the dataframe
        self.df = pd.concat([self.df, pd.DataFrame([new_expense])], ignore_index=True)
    
    def update_expense(self, index, date, merchant, amount, category, notes=""):
        """
        Update an existing expense
        
        Args:
            index: Index of the expense to update
            date: Updated date
            merchant: Updated merchant name
            amount: Updated amount
            category: Updated category
            notes: Updated notes
        """
        if index in self.df.index:
            self.df.at[index, 'Date'] = date
            self.df.at[index, 'Merchant'] = merchant
            self.df.at[index, 'Amount'] = amount
            self.df.at[index, 'Category'] = category
            self.df.at[index, 'Notes'] = notes
    
    def delete_expense(self, index):
        """
        Delete an expense by index
        
        Args:
            index: Index of the expense to delete
        """
        if index in self.df.index:
            self.df = self.df.drop(index)
            # Reset index after deletion
            self.df = self.df.reset_index(drop=True)
    
    def filter_expenses(self, start_date=None, end_date=None, category=None, merchant=None):
        """
        Filter expenses by various criteria
        
        Args:
            start_date: Start date for filtering
            end_date: End date for filtering
            category: Category to filter by
            merchant: Merchant to filter by
            
        Returns:
            Filtered dataframe
        """
        filtered_df = self.df.copy()
        
        # Apply date filters
        if start_date:
            filtered_df = filtered_df[filtered_df['Date'] >= pd.Timestamp(start_date)]
        if end_date:
            filtered_df = filtered_df[filtered_df['Date'] <= pd.Timestamp(end_date)]
        
        # Apply category filter
        if category:
            filtered_df = filtered_df[filtered_df['Category'] == category]
        
        # Apply merchant filter
        if merchant:
            filtered_df = filtered_df[filtered_df['Merchant'] == merchant]
        
        return filtered_df
