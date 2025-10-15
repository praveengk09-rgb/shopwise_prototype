from flask import Flask, request, jsonify
from flask_cors import CORS
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import re
from urllib.parse import quote_plus
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UniversalEcommerceScraper:
    def __init__(self):
        self.driver = None

    def create_driver(self):
        """Create and configure Chrome driver"""
        try:
            options = uc.ChromeOptions()
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            self.driver = uc.Chrome(options=options)
            return self.driver
        except Exception as e:
            logger.error(f"Error creating driver: {e}")
            raise

    def extract_price(self, price_text):
        """Extract numeric price from text"""
        if not price_text or price_text == "N/A":
            return None
        cleaned_price = re.sub(r'[^\d,]', '', price_text)
        price_match = re.search(r'[\d,]+', cleaned_price.replace(',', ''))
        if price_match:
            return int(price_match.group().replace(',', ''))
        return None

    def is_relevant_product(self, title, search_query):
        """Check if product title is relevant to search query"""
        if not title or len(title) < 3:
            return False
        
        title_lower = title.lower()
        query_lower = search_query.lower()
        
        # Filter out accessories when searching for main devices
        main_device_keywords = ['iphone', 'phone', 'mobile', 'samsung', 'pixel', 'oneplus']
        accessory_keywords = ['cover', 'case', 'protector', 'screen guard', 'tempered glass', 'pouch', 'skin']
        
        if any(dev in query_lower for dev in main_device_keywords):
            if any(acc in title_lower for acc in accessory_keywords):
                return False
        
        # Check word matching
        stop_words = {'for', 'the', 'a', 'an', 'in', 'on', 'at', 'to', 'and', 'or', 'with'}
        query_words = [word for word in query_lower.split() if len(word) > 2 and word not in stop_words]
        
        if not query_words:
            return False
        
        match_count = sum(1 for word in query_words if word in title_lower)
        return match_count >= len(query_words) / 2

    def auto_categorize_product(self, title):
        """Automatically categorize product based on title"""
        title_lower = title.lower()
        
        categories = {
            "Mobile Phones": ['phone', 'mobile', 'iphone', 'samsung', 'oneplus', 'pixel'],
            "Laptops": ['laptop', 'notebook', 'macbook', 'chromebook'],
            "Television": ['tv', 'television', 'smart tv', 'led tv'],
            "Audio Accessories": ['headphone', 'earphone', 'earbud', 'airpods'],
            "Mobile Accessories": ['charger', 'cable', 'adapter', 'power bank'],
            "Wearables": ['watch', 'smartwatch', 'fitness band'],
            "Cameras": ['camera', 'dslr', 'gopro'],
            "Apparel": ['shirt', 't-shirt', 'tshirt', 'polo', 'top', 'blouse', 'hoodie', 'sweatshirt'],
            "Bottoms": ['jeans', 'trouser', 'pant', 'cargo', 'chino'],
            "Footwear": ['shoe', 'sneaker', 'boot', 'sandal', 'slipper', 'footwear'],
            "Kitchen Appliances": ['mixer', 'grinder', 'blender', 'juicer', 'cooker'],
            "Furniture": ['sofa', 'chair', 'table', 'bed', 'mattress'],
            "Personal Care": ['shampoo', 'conditioner', 'hair oil', 'soap', 'facewash'],
            "Beauty & Cosmetics": ['makeup', 'lipstick', 'kajal', 'mascara', 'foundation'],
        }
        
        for category, keywords in categories.items():
            if any(word in title_lower for word in keywords):
                return category
        
        return "General Products"

    def scrape_flipkart(self, search_query):
        """Scrape products from Flipkart"""
        logger.info("  📱 Loading Flipkart...")
        products = []
        
        try:
            search_url = f"https://www.flipkart.com/search?q={quote_plus(search_query)}"
            self.driver.get(search_url)
            time.sleep(random.uniform(4, 6))
            
            # Scroll to load more products
            for _ in range(4):
                self.driver.execute_script("window.scrollBy(0, 1000);")
                time.sleep(2)
            
            # Try multiple container selectors
            container_selectors = [
                "div[data-id]", "div._1AtVbE", "div._13oc-S", 
                "div.tUxRFH", "div._2kHMtA", "div.cPHDOP"
            ]
            
            containers = []
            for selector in container_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if len(elements) >= 3:
                        containers = elements
                        break
                except:
                    continue
            
            for container in containers[:20]:
                try:
                    # Extract title
                    title = ""
                    title_selectors = ["a.wjcEIp", "a.WKTcLC", "div.KzDlHZ", "a.IRpwTa", 
                                      "div._2WkVRV", "a.s1Q9rs", "a._2rpwqI", "div._4rR01T"]
                    
                    for selector in title_selectors:
                        try:
                            title_elem = container.find_element(By.CSS_SELECTOR, selector)
                            title = title_elem.text.strip() or title_elem.get_attribute('title') or ""
                            if title and len(title) > 3:
                                break
                        except:
                            continue
                    
                    if not title or not self.is_relevant_product(title, search_query):
                        continue
                    
                    # Extract URL
                    product_url = search_url
                    try:
                        link_elem = container.find_element(By.CSS_SELECTOR, "a[href]")
                        href = link_elem.get_attribute('href')
                        if href and ('/p/' in href or '/dp/' in href or 'pid=' in href):
                            product_url = href if href.startswith('http') else f"https://www.flipkart.com{href}"
                    except:
                        pass
                    
                    # Extract price
                    price_text = "N/A"
                    price_selectors = ["div.Nx9bqj", "div._30jeq3", "div._3I9_wc", 
                                      "div._25b18c", "div.hl05eU", "div._16Jk6d"]
                    
                    for selector in price_selectors:
                        try:
                            price_elem = container.find_element(By.CSS_SELECTOR, selector)
                            price_text = price_elem.text.strip()
                            if price_text and ('₹' in price_text or re.search(r'\d{2,}', price_text)):
                                break
                        except:
                            continue
                    
                    if price_text == "N/A":
                        continue
                    
                    # Extract rating
                    rating = "N/A"
                    rating_selectors = ["span.Wphh3N", "div.XQDdHH", "div._3LWZlK", "span._2_R_DZ"]
                    for selector in rating_selectors:
                        try:
                            rating_elem = container.find_element(By.CSS_SELECTOR, selector)
                            rating = rating_elem.text.strip()
                            if rating:
                                break
                        except:
                            continue
                    
                    # Extract image
                    image_url = "N/A"
                    try:
                        img_elem = container.find_element(By.CSS_SELECTOR, "img")
                        image_url = img_elem.get_attribute('src') or img_elem.get_attribute('data-src') or "N/A"
                    except:
                        pass
                    
                    products.append({
                        'title': title,
                        'price': price_text,
                        'price_num': self.extract_price(price_text),
                        'rating': rating,
                        'category': self.auto_categorize_product(title),
                        'source': 'Flipkart',
                        'url': product_url,
                        'image': image_url
                    })
                    
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Flipkart: {e}")
        
        logger.info(f"  ✅ Found {len(products)} products on Flipkart")
        return products

    def scrape_amazon(self, search_query):
        """Scrape products from Amazon"""
        logger.info("  🛒 Loading Amazon...")
        products = []
        
        try:
            search_url = f"https://www.amazon.in/s?k={quote_plus(search_query)}&ref=nb_sb_noss"
            self.driver.get(search_url)
            time.sleep(random.uniform(4, 6))
            
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-component-type='s-search-result']"))
                )
            except:
                pass
            
            self.driver.execute_script("window.scrollBy(0, 1500);")
            time.sleep(2)
            
            product_containers = self.driver.find_elements(By.CSS_SELECTOR, "[data-component-type='s-search-result']")
            
            for container in product_containers[:12]:
                try:
                    # Extract title
                    title = ""
                    title_selectors = ["h2 a span", "h2 span", ".a-size-mini span",
                                      ".a-size-base-plus", ".a-size-base", "span.a-text-normal"]
                    
                    for selector in title_selectors:
                        try:
                            title_elem = container.find_element(By.CSS_SELECTOR, selector)
                            title = title_elem.text.strip()
                            if title and len(title) > 5:
                                break
                        except:
                            continue
                    
                    if not title or not self.is_relevant_product(title, search_query):
                        continue
                    
                    # Extract URL
                    product_url = search_url
                    url_selectors = ["h2 a", ".s-product-image-container a", "a[href*='/dp/']"]
                    
                    for selector in url_selectors:
                        try:
                            link_elem = container.find_element(By.CSS_SELECTOR, selector)
                            href = link_elem.get_attribute('href')
                            if href and '/dp/' in href:
                                product_url = href if href.startswith('http') else f"https://www.amazon.in{href}"
                                break
                        except:
                            continue
                    
                    # Extract price
                    price_text = "N/A"
                    price_selectors = [".a-price-whole", ".a-price .a-offscreen", ".a-price"]
                    
                    for selector in price_selectors:
                        try:
                            price_elem = container.find_element(By.CSS_SELECTOR, selector)
                            price_text = price_elem.text.strip() or price_elem.get_attribute("textContent").strip()
                            if price_text and ('₹' in price_text or re.search(r'\d', price_text)):
                                break
                        except:
                            continue
                    
                    if price_text == "N/A":
                        continue
                    
                    # Extract rating
                    rating = "N/A"
                    rating_selectors = [".a-icon-alt", "span[aria-label*='out of']"]
                    
                    for selector in rating_selectors:
                        try:
                            rating_elem = container.find_element(By.CSS_SELECTOR, selector)
                            rating_text = rating_elem.get_attribute("title") or rating_elem.text
                            if rating_text and any(char.isdigit() for char in rating_text):
                                rating = rating_text
                                break
                        except:
                            pass
                    
                    # Extract image
                    image_url = "N/A"
                    try:
                        img_elem = container.find_element(By.CSS_SELECTOR, "img.s-image, img")
                        image_url = img_elem.get_attribute('src') or "N/A"
                    except:
                        pass
                    
                    products.append({
                        'title': title,
                        'price': price_text,
                        'price_num': self.extract_price(price_text),
                        'rating': rating,
                        'category': self.auto_categorize_product(title),
                        'source': 'Amazon',
                        'url': product_url,
                        'image': image_url
                    })
                    
                except Exception:
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Amazon: {e}")
        
        logger.info(f"  ✅ Found {len(products)} products on Amazon")
        return products

    def scrape_vijay_sales(self, search_query):
        """Scrape products from Vijay Sales"""
        logger.info("  🏬 Loading Vijay Sales...")
        products = []
        
        try:
            search_url = f"https://www.vijaysales.com/search-listing?q={quote_plus(search_query)}"
            self.driver.get(search_url)
            time.sleep(random.uniform(4, 6))
            
            for i in range(4):
                self.driver.execute_script("window.scrollBy(0, 800);")
                time.sleep(2)
            
            container_selectors = [
                ".product-card", ".product-item", ".item",
                ".product-container", "[class*='product']"
            ]
            
            containers = []
            for selector in container_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if len(elements) >= 2:
                        containers = elements
                        break
                except:
                    continue
            
            for container in containers[:15]:
                try:
                    title = ""
                    product_url = search_url
                    
                    # Extract title and URL
                    title_selectors = ["a.product-name", "a.product-title", "a.item-name"]
                    
                    for selector in title_selectors:
                        try:
                            link_elem = container.find_element(By.CSS_SELECTOR, selector)
                            title = link_elem.text.strip() or link_elem.get_attribute('title') or ""
                            if title and len(title) > 3:
                                href = link_elem.get_attribute('href')
                                if href:
                                    product_url = href if href.startswith('http') else f"https://www.vijaysales.com{href}"
                                break
                        except:
                            continue
                    
                    if not title or not self.is_relevant_product(title, search_query):
                        continue
                    
                    # Extract price
                    price_text = "N/A"
                    price_selectors = [".price", ".final-price", ".current-price", ".selling-price"]
                    
                    for selector in price_selectors:
                        try:
                            price_elem = container.find_element(By.CSS_SELECTOR, selector)
                            price_text = price_elem.text.strip()
                            if price_text and ('₹' in price_text or re.search(r'\d{2,}', price_text)):
                                break
                        except:
                            continue
                    
                    if price_text == "N/A":
                        try:
                            container_text = container.text
                            price_match = re.search(r'₹\s*[\d,]+', container_text)
                            if price_match:
                                price_text = price_match.group().strip()
                        except:
                            pass
                    
                    if price_text == "N/A":
                        continue
                    
                    # Extract rating
                    rating = "N/A"
                    try:
                        rating_elem = container.find_element(By.CSS_SELECTOR, ".rating, .star-rating")
                        rating = rating_elem.text.strip()
                    except:
                        pass
                    
                    # Extract image
                    image_url = "N/A"
                    try:
                        img_elem = container.find_element(By.CSS_SELECTOR, "img")
                        image_url = img_elem.get_attribute('src') or "N/A"
                        if image_url != "N/A" and image_url.startswith('/'):
                            image_url = f"https://www.vijaysales.com{image_url}"
                    except:
                        pass
                    
                    products.append({
                        'title': title,
                        'price': price_text,
                        'price_num': self.extract_price(price_text),
                        'rating': rating,
                        'category': self.auto_categorize_product(title),
                        'source': 'Vijay Sales',
                        'url': product_url,
                        'image': image_url
                    })
                    
                except Exception:
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Vijay Sales: {e}")
        
        logger.info(f"  ✅ Found {len(products)} products on Vijay Sales")
        return products

    def scrape_jiomart(self, search_query):
        """Scrape products from JioMart"""
        logger.info("  🔵 Loading JioMart...")
        products = []
        
        try:
            search_url = f"https://www.jiomart.com/search/{quote_plus(search_query)}"
            self.driver.get(search_url)
            time.sleep(random.uniform(4, 6))
            
            for _ in range(3):
                self.driver.execute_script("window.scrollBy(0, 1000);")
                time.sleep(1.5)
            
            containers = self.driver.find_elements(By.CSS_SELECTOR, "div.plp-card-container")
            
            for container in containers[:15]:
                try:
                    title = container.find_element(By.CSS_SELECTOR, "div.plp-card-details-name").text.strip()
                    price_text = container.find_element(By.CSS_SELECTOR, "span.jm-heading-xxs").text.strip()
                    
                    if not self.is_relevant_product(title, search_query):
                        continue
                    
                    try:
                        product_url = container.find_element(By.TAG_NAME, "a").get_attribute("href")
                    except:
                        product_url = search_url
                    
                    try:
                        image_url = container.find_element(By.CSS_SELECTOR, "img").get_attribute("src")
                    except:
                        image_url = "N/A"
                    
                    products.append({
                        'title': title,
                        'price': price_text,
                        'price_num': self.extract_price(price_text),
                        'rating': "N/A",
                        'category': self.auto_categorize_product(title),
                        'source': 'JioMart',
                        'url': product_url,
                        'image': image_url
                    })
                    
                except Exception:
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping JioMart: {e}")
        
        logger.info(f"  ✅ Found {len(products)} products on JioMart")
        return products

    def compare_prices(self, search_query):
        """Compare prices across all platforms"""
        logger.info(f"\n🔍 UNIVERSAL PRICE COMPARISON")
        logger.info(f"Searching for: '{search_query}'")
        logger.info("=" * 60)
        
        all_products = []
        self.create_driver()
        
        try:
            all_products += self.scrape_flipkart(search_query)
            all_products += self.scrape_amazon(search_query)
            all_products += self.scrape_vijay_sales(search_query)
            all_products += self.scrape_jiomart(search_query)
        finally:
            if self.driver:
                try:
                    logger.info("👋 Closing browser...")
                    self.driver.quit()
                except Exception:
                    pass
                time.sleep(0.5)
        
        # Filter valid products
        valid_products = [p for p in all_products if p['price_num'] is not None and p['price_num'] >= 10]
        valid_products.sort(key=lambda x: x['price_num'])
        
        logger.info(f"\n✅ Total products found: {len(valid_products)}")
        return valid_products


# Flask Application
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

@app.route('/')
def home():
    """Health check endpoint"""
    return jsonify({
        'status': 'success',
        'message': 'Price Comparison API is running',
        'version': '1.0.0'
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'Server is running'
    }), 200

@app.route('/api/search', methods=['POST'])
def search_products():
    """Search products across all platforms"""
    try:
        data = request.json
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({
                'error': 'Search query is required',
                'products': []
            }), 400
        
        logger.info(f"\n📡 API Request received for: {query}")
        
        scraper = UniversalEcommerceScraper()
        products = scraper.compare_prices(query)
        
        logger.info(f"✅ Returning {len(products)} products to frontend\n")
        
        return jsonify({
            'success': True,
            'query': query,
            'total_products': len(products),
            'products': products
        }), 200
    
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'products': []
        }), 500

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 PRICE COMPARISON API SERVER")
    print("="*60)
    print("📡 Server running on http://localhost:5000")
    print("🌐 Ready to receive search requests")
    print("📝 Endpoints:")
    print("   - GET  /               : Health check")
    print("   - GET  /api/health     : Health status")
    print("   - POST /api/search     : Search products")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)