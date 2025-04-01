import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient

# MongoDB bağlantısını ayarla
client = MongoClient("mongodb://localhost:27017/")
db = client["news_database"]  # Veritabanı adı
collection = db["hurriyet_news"]  # Koleksiyon adı

# URL of the page you want to scrape
url = "https://www.hurriyet.com.tr"

# Fetch the page content
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

# Find the carousel element
carousel = soup.find('div', class_='home-carousel')

if carousel:
    # Find all the slides within the carousel
    slides = carousel.find_all('div', class_='swiper-slide')

    # Loop through each slide and extract the data
    for slide in slides:
        try:
            raw_link = slide.find('a')['href']
            category = "Bilinmiyor"  # Varsayılan olarak tanımla

            # Linki tam hale getir
            if raw_link.startswith("/"):
                link = "https://www.hurriyet.com.tr" + raw_link
            elif raw_link.startswith("bigpara.hurriyet.com.tr"):
                link = "https://" + raw_link
                category = "bigpara"  # bigpara ile başlıyorsa kategori bigpara olsun
            else:
                link = raw_link

            # Kategori belirleme
            if "hurriyet.com.tr" in link:
                parts = link.split("/")
                if len(parts) > 3:
                    category = parts[3]  # İlk kelime kategoridir
                    # Eğer kategori "kelebek" ise, bir sonraki kısmı al
                    if category == "kelebek" and len(parts) > 4:
                        category = parts[4]
                else:
                    category = "haberler"  # Default kategori

            title = slide.find('div', class_='slide__title').text.strip()
            image_url = slide.find('img')['data-src']

            # Daha önce aynı link MongoDB'de var mı kontrol et
            if collection.find_one({"link": link}):
                print(f"Zaten mevcut: {title}")
                continue

            # Haber sayfasına giderek .readingTime içeriğini çek
            article_response = requests.get(link)
            article_soup = BeautifulSoup(article_response.text, 'html.parser')
            reading_time_element = article_soup.find(class_='readingTime')
            article_text = reading_time_element.text.strip() if reading_time_element else "Haber metni bulunamadı"
            article_text = article_text[14:]

            news_data = {
                "title": title,
                "link": link,
                "image_url": image_url,
                "category": category,
                "article_text": article_text  # Haberin içeriği
            }

            # Veriyi MongoDB'ye ekle
            collection.insert_one(news_data)
            print(f"Kaydedildi: {title} - Kategori: {category}\n Link: {link}\n")
        except Exception as e:
            print(f"Hata oluştu: {e}")
else:
    print("Carousel bulunamadı.")

client.close()
