import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import os
import json
from utils.ocr_processor import OCRProcessor
from utils.data_manager import ExpenseDataManager
from utils.expense_analyzer import ExpenseAnalyzer
from utils.ai_helper_fixed import generate_spending_insights

# Set page configuration
st.set_page_config(
    page_title="Receipt OCR & Expense Tracker",
    page_icon="📊",
    layout="wide"
)

# Initialize session state variables if they don't exist
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False

# Initialize data manager
data_manager = ExpenseDataManager("data/expenses.csv")

# Load data on app startup
if not st.session_state.data_loaded:
    data_manager.load_data()
    st.session_state.data_loaded = True

# Initialize OCR processor
ocr_processor = OCRProcessor()

# Initialize expense analyzer
expense_analyzer = ExpenseAnalyzer(data_manager)

# Page header
st.title("Receipt OCR & Expense Tracker")
st.markdown("Upload receipt images, track expenses, and analyze your spending patterns")

# Create tabs for different sections
tab1, tab2, tab3 = st.tabs(["Upload Receipt", "Manage Expenses", "Dashboard"])

# Tab 1: Upload Receipt
with tab1:
    st.header("Upload Receipt Image")
    
    # File uploader for receipt images
    uploaded_file = st.file_uploader("Choose a receipt image", type=["jpg", "jpeg", "png"])
    
    col1, col2 = st.columns(2)
    
    if uploaded_file is not None:
        with col1:
            st.image(uploaded_file, caption="Uploaded Receipt", use_column_width=True)
        
        with col2:
            st.info("Processing receipt...")
            
            # Process the image with OCR and AI enhancement
            extracted_text, date, merchant, amount, suggested_category = ocr_processor.process_receipt(uploaded_file)
            
            st.subheader("Extracted Information")
            st.text_area("Raw Text", extracted_text, height=200)
            
            # Display a badge if AI was used for processing
            if ocr_processor.use_ai:
                st.success("✨ Enhanced with AI for better accuracy")
            
            # Form for editing and confirming extracted details
            with st.form("receipt_details_form"):
                st.subheader("Verify/Edit Details")
                
                date_value = date if date else datetime.datetime.now().date()
                confirmed_date = st.date_input("Date", value=date_value)
                
                confirmed_merchant = st.text_input("Merchant", value=merchant if merchant else "")
                
                amount_value = amount if amount else ""
                confirmed_amount = st.text_input("Amount ($)", value=amount_value)
                
                # Category selection
                categories = ["Groceries", "Dining", "Transportation", "Entertainment", "Utilities", 
                              "Shopping", "Healthcare", "Education", "Travel", "Other"]
                
                # Use the AI-suggested category if available, otherwise default to first category
                default_category_index = 0
                if suggested_category and suggested_category in categories:
                    default_category_index = categories.index(suggested_category)
                    
                confirmed_category = st.selectbox(
                    "Category", 
                    categories, 
                    index=default_category_index,
                    help="Category suggested by AI based on the merchant name and receipt content"
                )
                
                # Notes field
                notes = st.text_area("Notes", "")
                
                # Submit button
                submitted = st.form_submit_button("Save Expense")
                
                if submitted:
                    try:
                        # Validate inputs
                        if not confirmed_merchant:
                            st.error("Please enter a merchant name.")
                        elif not confirmed_amount:
                            st.error("Please enter an amount.")
                        else:
                            # Try to convert amount to float
                            try:
                                amount_float = float(confirmed_amount)
                                # Add the expense to the data manager
                                data_manager.add_expense(
                                    date=confirmed_date,
                                    merchant=confirmed_merchant,
                                    amount=amount_float,
                                    category=confirmed_category,
                                    notes=notes
                                )
                                # Save the updated data
                                data_manager.save_data()
                                st.success("Expense saved successfully!")
                            except ValueError:
                                st.error("Please enter a valid amount.")
                    except Exception as e:
                        st.error(f"Error saving expense: {str(e)}")

