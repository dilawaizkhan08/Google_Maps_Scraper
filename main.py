from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from playwright.sync_api import sync_playwright
import pandas as pd
import os
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app)

users = {
    "testuser": "password123"  # username: password
}

def extract_data(xpath, data_list, page, timeout=5000):
    try:
        if page.locator(xpath).count() > 0:
            data = page.locator(xpath).inner_text(timeout=timeout)
            data_list.append(data)
        else:
            data_list.append("N/A")  # Default value if element is missing
    except Exception as e:
        print(f"Skipping element at {xpath} due to timeout/error: {e}")
        data_list.append("N/A")  # Default value if data can't be fetched

def scrape_data(search_for, total=10):
    names_list, address_list, website_list, phones_list = [], [], [], []
    reviews_c_list, reviews_a_list = [], []
    store_s_list, in_store_list, store_del_list = [], [], []
    place_t_list, open_list, intro_list = [], [], []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.google.com/maps")
        page.wait_for_selector('//input[@id="searchboxinput"]')

        page.locator('//input[@id="searchboxinput"]').fill(search_for)
        page.keyboard.press("Enter")
        page.wait_for_selector('//a[contains(@href, "https://www.google.com/maps/place")]')

        previously_counted = 0
        while True:
            page.mouse.wheel(0, 1000000)
            page.wait_for_selector('//a[contains(@href, "https://www.google.com/maps/place")]')
            if page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').count() >= total:
                listings = page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').all()[:total]
                listings = [listing.locator("xpath=..") for listing in listings]
                break
            else:
                current_count = page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').count()
                if current_count == previously_counted:
                    listings = page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').all()
                    break
                previously_counted = current_count

        for listing in listings:
            listing.click()
            page.wait_for_selector('//div[@class="TIHn2 "]//h1[@class="DUwDvf lfPIob"]')

            name_xpath = '//div[@class="TIHn2 "]//h1[@class="DUwDvf lfPIob"]'
            address_xpath = '//button[@data-item-id="address"]//div[contains(@class, "fontBodyMedium")]'
            website_xpath = '//a[@data-item-id="authority"]//div[contains(@class, "fontBodyMedium")]'
            phone_number_xpath = '//button[contains(@data-item-id, "phone:tel:")]//div[contains(@class, "fontBodyMedium")]'
            reviews_count_xpath = '//div[@class="TIHn2 "]//div[@class="fontBodyMedium dmRWX"]//div//span//span//span[@aria-label]'
            reviews_average_xpath = '//div[@class="TIHn2 "]//div[@class="fontBodyMedium dmRWX"]//div//span[@aria-hidden]'
            info1 = '//div[@class="LTs0Rc"][1]'
            opens_at_xpath = '//button[contains(@data-item-id, "oh")]//div[contains(@class, "fontBodyMedium")]'
            place_type_xpath = '//div[@class="LBgpqf"]//button[@class="DkEaL "]'
            intro_xpath = '//div[@class="WeS02d fontBodyMedium"]//div[@class="PYvSYb "]'

            extract_data(name_xpath, names_list, page)
            extract_data(address_xpath, address_list, page)
            extract_data(website_xpath, website_list, page)
            extract_data(phone_number_xpath, phones_list, page)
            extract_data(place_type_xpath, place_t_list, page)
            extract_data(intro_xpath, intro_list, page)

            # Safe extraction for specific elements
            try:
                reviews_count = page.locator(reviews_count_xpath).inner_text(timeout=5000) if page.locator(reviews_count_xpath).count() > 0 else ""
                reviews_c_list.append(reviews_count.replace('(', '').replace(')', '').replace(',', ''))

                reviews_average = page.locator(reviews_average_xpath).inner_text(timeout=5000) if page.locator(reviews_average_xpath).count() > 0 else ""
                reviews_a_list.append(reviews_average.replace(' ', '').replace(',', '.'))

                store_s_list.append("Yes" if 'shop' in page.locator(info1).inner_text(timeout=5000) else "No")
                in_store_list.append("Yes" if 'pickup' in page.locator(info1).inner_text(timeout=5000) else "No")
                store_del_list.append("Yes" if 'delivery' in page.locator(info1).inner_text(timeout=5000) else "No")
            except Exception as e:
                print(f"Skipping store info due to timeout/error: {e}")
                store_s_list.append("No")
                in_store_list.append("No")
                store_del_list.append("No")

            opening_time = page.locator(opens_at_xpath).inner_text(timeout=5000) if page.locator(opens_at_xpath).count() > 0 else ""
            open_list.append(opening_time)

        # DataFrame construction and CSV output
        df = pd.DataFrame({
            'Names': names_list, 'Website': website_list, 'Introduction': intro_list,
            'Phone Number': phones_list, 'Address': address_list, 'Review Count': reviews_c_list,
            'Average Review Count': reviews_a_list, 'Store Shopping': store_s_list,
            'In Store Pickup': in_store_list, 'Delivery': store_del_list,
            'Type': place_t_list, 'Opens At': open_list
        })

        df.drop_duplicates(subset=['Names', 'Phone Number', 'Address'], inplace=True)
        df.dropna(axis=1, how='all', inplace=True)
        df.to_csv('result.csv', index=False)
        browser.close()
        return df

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    # Simple authentication (replace with your DB logic)
    if users.get(username) == password:
        session['username'] = username  # Set session data
        return redirect(url_for('query'))
    else:
        return render_template('login.html', error="Invalid credentials")

@app.route('/query', methods=['GET', 'POST'])
def query():
    if 'username' not in session:
        return redirect(url_for('index'))  # Redirect to login if not logged in

    if request.method == 'POST':
        search_term = request.json.get('search_term')
        if not search_term:
            return jsonify({"error": "Search term is required"}), 400
        data = scrape_data(search_term, total=10)
        return data.to_dict(orient='records')

    return render_template('query.html')

@app.route('/logout')
def logout():
    session.pop('username', None)  # Remove user from session
    return redirect(url_for('index'))  # Redirect to login page

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
