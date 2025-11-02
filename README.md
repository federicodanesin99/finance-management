# Personal Finance Management App with Streamlit and Supabase

## Main Features

### Dashboard
- KPI overview (income, expenses, balance, assets)
- Monthly trends with interactive charts
- Category summaries
- Quick navigation to monthly details

### Transaction Management
- Quick addition of income and expense transactions
- Monthly navigation with previous/next arrows
- Monthly summary (income, expenses, actual/planned balance)
- Inline editing via data editor
- Filters by date, category, account, and type

### Account Management
- Multiple accounts (main, savings, investment, custom)
- Real-time balance visualization
- Transfers between accounts with temporary PIN confirmation
- Manual balance adjustment with compensation entry
- Account activation/deactivation

### Recurring Transactions
- Creation of recurring transactions (monthly, weekly, yearly)
- Automatic generation at due dates
- Start and end date management
- Next occurrence tracking

### Advanced Statistics
- Trends over the last 12 months
- Top expenses by category
- Year-over-year comparison
- Interactive charts with Plotly

### Authentication
- Login/Registration with Supabase Auth
- Secure session management
- Row Level Security (RLS)
- Isolated data per user

---

## Installation

### 1. Requirements
Python 3.8+
Supabase account (free)

### 2. Clone the repository
git clone <repository-url>
cd personal-finance-app

###3. Install dependencies
pip install -r requirements.txt

###4. Configure Supabase
A. Create a Supabase project
Go to supabase.com
Create a new project
Copy the project URL and anon key

B. Run the SQL schema
In the Supabase dashboard, go to SQL Editor
Copy all the content from schema_supabase.sql
Execute the script

C. Enable authentication
Go to Authentication > Providers
Enable the Email provider
Set redirect URLs:
http://localhost:8501
Your production domain

###5. Configure secrets
Create a .streamlit/secrets.toml file:

[supabase]
url = "YOUR_SUPABASE_URL"
key = "YOUR_SUPABASE_ANON_KEY"
Important: Add this to your .gitignore:

.streamlit/secrets.toml

###6. Run the app
streamlit run app.py
The app will be available at http://localhost:8501.

Deploying on Streamlit Cloud
1. Prepare the repository
git init
git add .
git commit -m "Initial commit"
git push origin main

2. Deploy to Streamlit Cloud
Go to share.streamlit.io
Connect your GitHub repository
Select the main branch
Main file: app.py
3. Configure secrets
In the Streamlit Cloud dashboard:
Go to Settings > Secrets
Paste the content of .streamlit/secrets.toml

4. Update Supabase redirect URLs

In the Supabase dashboard:
Authentication > URL Configuration
Add your app URL: https://your-app.streamlit.app
