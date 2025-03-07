# My Project

This project includes:
1. A product display and payment processing app (`display_payment_app`).
2. A product update app (`update_csv_app`).

## Installation

1. Install dependencies:
pip install -r requirements.txt

markdown
Copy
Edit

2. Run the update product app:
cd update_csv_app python app.py

arduino
Copy
Edit

3. Run the display and payment app:
cd display_payment_app python app.py

shell
Copy
Edit

## Folder Structure

my_project/ ├── .env ├── README.md ├── requirements.txt ├── data/ │ ├── analysis.csv # CSV file storing product data ├── display_payment_app/ │ ├── app.py │ └── templates/ │ ├── index.html │ ├── buy_form.html │ └── qr_payment.html ├── update_csv_app/ │ ├── app.py │ └── templates/ │ └── add_product.html

Copy
Edit
