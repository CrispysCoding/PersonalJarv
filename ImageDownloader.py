import os
import time
import random
from bs4 import BeautifulSoup
from PIL import Image, ImageFilter
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests

def turn_off_safe_search(driver):
    try:
        # Open the Google search settings page
        driver.get("https://www.google.com/safesearch?utm_source=google&utm_medium=pref-page&hl=en&prev=https://www.google.com/preferences&safe=&authuser=0&hcb=0")

        # Wait for the SafeSearch dropdown to appear
        safe_search_dropdown = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".i9lrp"))
        )

        # Find the "Show most relevant results" option and click on it
        option_label = driver.find_element_by_css_selector(".j0Ppje")
        if option_label.text != "Show most relevant results":
            option_label.click()

        print("SafeSearch turned off successfully.")

    except Exception as e:
        print(f"Error turning off SafeSearch: {str(e)}")

def get_image(image_url, headers):
    try:
        response = requests.head(image_url, headers=headers)
        if response.status_code == 200:
            content_length = int(response.headers.get("content-length", 0))
            if content_length > 0:
                return True
    except Exception as e:
        pass
    return False

def search_large_images(query, num_jpg_media, num_gif_media, download_path):
    # Initialize the web driver with incognito mode
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--incognito")
    driver = webdriver.Chrome(options=chrome_options)

    # Turn off SafeSearch (optional, you can remove this if not needed)
    turn_off_safe_search(driver)

    # Define the URL of the Google Images search page with the "large" size filter and media type
    url = f"https://www.google.com/search?q={query}&tbm=isch&tbs=isz:l"

    # Set headers to mimic a real browser request
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }

    # Function to download and unblur media files
    def download_and_unblur_media(media_urls, num_media, file_extension):
        # Ensure the download directory exists
        if not os.path.exists(download_path):
            os.makedirs(download_path)

        # Shuffle the list of media URLs to get random images
        random.shuffle(media_urls)

        # Download and unblur the specified number of media files
        downloaded_count = 0
        for i, media_url in enumerate(media_urls):
            if downloaded_count >= num_media:
                break  # Stop downloading once the desired number is reached
            try:
                if get_image(media_url, headers) and i < num_media:  # Check image dimensions
                    # Send an HTTP GET request for each media URL
                    response = requests.get(media_url, headers=headers)
                    media_data = response.content

                    # Generate a unique filename for each media file
                    filename = f"{query}_{downloaded_count + 1}.{file_extension}"

                    # Specify the path to save the media file
                    media_path = os.path.join(download_path, filename)

                    # If the file already exists, increment the index
                    while os.path.exists(media_path):
                        downloaded_count += 1
                        filename = f"{query}_{downloaded_count + 1}.{file_extension}"
                        media_path = os.path.join(download_path, filename)

                    # Save the media file to the specified path
                    with open(media_path, "wb") as media_file:
                        media_file.write(media_data)

                    # Open the downloaded image using Pillow
                    image = Image.open(media_path)
                    # Apply unblurring filter (sharpening)
                    unblurred_image = image.filter(ImageFilter.SHARPEN)
                    # Save the unblurred image
                    unblurred_image.save(media_path)

                    print(f"Downloaded and unblurred {filename}")
                    downloaded_count += 1
            except Exception as e:
                print(f"Error downloading media {i + 1}: {str(e)}")

    try:
        # Open the Google Images search page
        driver.get(url)

        # Scroll to load more images
        num_scrolls = (num_jpg_media + num_gif_media) // 20  # Each scroll loads approximately 20 images
        for _ in range(num_scrolls):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # Give the page some time to load new images

        # Parse the page source with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Find all media tags (images and GIFs)
        media_tags = soup.find_all("img")

        # Extract media URLs and store them in a list, excluding palette images
        media_urls = [media["data-src"] for media in media_tags if "data-src" in media.attrs and "palette" not in media["data-src"]]

        # Download JPG images and GIFs and unblur them
        download_and_unblur_media(media_urls, num_jpg_media, "jpg")
        download_and_unblur_media(media_urls, num_gif_media, "gif")

    except Exception as e:
        print(f"Error: {str(e)}")

    finally:
        # Close the web driver
        driver.quit()

# Example usage
search_query = "Cursed Memes"
num_jpg_media_to_fetch = 500  # Set the number of JPG images you want to download
num_gif_media_to_fetch = 0  # Set the number of GIFs you want to download
download_directory = "downloaded_media"

search_large_images(search_query, num_jpg_media_to_fetch, num_gif_media_to_fetch, download_directory)
