import pandas as pd
import os
import time
import sys
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for
import csv
from payos import PayOS, ItemData, PaymentData  # Your PayOS API integration

sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()
BASE_ANALYSIS_DIR = os.getenv('BASE_ANALYSIS_DIR')
PAYOS_CLIENT_ID = os.getenv("PAYOS_CLIENT_ID")
PAYOS_API_KEY = os.getenv("PAYOS_API_KEY")
PAYOS_CHECKSUM_KEY = os.getenv("PAYOS_CHECKSUM_KEY")
WEB_DOMAIN = os.getenv("WEB_DOMAIN")

payos = PayOS(PAYOS_CLIENT_ID, PAYOS_API_KEY, PAYOS_CHECKSUM_KEY)

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Đặt thư mục tải lên (được sử dụng khi xử lý tải lên tệp).
# QUAN TRỌNG: Để phục vụ các tệp tĩnh, Flask sử dụng thư mục 'static' nằm tương đối với ứng dụng của bạn.
app.config['UPLOAD_FOLDER'] = r'F:\my_project_payment-gateway\my_project_payment-gateway\static\uploads'

# Đảm bảo rằng UPLOAD_FOLDER tồn tại.
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route("/")
def display_products():
    products = []
    try:
        data = pd.read_csv(os.path.join(BASE_ANALYSIS_DIR, 'analysis.csv'))
        required_columns = {
            'product_name', 
            'discount_percentage', 
            'current_price', 
            'original_price', 
            'product_image_url'
        }
        if not required_columns.issubset(data.columns):
            return ("The CSV file must contain 'product_name', 'discount_percentage', 'current_price', "
                    "'original_price', 'product_image_url' and columns."), 400
        products = data.to_dict(orient="records")
    except Exception as e:
        return f"An error occurred while processing the file: {e}", 500
    
    shopcart = []
    total_amount = 0
    count_product = 0
    try:
        data = pd.read_csv(os.path.join(BASE_ANALYSIS_DIR, 'shoppingcart.csv'), encoding="utf-8")
        required_columns = {'product_name', 'original_price', 'discounted_price', 'quantity'}
        if not required_columns.issubset(data.columns):
            return "CSV file is missing required columns.", 400
        shopcart = data.to_dict(orient="records")

        # tính tổng số lượng sản phẩm trong giỏ hàng
        count_product = len(shopcart)

        # tính tổng tiền của giỏ hàng
        for pro in shopcart:
            try:
                price = float(pro['discounted_price'].replace('₫', '').replace('.', '').strip())
                quantity = float(pro['quantity'])
                total_amount += price * quantity
            except Exception as e:
                print(f"Lỗi xử lý giá sản phẩm {pro}: {e}")

        # Debug: In ra danh sách giỏ hàng
        print("Dữ liệu giỏ hàng:", shopcart)

    except Exception as e:
        print("Lỗi đọc file CSV:", e)
        return "An error occurred while processing the file.", 500

    return render_template("index.html", products=products, shopcart=shopcart, total_amount=total_amount, count_product=count_product)

