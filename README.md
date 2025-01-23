# **News Data Extraction Bot (RPA Challenge)**

## **Overview**
Our mission is to help companies automate tedious but critical business processes. This RPA challenge showcases your ability to build a bot for process automation. The goal is to automate the extraction of data from a news site and process it for storage.

## **The Challenge**
Your task is to automate the process of extracting data from a news website, including the title, date, description, and picture filename. The bot should:
- Search for a given phrase.
- Filter news by category, section, or topic.
- Extract the latest news within a specified time frame (by month).
- Store the extracted data in an Excel file.

## **Source**
The source website used for this challenge:
- [https://www.aljazeera.com/](https://www.aljazeera.com/)

## **Parameters**
The process must handle three parameters via Robocloud workitems:
- Search phrase
- News category/section/topic
- Number of months for which to receive news

Example:
- **0 or 1** - Only the current month
- **2** - Current and previous month
- **3** - Current and two previous months

## **Process Steps**
1. Open the news website using a given link.
2. Enter the search phrase in the search field.
3. If applicable, filter by news category/section.
4. Extract the latest news.
5. Store the following details in an Excel file:
   - Title
   - Date
   - Description (if available)
   - Picture filename
   - Count of search phrases in the title and description
   - True/False indicating if the title/description contains money-related amounts
6. Download the picture and specify the filename in the Excel file.

## **Instructions**
1. Push your code to a public GitHub repository.
2. Create a Robocorp Control Room process using your GitHub repo.
3. Ensure the process runs successfully and stores results in the `/output` directory.
