import pandas as pd
import datetime

class ExpenseAnalyzer:
    """
    Class for analyzing expense data and generating insights
    """
    
    def __init__(self, data_manager):
        """
        Initialize the expense analyzer with a data manager
        
        Args:
            data_manager: Instance of ExpenseDataManager
        """
        self.data_manager = data_manager
    
    def get_date_range(self, time_period):
        """
        Get start and end dates for a specified time period
        
        Args:
            time_period: String representing the time period 
                         ("All Time", "This Month", "Last Month", "This Year", "Last Year")
            
        Returns:
            tuple: (start_date, end_date)
        """
        today = datetime.datetime.now().date()
        
        if time_period == "All Time":
            # Use the earliest and latest dates in the dataset if available
            if not self.data_manager.df.empty:
                start_date = self.data_manager.df['Date'].min().date()
                end_date = self.data_manager.df['Date'].max().date()
            else:
                # Default to a year ago if no data
                start_date = today - datetime.timedelta(days=365)
                end_date = today
        
        elif time_period == "This Month":
            # First day of current month to today
            start_date = today.replace(day=1)
            end_date = today
        
        elif time_period == "Last Month":
            # First and last day of previous month
            if today.month == 1:
                last_month = 12
                last_month_year = today.year - 1
            else:
                last_month = today.month - 1
                last_month_year = today.year
            
            # First day of last month
            start_date = datetime.date(last_month_year, last_month, 1)
            
            # Last day of last month
            if last_month == 12:
                end_date = datetime.date(last_month_year, 12, 31)
            else:
                # Last day is one day before the first day of current month
                end_date = datetime.date(today.year, today.month, 1) - datetime.timedelta(days=1)
        
        elif time_period == "This Year":
            # January 1st of current year to today
            start_date = datetime.date(today.year, 1, 1)
            end_date = today
        
        elif time_period == "Last Year":
            # January 1st to December 31st of previous year
            start_date = datetime.date(today.year - 1, 1, 1)
            end_date = datetime.date(today.year - 1, 12, 31)
        
        else:  # Default to All Time
            if not self.data_manager.df.empty:
                start_date = self.data_manager.df['Date'].min().date()
                end_date = self.data_manager.df['Date'].max().date()
            else:
                start_date = today - datetime.timedelta(days=365)
                end_date = today
        
        return start_date, end_date
    
    def get_total_spent(self, filtered_df=None):
        """
        Calculate the total amount spent
        
        Args:
            filtered_df: Filtered dataframe to analyze (uses all data if None)
            
        Returns:
            float: Total amount spent
        """
        df = filtered_df if filtered_df is not None else self.data_manager.df
        if df.empty:
            return 0.0
        return df['Amount'].sum()
    
    def get_spending_by_category(self, filtered_df=None):
        """
        Calculate spending by category
        
        Args:
            filtered_df: Filtered dataframe to analyze (uses all data if None)
            
        Returns:
            DataFrame: Spending by category
        """
        df = filtered_df if filtered_df is not None else self.data_manager.df
        if df.empty:
            return pd.DataFrame(columns=['Category', 'Amount'])
        
        return df.groupby('Category')['Amount'].sum().reset_index().sort_values('Amount', ascending=False)
    
    def get_spending_by_merchant(self, filtered_df=None, top_n=10):
        """
        Calculate spending by merchant
        
        Args:
            filtered_df: Filtered dataframe to analyze (uses all data if None)
            top_n: Number of top merchants to return
            
        Returns:
            DataFrame: Spending by merchant
        """
        df = filtered_df if filtered_df is not None else self.data_manager.df
        if df.empty:
            return pd.DataFrame(columns=['Merchant', 'Amount'])
        
        return df.groupby('Merchant')['Amount'].sum().reset_index().sort_values('Amount', ascending=False).head(top_n)
    
    def get_monthly_spending(self, filtered_df=None):
        """
        Calculate monthly spending
        
        Args:
            filtered_df: Filtered dataframe to analyze (uses all data if None)
            
        Returns:
            DataFrame: Monthly spending
        """
        df = filtered_df if filtered_df is not None else self.data_manager.df
        if df.empty:
            return pd.DataFrame(columns=['Month', 'Amount'])
        
        # Add month-year column
        df = df.copy()
        df['Month'] = df['Date'].dt.strftime('%Y-%m')
        
        # Group by month-year and sum amounts
        monthly = df.groupby('Month')['Amount'].sum().reset_index()
        
        # Sort by month-year
        monthly = monthly.sort_values('Month')
        
        return monthly
    
    def get_average_expense(self, filtered_df=None):
        """
        Calculate the average expense amount
        
        Args:
            filtered_df: Filtered dataframe to analyze (uses all data if None)
            
        Returns:
            float: Average expense amount
        """
        df = filtered_df if filtered_df is not None else self.data_manager.df
        if df.empty:
            return 0.0
        return df['Amount'].mean()
    
    def get_top_expenses(self, filtered_df=None, top_n=5):
        """
        Get the top expenses by amount
        
        Args:
            filtered_df: Filtered dataframe to analyze (uses all data if None)
            top_n: Number of top expenses to return
            
        Returns:
            DataFrame: Top expenses
        """
        df = filtered_df if filtered_df is not None else self.data_manager.df
        if df.empty:
            return pd.DataFrame(columns=['Date', 'Merchant', 'Category', 'Amount', 'Notes'])
        
        return df.sort_values('Amount', ascending=False).head(top_n)
