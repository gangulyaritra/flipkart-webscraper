import os
import sys
import uvicorn
import pandas as pd
from fastapi import FastAPI, Form, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.responses import FileResponse
from src.scraper import Scraper
from src.exception import FlipkartCustomException
from src.data_access import Database
from src.logging import CustomLogger
from src.utils import plotly_wordcloud

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="css")
templates = Jinja2Templates(directory="templates")

os.makedirs("logs", exist_ok=True)
logger = CustomLogger("endpoint_logs")
database = Database()


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(name="index.html", context={"request": request})


@app.post("/results")
def results(request: Request, content: str = Form(...)):
    """
    This API gets search results from index.html and queries the database.
    If that collection is unavailable, it calls the Scraper class to scrape data from Flipkart.
    :return: Renders results.html
    """
    try:
        search_string = content.replace(" ", "_")
        logger.info(f"Searching Flipkart for {search_string}")
        reviews = database.get_collection(search_string)

        if not reviews.__len__() and search_string != "":
            scrap = Scraper(search_string)
            reviews = scrap.get_data()
            database.create_collection(search_string, reviews)

        return templates.TemplateResponse(
            name="results.html",
            context={
                "request": request,
                "reviews": reviews[0][list(reviews[0].keys())[1]],
                "list_of_products": list(reviews[0].keys())[1:],
                "search_string": search_string,
            },
        )

    except Exception as e:
        message = FlipkartCustomException(e, sys)
        logger.error(message.error_message)
        return templates.TemplateResponse(name="505.html", context={"request": request})


@app.get("/get_wordcloud")
def get_wordcloud(request: Request, search_string: str):
    """
    This API gets a search query from the user to find
    and load collection from the database to generate.
    :return: Renders wordcloud.html
    """
    try:
        reviews = database.get_collection(search_string)
        return templates.TemplateResponse(
            name="wordcloud.html",
            context={
                "request": request,
                "list_of_products": list(reviews[0].keys())[1:],
                "search_string": search_string,
            },
        )

    except Exception as e:
        message = FlipkartCustomException(e, sys)
        logger.error(message.error_message)
        return templates.TemplateResponse(name="505.html", context={"request": request})


@app.post("/post_wordcloud")
def post_wordcloud(
    request: Request, search_string: str = Form(...), product: str = Form(...)
):
    """
    This API gets a word cloud creation request from get API and acts to create test.html
    :return: Renders test.html, which includes plotly Word Cloud.
    """
    try:
        reviews = database.get_collection(search_string)
        result_fig = plotly_wordcloud(reviews[0][product.replace("_", " ")[:-1]])
        result_fig.write_html("templates/test.html")
        return templates.TemplateResponse(
            name="test.html", context={"request": request}
        )

    except Exception as e:
        message = FlipkartCustomException(e, sys)
        logger.error(message.error_message)
        return templates.TemplateResponse(name="505.html", context={"request": request})


@app.get("/get_download_csv")
def get_download_csv(request: Request, search_string: str):
    """
    This API provides users to select data to download in CSV format.
    :return: Renders download_data.html
    """
    try:
        reviews = database.get_collection(search_string)
        return templates.TemplateResponse(
            name="download_data.html",
            context={
                "request": request,
                "list_of_products": list(reviews[0].keys())[1:],
                "search_string": search_string,
            },
        )

    except Exception as e:
        message = FlipkartCustomException(e, sys)
        logger.error(message.error_message)
        return templates.TemplateResponse(name="505.html", context={"request": request})


@app.post("/post_download_csv")
def post_download_csv(
    request: Request, search_string: str = Form(...), product: str = Form(...)
):
    """
    This API downloads selected data into the user's local system.
    :return: Download data in CSV format.
    """
    try:
        reviews = database.get_collection(search_string)
        data = reviews[0][product.replace("_", " ")[:-1]]
        df = pd.DataFrame(data)
        df.to_csv("static/csv/data.csv", index=False)
        return FileResponse(path="static/csv/data.csv", filename="data.csv")

    except Exception as e:
        message = FlipkartCustomException(e, sys)
        logger.error(message.error_message)
        return templates.TemplateResponse(name="505.html", context={"request": request})


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
