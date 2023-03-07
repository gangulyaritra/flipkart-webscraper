import sys
import requests
from bs4 import BeautifulSoup as bs
from src.entity import Product
from src.utils import read_config
from src.logging import CustomLogger
from src.exception import FlipkartCustomException

logger = CustomLogger("logic_layer_logs")
config = read_config()


class Scraper:
    def __init__(self, search_result):
        """
        :param search_result: Enter a product to scrap from Flipkart.
        """
        self.search_string = search_result
        self.reviews = []
        self.comment_boxes = None
        self.boxes = None
        self.result = None
        self.scraped_data = {}

    def __read_url(self, link):
        """
        :param link: Enter the URL to get data from the webpage.
        """
        self.result = requests.get(link)
        self.result.encoding = "utf-8"
        self.result = bs(self.result.text, "html.parser")
        return self.result

    def __flipkart_url(self):
        """
        It is an internal function used to get search results and store product card information
        in `self.boxes` which gets further used in the `getdata` method of the class.
        """
        flipkart_url = config["links"]["flipkart_url"] + self.search_string
        page = self.__read_url(flipkart_url)
        self.boxes = page.findAll("div", {"class": "_1YokD2 _3Mn1Gg"})

    @staticmethod
    def __get_name(data):
        """
        :param data: Get the product card and returns the name of the product.
        :return: Name str
        """
        try:
            name = data.div.div.find_all("p", {"class": "_2sc7ZR _2V5EHH"})[0].text
        except Exception as e:
            name = "Name Unavailable."

        return name

    @staticmethod
    def __get_rating(data):
        """
        :param data: Get the product card and returns the rating of the product.
        :return: rating str
        """
        try:
            rating = data.div.div.div.div.text
        except Exception as e:
            rating = "Rating Unavailable."

        return rating

    @staticmethod
    def __get_comment_head(data):
        """
        :param data: Get the product card and returns the comment_head of the product.
        :return: comment_head str
        """
        try:
            comment_head = data.div.div.div.p.text
        except Exception as e:
            comment_head = "Comment Heading Unavailable."

        return comment_head

    @staticmethod
    def __get_comment(data):
        """
        :param data: Get the product card and returns the comment on the product.
        :return: comment str
        """
        try:
            comment_tag = data.div.div.find_all("div", {"class": ""})
            comment = comment_tag[0].div.text
        except Exception as e:
            comment = "Comment Unavailable."

        return comment

    def get_data(self) -> Product:
        """
        This method makes use of the private methods to scrape data from Flipkart.
        :return: Retrieve Information for five products.
        """
        try:
            self.__flipkart_url()
            self.boxes[0].findAll("div", {"class": "_2kHMtA"})
            for box in self.boxes[0].findAll("div", {"class": "_2kHMtA"})[:5]:
                product_url = config["links"]["product_url"] + box.a["href"]
                page = self.__read_url(product_url)
                self.comment_boxes = page.find_all("div", {"class": "_16PBlm"})
                logger.info(f"Scrapping Data {self.search_string} from Flipkart.")

                Product_name = page.find_all("h1", {"class": "yhB1nd"})[
                    0
                ].span.get_text()

                for data in self.comment_boxes:
                    name = self.__get_name(data)
                    rating = self.__get_rating(data)
                    comment_head = self.__get_comment_head(data)
                    comment = self.__get_comment(data)

                    product = Product(
                        Product_name=self.search_string,
                        Name=name,
                        Rating=rating,
                        CommentHead=comment_head,
                        Comment=comment,
                    )._asdict()
                    self.reviews.append(product)

                self.scraped_data[Product_name] = self.reviews
                self.reviews = []
                logger.info(f"Scrapping Completed for {self.search_string}.")
            return [self.scraped_data]

        except Exception as e:
            message = FlipkartCustomException(e, sys)
            logger.error(message.error_message)
            raise message.error_message from e