# Tab 2: Manage Expenses
with tab2:
    st.header("Manage Expenses")
    
    # Display the expense data in an editable dataframe
    if data_manager.df.empty:
        st.info("No expenses recorded yet. Upload a receipt in the 'Upload Receipt' tab to get started.")
    else:
        # Add new expense manually
        with st.expander("Add New Expense Manually"):
            with st.form("manual_expense_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    manual_date = st.date_input("Date", value=datetime.datetime.now().date())
                    manual_merchant = st.text_input("Merchant")
                    manual_amount = st.number_input("Amount ($)", min_value=0.0, step=0.01)
                
                with col2:
                    categories = ["Groceries", "Dining", "Transportation", "Entertainment", "Utilities", 
                                 "Shopping", "Healthcare", "Education", "Travel", "Other"]
                    manual_category = st.selectbox("Category", categories, key="manual_category")
                    manual_notes = st.text_area("Notes", "", key="manual_notes")
                
                manual_submit = st.form_submit_button("Add Expense")
                
                if manual_submit:
                    if not manual_merchant:
                        st.error("Please enter a merchant name.")
                    elif manual_amount <= 0:
                        st.error("Please enter a valid amount greater than zero.")
                    else:
                        # Add the expense to the data manager
                        data_manager.add_expense(
                            date=manual_date,
                            merchant=manual_merchant,
                            amount=manual_amount,
                            category=manual_category,
                            notes=manual_notes
                        )
                        # Save the updated data
                        data_manager.save_data()
                        st.success("Expense added successfully!")
                        st.rerun()
        
        # Filter options
        st.subheader("Filter Expenses")
        col1, col2 = st.columns(2)
        
        with col1:
            # Date range filter
            date_range = st.date_input(
                "Date Range",
                value=(
                    data_manager.df['Date'].min() if not data_manager.df.empty else datetime.datetime.now().date(),
                    data_manager.df['Date'].max() if not data_manager.df.empty else datetime.datetime.now().date()
                ),
                key="date_filter",
                help="Filter expenses by date range",
                max_value=datetime.datetime.now().date()
            )
        
        with col2:
            # Category filter
            all_categories = ["All"] + sorted(data_manager.df['Category'].unique().tolist())
            selected_category = st.selectbox("Category", all_categories, key="category_filter")
        
        # Apply filters
        filtered_df = data_manager.filter_expenses(
            start_date=date_range[0] if len(date_range) > 0 else None,
            end_date=date_range[1] if len(date_range) > 1 else None,
            category=selected_category if selected_category != "All" else None
        )
        
        if filtered_df.empty:
            st.info("No expenses match the selected filters.")
        else:
            # Display the filtered expenses
            st.subheader("Expense Records")
            
            # Create a copy of the dataframe for display
            display_df = filtered_df.copy()
            display_df['Date'] = display_df['Date'].dt.strftime('%Y-%m-%d')
            display_df['Amount'] = display_df['Amount'].map('${:.2f}'.format)
            
            # Display expense records with action buttons
            st.dataframe(display_df, use_container_width=True)
            
            # Select expense to edit or delete
            if not filtered_df.empty:
                expense_indices = filtered_df.index.tolist()
                selected_expense_idx = st.selectbox(
                    "Select an expense to edit or delete",
                    options=expense_indices,
                    format_func=lambda x: f"{filtered_df.loc[x, 'Date'].strftime('%Y-%m-%d')} | {filtered_df.loc[x, 'Merchant']} | ${filtered_df.loc[x, 'Amount']:.2f}"
                )
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("Delete Selected Expense"):
                        data_manager.delete_expense(selected_expense_idx)
                        data_manager.save_data()
                        st.success("Expense deleted successfully!")
                        st.rerun()
                
                with col2:
                    if st.button("Edit Selected Expense"):
                        st.session_state.editing_expense = selected_expense_idx
                
                # Edit expense form
                if 'editing_expense' in st.session_state:
                    with st.form("edit_expense_form"):
                        st.subheader(f"Edit Expense - {filtered_df.loc[st.session_state.editing_expense, 'Merchant']}")
                        
                        edit_date = st.date_input(
                            "Date", 
                            value=filtered_df.loc[st.session_state.editing_expense, 'Date']
                        )
                        
                        edit_merchant = st.text_input(
                            "Merchant", 
                            value=filtered_df.loc[st.session_state.editing_expense, 'Merchant']
                        )
                        
                        edit_amount = st.number_input(
                            "Amount ($)", 
                            value=float(filtered_df.loc[st.session_state.editing_expense, 'Amount']),
                            min_value=0.0,
                            step=0.01
                        )
                        
                        edit_category = st.selectbox(
                            "Category", 
                            categories,
                            index=categories.index(filtered_df.loc[st.session_state.editing_expense, 'Category']) if filtered_df.loc[st.session_state.editing_expense, 'Category'] in categories else 0
                        )
                        
                        edit_notes = st.text_area(
                            "Notes", 
                            value=filtered_df.loc[st.session_state.editing_expense, 'Notes']
                        )
                        
                        update_submitted = st.form_submit_button("Update Expense")
                        
                        if update_submitted:
                            data_manager.update_expense(
                                index=st.session_state.editing_expense,
                                date=edit_date,
                                merchant=edit_merchant,
                                amount=edit_amount,
                                category=edit_category,
                                notes=edit_notes
                            )
                            data_manager.save_data()
                            st.success("Expense updated successfully!")
                            del st.session_state.editing_expense
                            st.rerun()

# Tab 3: Dashboard
with tab3:
    st.header("Expense Dashboard")
    
    if data_manager.df.empty:
        st.info("No expenses recorded yet. Upload a receipt or add expenses manually to see analytics.")
    else:
        # Time period selection for the dashboard
        time_periods = ["All Time", "This Month", "Last Month", "This Year", "Last Year", "Custom"]
        selected_period = st.selectbox("Select Time Period", time_periods)
        
        if selected_period == "Custom":
            custom_date_range = st.date_input(
                "Custom Date Range",
                value=(
                    data_manager.df['Date'].min(),
                    data_manager.df['Date'].max()
                ),
                max_value=datetime.datetime.now().date()
            )
            start_date = custom_date_range[0]
            end_date = custom_date_range[1]
        else:
            start_date, end_date = expense_analyzer.get_date_range(selected_period)
        
        # Filter data for the selected period
        period_df = data_manager.filter_expenses(start_date, end_date)
        
        if period_df.empty:
            st.info(f"No expenses found for the selected period ({selected_period}).")
        else:
            # Top metrics
            st.subheader("Summary Metrics")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_spent = period_df['Amount'].sum()
                st.metric("Total Spent", f"${total_spent:.2f}")
            
            with col2:
                avg_expense = period_df['Amount'].mean()
                st.metric("Average Expense", f"${avg_expense:.2f}")
            
            with col3:
                num_transactions = len(period_df)
                st.metric("Number of Transactions", num_transactions)
            
            with col4:
                if not period_df.empty:
                    top_category = period_df.groupby('Category')['Amount'].sum().idxmax()
                    top_category_amount = period_df.groupby('Category')['Amount'].sum().max()
                    st.metric("Top Spending Category", f"{top_category} (${top_category_amount:.2f})")
                else:
                    st.metric("Top Spending Category", "None")
            
            # Charts section
            st.subheader("Spending Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Category breakdown
                category_data = period_df.groupby('Category')['Amount'].sum().reset_index()
                fig_category = px.pie(
                    category_data, 
                    values='Amount', 
                    names='Category',
                    title='Spending by Category',
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig_category.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_category, use_container_width=True)
            
            with col2:
                # Monthly trend
                if len(period_df) > 1:  # Only show if there's sufficient data
                    # Create a monthly summary
                    period_df['month_year'] = period_df['Date'].dt.strftime('%Y-%m')
                    monthly_data = period_df.groupby('month_year')['Amount'].sum().reset_index()
                    monthly_data = monthly_data.sort_values('month_year')
                    
                    fig_trend = px.bar(
                        monthly_data,
                        x='month_year',
                        y='Amount',
                        title='Monthly Spending Trend',
                        labels={'month_year': 'Month', 'Amount': 'Total Amount ($)'}
                    )
                    st.plotly_chart(fig_trend, use_container_width=True)
                else:
                    st.info("More data is needed to show spending trends.")
            
            # Top expenses
            st.subheader("Top Expenses")
            top_expenses = period_df.sort_values('Amount', ascending=False).head(10)
            top_expenses['Date'] = top_expenses['Date'].dt.strftime('%Y-%m-%d')
            top_expenses['Amount'] = top_expenses['Amount'].map('${:.2f}'.format)
            st.dataframe(top_expenses[['Date', 'Merchant', 'Category', 'Amount', 'Notes']], use_container_width=True)
            
            # Merchant analysis
            st.subheader("Top Merchants")
            merchant_data = period_df.groupby('Merchant')['Amount'].sum().reset_index().sort_values('Amount', ascending=False).head(10)
            fig_merchant = px.bar(
                merchant_data,
                x='Merchant',
                y='Amount',
                title='Top 10 Merchants by Spending',
                labels={'Merchant': 'Merchant', 'Amount': 'Total Amount ($)'}
            )
            st.plotly_chart(fig_merchant, use_container_width=True)
            
            # AI-Powered Spending Insights
            st.subheader("✨ AI-Powered Insights")
            
            try:
                # Prepare data for AI analysis
                spending_data = {
                    "category_spending": expense_analyzer.get_spending_by_category(period_df).to_dict(),
                    "monthly_spending": period_df.groupby('month_year')['Amount'].sum().to_dict() if 'month_year' in period_df.columns else {},
                    "total_spent": float(total_spent),
                    "avg_expense": float(avg_expense),
                    "time_period": selected_period,
                    "top_expenses": top_expenses[['Merchant', 'Category', 'Amount']].to_dict() if not top_expenses.empty else {}
                }
                
                # Get AI-powered insights
                insights = generate_spending_insights(spending_data)
                
                # Display insights in an expandable container
                with st.expander("View Smart Spending Analysis", expanded=True):
                    st.markdown(insights)
            except Exception as e:
                st.warning(f"AI-powered insights could not be generated. Please check if the OpenAI API key is configured properly. Error: {str(e)}")
                st.info("To use AI-powered insights, add your OpenAI API key in the secrets configuration.")

# Footer
st.markdown("---")
st.markdown("Receipt OCR & Expense Tracker - Developed with Streamlit")
