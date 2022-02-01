from bs4 import BeautifulSoup
from selenium import webdriver
from config import host, user, password, db_name
import psycopg2
import time
from multiprocessing import Pool
from fake_useragent import UserAgent

useragent = UserAgent()

options = webdriver.ChromeOptions()
options.headless = True
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument(f"user-agent={useragent.random}")
options.add_argument("--window-size=1920,1080")




def get_cats(retailer_url):
    retailer_name = retailer_url.rsplit("/")[-1]
    start_time = time.time()
    connection = psycopg2.connect(
        host=host,
        user=user,
        password=password,
        database=db_name
    )
    connection.autocommit = True

    driver = webdriver.Chrome(
        executable_path="/home/pazhiloy/PycharmProjects/edadil/chromedriver",
        options=options
    )

    driver.get(url=retailer_url)
    # time.sleep(1)
    # driver.refresh()
    time.sleep(2)

    try:

        source_page1 = driver.page_source
        time.sleep(2)

        soup = BeautifulSoup(source_page1, "lxml")

        urls = soup.find_all("a", class_="b-accordion__item1-title b-accordion__item1-title_selected_false b-accordion__item1-title_opened_false")

        all_cats_urls = []
        all_cats_filters = []

        for url in urls:

            url = "https://edadeal.ru" + url.get("href")
            all_cats_urls.append(url)
            cat_filter = url.split("=")[-1]
            all_cats_filters.append(cat_filter)

        # print(f"Все ссылки категорий: {all_cats_urls}")
    except Exception as ex:
        print(ex)

    if connection:
        connection.close()
    print("Сбор информации завершён успешно")
    print(f"Время потраченное на сбор информации для {retailer_name}: {time.time() - start_time}")

    driver.close()
    driver.quit()

    return all_cats_urls

