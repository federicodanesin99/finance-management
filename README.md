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
```bash
Python 3.8+
Supabase account (free)

### 1. Clone the repository
git clone <repository-url>
cd personal-finance-app