@app.route("/addshoppingcart", methods=["POST"])
def add_to_shopping_cart():
    # tạo file csv để lưu thông tin hàng
    cart_file_path = os.path.join(BASE_ANALYSIS_DIR, 'shoppingcart.csv')
    if not os.path.exists(cart_file_path):
        with open(cart_file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['product_name', 'original_price', 'discounted_price', 'quantity'])

    # đọc dữ liệu gửi về từ fontend với các thông tin cần
    data = request.get_json()
    product_name = data.get("productName")
    original_price = data.get("originalPrice")
    discounted_price = data.get("discountedPrice")
    quantity = data.get("quantity", 1)
    
    # nếu hàng đã có trong giỏ hàng thì tăng số lượng sản phẩm lên 1
    cart_data = pd.read_csv(cart_file_path)
    if product_name in cart_data['product_name'].values:
        cart_data.loc[cart_data['product_name'] == product_name, 'quantity'] += quantity
        cart_data.to_csv(cart_file_path, index=False)
        return {"success": True, "message": "Product quantity updated in the cart."}, 200

    # thêm thông tin hàng hóa vào file csv
    with open(cart_file_path, mode='a', newline='', encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([product_name, original_price, discounted_price, quantity])

    return {"success": True, "message": "Product added to the cart."}, 200
  
@app.route("/checkout", methods=["POST"])
def checkout():
    try:
        # Đọc dữ liệu giỏ hàng từ file CSV
        cart_file_path = os.path.join(BASE_ANALYSIS_DIR, 'shoppingcart.csv')
        cart_data = pd.read_csv(cart_file_path)
        
        # Lấy thông tin người mua từ các trường biểu mẫu
        buyerName = request.form.get("buyerName")
        buyerEmail = request.form.get("buyerEmail")
        buyerPhone = request.form.get("buyerPhone")
        
        # Tạo danh sách các mục thanh toán và tính tổng số tiền
        items = []
        total_amount = 0
        for _, row in cart_data.iterrows():
            item = ItemData(
                name=row['product_name'],
                quantity=int(row['quantity']),
                price=int(float(row['discounted_price'].replace('₫', '').replace('.', '').strip()))
            )
            items.append(item)
            total_amount += item.price * item.quantity
        
        # Xây dựng mô tả thô bao gồm tên người mua và điện thoại người mua
        raw_description = f"{buyerName}-{buyerPhone}-Checkout"
        description = raw_description[:25]
        
        # Tạo dữ liệu thanh toán
        payment_data = PaymentData(
            orderCode=int(time.time()),
            amount=total_amount,
            description=description,
            buyerName=buyerName,
            buyerEmail=buyerEmail,
            buyerPhone=buyerPhone,
            items=items,
            cancelUrl=WEB_DOMAIN,
            returnUrl=WEB_DOMAIN
        )
        
        # Gọi API PayOS của bạn để tạo liên kết thanh toán
        payment_link_response = payos.createPaymentLink(payment_data)
    except Exception as e:
        return str(e)
    
    # Chuyển hướng người dùng ngay lập tức đến URL thanh toán
    return redirect(payment_link_response.checkoutUrl)

@app.route("/payment", methods=["POST"])
def create_payment_link():
    try:
        # Lấy thông tin sản phẩm.
        product_name = request.form.get("product_name")
        current_price = int(float(request.form.get("current_price")))
        
        # Lấy thông tin người mua từ các trường biểu mẫu.
        buyerName = request.form.get("buyerName")
        buyerEmail = request.form.get("buyerEmail")
        buyerPhone = request.form.get("buyerPhone")
        
        # Xây dựng mô tả thô bao gồm tên người mua, điện thoại người mua và tên sản phẩm.
        # Cắt bớt còn 25 ký tự nếu cần.
        raw_description = f"{buyerName}-{buyerPhone}-{product_name}"
        description = raw_description[:25]
        
        # Tạo mục thanh toán và dữ liệu thanh toán.
        item = ItemData(name=product_name, quantity=1, price=current_price)
        payment_data = PaymentData(
            orderCode=int(time.time()),
            amount=current_price,
            description=description,
            buyerName=buyerName,
            buyerEmail=buyerEmail,
            buyerPhone=buyerPhone,
            items=[item],
            cancelUrl=WEB_DOMAIN,
            returnUrl=WEB_DOMAIN
        )
        
        # Gọi API PayOS của bạn để tạo liên kết thanh toán.
        payment_link_response = payos.createPaymentLink(payment_data)
    except Exception as e:
        return str(e)
    
    # Chuyển hướng người dùng ngay lập tức đến URL thanh toán.
    return redirect(payment_link_response.checkoutUrl)

# (Tùy chọn) Lộ trình gỡ lỗi để liệt kê các tệp trong thư mục tải lên của bạn
@app.route("/check_uploads")
def check_uploads():
    try:
        files = os.listdir(app.config['UPLOAD_FOLDER'])
        return "Files in uploads: " + ", ".join(files)
    except Exception as e:
        return str(e)

if __name__ == "__main__":
    app.run(debug=True)