def get_info(cat_url):

    start_time = time.time()
    connection = psycopg2.connect(
        host=host,
        user=user,
        password=password,
        database=db_name
    )
    connection.autocommit = True

    driver = webdriver.Chrome(
        executable_path="/home/pazhiloy/PycharmProjects/edadil/chromedriver",
        options=options
    )


    # driver.get(url=retailer_url)
    # # time.sleep(1)
    # # driver.refresh()
    # time.sleep(2)
    #
    # try:
    #
    #     source_page1 = driver.page_source
    #     time.sleep(2)
    #
    #     soup = BeautifulSoup(source_page1, "lxml")
    #
    #     urls = soup.find_all("a", class_="b-accordion__item1-title b-accordion__item1-title_selected_false b-accordion__item1-title_opened_false")
    #
    #     all_cats_filters = []
    #     all_cats_urls = []
    #
    #     for url in urls:
    #
    #         url = "https://edadeal.ru" + url.get("href")
    #         all_cats_urls.append(url)
    #         cat_filter = url.split("=")[-1]
    #         all_cats_filters.append(cat_filter)
    #
    # print(f"Все ссылки категорий: {all_cats_urls}")

    # for cat_url in all_cats_urls:

    retailer_name = cat_url.rsplit("/")[-1].rsplit("?")[0]
    cat_filter = cat_url.split("=")[-1]
    driver.get(url=cat_url)
    time.sleep(3)

    source_page2 = driver.page_source
    soup = BeautifulSoup(source_page2, "lxml")

    subcat_urls = soup.find_all("a", class_="b-accordion__item2-title")
    try:
        cat_text = soup.find("div", class_="b-accordion__item1-title_opened_true").text
    except Exception as ex:
        cat_text = None
        print(ex)



    with connection.cursor() as cursor:
        cursor.execute(f"SELECT category_name FROM categories WHERE category_name = '{cat_filter}'")
        data = cursor.fetchone()
        if data is None:

            with connection.cursor() as cursor:
                cursor.execute(
                    f"INSERT INTO categories (category_name, cat_text) VALUES ('{cat_filter}', '{cat_text}');"
                )
            # print('[INFO] Категория была внесена')

        else:
            print('[INFO] Такая категория уже есть')


    all_subcats_urls = []
    all_subcats_filters = []

    for subcat_url in subcat_urls:

        subcat_url = "https://edadeal.ru" + subcat_url.get("href")
        # print(subcat_url)
        all_subcats_urls.append(subcat_url)
        subcat_filter = subcat_url.split("=")[-1]
        all_subcats_filters.append(subcat_filter)

    for subcat_url in all_subcats_urls:

        sub_filter = subcat_url.split("=")[-1]
        driver.get(url=subcat_url)
        time.sleep(3)

        source_page3 = driver.page_source
        soup = BeautifulSoup(source_page3, "lxml")

        try:
            sub_text = soup.find("div", class_="b-accordion__item2-title_disabled_false").text
        except Exception as ex:
            sub_text = None
            print(ex)

        try:
            pages_count = int(soup.find_all("div", class_="b-button__content")[-2].text)
        except Exception:
            pages_count = 1

        with connection.cursor() as cursor:
            cursor.execute(f"SELECT subcat_name FROM subcats WHERE subcat_name = '{sub_filter}'")
            data = cursor.fetchone()
            if data is None:

                with connection.cursor() as cursor:
                    cursor.execute(
                        f"INSERT INTO subcats (subcat_name, sub_text) VALUES ('{sub_filter}', '{sub_text}');"
                    )
                # print('[INFO] Подкатегория была внесена')
            else:
                print('[INFO] Такая подкатегория уже есть')



            with connection.cursor() as cursor:
                cursor.execute(
                    f"INSERT INTO retailers_cats_subcats (retailer_name, cat_name, subcat_name) VALUES ('{retailer_name}', '{cat_text}', '{sub_text}');"
                )

            # print(sub_category)
            # print('[INFO] Подкатегория была внесена')


        for i in range(1, pages_count + 1):
            try:
                driver.get(
                    url=f"https://edadeal.ru/sankt-peterburg/retailers/{retailer_name}?page={i}&segment={sub_filter}")
                time.sleep(3)

                source_page4 = driver.page_source
                soup = BeautifulSoup(source_page4, "lxml")

                if driver.find_elements_by_xpath("//*[text() = 'Да. Мне есть 18']"):
                    driver.find_element_by_xpath("//*[text() = 'Да. Мне есть 18']").click()
                    time.sleep(3)
                else:
                    time.sleep(3)

                items_cards = soup.find("div", class_="p-retailer__offers").find_all("a")

                for item in items_cards:
                    product_name = item.find("div", class_="b-offer__description").get_text().replace(u'\xa0', u' ').replace("'", "")
                    product_url = "https://edadeal.ru" + item.get("href")
                    new_price = item.find("div", class_="b-offer__prices").find("div", class_="b-offer__price-new").text
                    try:
                        old_price = item.find("div", class_="b-offer__prices").find("div", class_="b-offer__price-old").get_text()
                    except Exception as ex:
                        old_price = new_price
                    sale = item.find("div", class_="b-offer__offer-info").get_text().replace(u'\xa0', u' ')

                    with connection.cursor() as cursor:
                        cursor.execute(f"SELECT product_url FROM products WHERE product_url = '{product_url}'")
                        data = cursor.fetchone()
                        if data is None:
                            # Вносим данные в таблицу

                            with connection.cursor() as cursor:
                                cursor.execute(
                                    f"INSERT INTO Products (product_name, new_price, old_price, sale, product_url, fk_subcat, fk_retailer) VALUES ('{product_name}', '{new_price}', '{old_price}', '{sale}', '{product_url}', '{sub_text}', '{retailer_name}');"
                                )

                                # print('[INFO] Данные продукта были внесены')
                        else:
                            print('[INFO] Такие продукты уже есть')

            except Exception as ex:
                print("Упс...", ex)
    # except Exception as ex:
    #     print("Упс...", ex)

    if connection:
        connection.close()
    print("Сбор информации завершён успешно")
    try:
        print(f"Потраченное время для {retailer_name}: {cat_filter} : {time.time() - start_time}")
    except Exception:
        pass

    driver.close()
    driver.quit()

if __name__ == '__main__':

    # all_retailer_urls = ["https://edadeal.ru/sankt-peterburg/retailers/perekrestok",
    #                      "https://edadeal.ru/sankt-peterburg/retailers/lenta-giper",
    #                      "https://edadeal.ru/sankt-peterburg/retailers/okmarket-giper"]
    #

    all_retailer_urls = ["https://edadeal.ru/sankt-peterburg/retailers/okmarket-giper"]

    pool = Pool(processes=3)
    all_cats_urls = pool.map(get_cats, all_retailer_urls)
    pool.close()
    pool.join()

    for retailer_cats_urls in all_cats_urls:

        pool3 = Pool(processes=6)
        pool3.map(get_info, retailer_cats_urls)

        pool3.close()
        pool3.join()