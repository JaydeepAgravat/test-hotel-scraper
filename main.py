import time
import csv
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException

# Configure logging
logging.basicConfig(
    filename='hotel_scraper.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='w'
)


def get_url(destination, check_in_date, check_out_date, month_year, hotel_code):
    try:
        url = f'''https://www.ihg.com/hotels/gb/en/find-hotels/select-roomrate?qDest={destination}&qPt=CASH&qCiD={check_in_date}&qCoD={check_out_date}&qCiMy={month_year}&qCoMy={month_year}&qAdlt=1&qChld=0&qRms=1&qAAR=6CBARC&qSlH={
            hotel_code}&qAkamaiCC=IN&srb_u=1&qExpndSrch=false&qSrt=sAV&qBrs=6c.hi.ex.sb.ul.ic.cp.cw.in.vn.cv.rs.ki.ma.sp.va.re.vx.nd.sx.we.lx.rn.sn.nu&qWch=0&qSmP=0&qRad=30&qRdU=mi&setPMCookies=true&qpMbw=0&qErm=false&qpMn=0&qLoSe=false&qChAge=&qRmFltr='''
        logging.info(f"Generated URL: {url}")
        return url
    except Exception as e:
        logging.error(f"Error generating URL: {e}")
        raise


def get_driver(url):
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36")

        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        logging.info(f"WebDriver initialized and navigated to {url}")
        return driver
    except WebDriverException as e:
        logging.error(f"Error initializing WebDriver: {e}")
        raise


def get_data(driver, destination, check_in_date, check_out_date, month_year, hotel_code):
    room_data = []

    try:
        # Wait for the hotel name to be present
        hotel_name_element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "title-wrapper"))
        )
        hotel_name = hotel_name_element.text.split("\n")[-1]
        logging.info(f"Hotel name found: {hotel_name}")

        # Wait for the room names to be present
        room_name_elements = WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "roomName"))
        )
        room_names = [ele.text for ele in room_name_elements]
        logging.info(f"Room names found: {room_names}")

        # Wait for the room prices to be present
        room_price_elements = WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "cash"))
        )
        room_prices = [ele.text for ele in room_price_elements]
        logging.info(f"Room prices found: {room_prices}")

        for name, price in zip(room_names, room_prices):
            room_data.append({
                "destination": destination,
                "hotel name": hotel_name,
                "check in date": f"{check_in_date}/{int(month_year[:2])+1}/{month_year[2:]}",
                "check out date": f"{check_out_date}/{int(month_year[:2])+1}/{month_year[2:]}",
                "room name": name,
                "room price": price
            })

        logging.info(f"Room data collected for hotel code {
                     hotel_code}: {room_data}")

    except (NoSuchElementException, TimeoutException) as e:
        logging.error(f"Error getting data for hotel code {hotel_code}: {e}")
    except Exception as e:
        logging.error(f"Unexpected error for hotel code {hotel_code}: {e}")

    return room_data


def save_to_csv(data, filename):
    try:
        keys = data[0].keys()
        with open(filename, 'w', newline='') as output_file:
            dict_writer = csv.DictWriter(output_file, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(data)
        logging.info(f"Data saved to {filename}")
    except Exception as e:
        logging.error(f"Error saving data to CSV: {e}")
        raise


def main():
    destination = "Auburn, Alabama, United States"
    today_date = datetime.now()
    check_in_date = today_date.day
    check_out_date = check_in_date + 1
    month_year = f"{(today_date.month-1):02d}{today_date.year}"
    hotel_codes = ["AUOAU", "AUOAV", "AUOCS",
                   "AUOOP", "PXCAL", "CSGGO", "AUOCW"]
    all_room_data = []
    driver = None
    try:
        for hotel_code in hotel_codes:
            url = get_url(destination, check_in_date,
                          check_out_date, month_year, hotel_code)
            driver = get_driver(url)
            room_data = get_data(
                driver, destination, check_in_date, check_out_date, month_year, hotel_code)
            all_room_data.extend(room_data)
    except Exception as e:
        logging.error(f"Error in main execution loop: {e}")
    finally:
        if driver:
            driver.quit()
            logging.info("WebDriver closed")

    if all_room_data:
        csv_filename = "hotel_room_data.csv"
        save_to_csv(all_room_data, csv_filename)
    else:
        logging.warning("No data collected, CSV file not created")


if __name__ == "__main__":
    main()
