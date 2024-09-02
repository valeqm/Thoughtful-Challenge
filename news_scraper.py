import os
import re
import time
import shutil
import pandas as pd
from datetime import datetime
from RPA.Browser.Selenium import Selenium


class NewsScraper:
    def __init__(self, search_phrase, category, months):
        self.search_phrase = search_phrase
        self.category = category
        self.months = max(1, int(months))
        self.excel_file = "output/data_news.xlsx"
        self.browser = Selenium()
        self.base_url = "https://www.aljazeera.com/"
        self.image_dir = os.path.join(os.getcwd(), "output/images")
        self._prepare_directories()

    def _prepare_directories(self):
        """Prepare the directories for images and clean up if necessary."""
        if os.path.exists(self.image_dir):
            shutil.rmtree(self.image_dir)
        os.makedirs(self.image_dir)

    def open_site(self):
        """Open the base website and accept cookies."""
        self.browser.open_available_browser(self.base_url)
        self.browser.wait_until_element_is_visible('//button[@id="onetrust-accept-btn-handler"]')
        self.browser.click_element('//button[@id="onetrust-accept-btn-handler"]')

    def search_news(self):
        """Search for news articles using the provided search phrase."""
        search_button_selector = '//div[@class="site-header__search-trigger"]/button'
        search_input_selector = '//div[@class="search-bar__input-container"]/input'
        search_text_selector = '//div[@class="search-bar__button"]/button'

        self.browser.click_button(search_button_selector)
        self.browser.input_text(search_input_selector, self.search_phrase)
        self.browser.click_button(search_text_selector)
        self.browser.wait_until_element_is_visible('//div[@class="search-result__list"]//h3[@class="gc__title"]', timeout=10)

    def select_order(self):
        """Select the "Date" option from the sorting dropdown."""
        self.browser.wait_until_element_is_visible('//button[@aria-label="Close Ad"]')
        time.sleep(2)
        self.browser.click_element('//button[@aria-label="Close Ad"]')
        order_button_select = '//div[@class="search-summary__select"]/select[@id="search-sort-option"]'
        self.browser.wait_until_element_is_visible(order_button_select, timeout=10)
        self.browser.select_from_list_by_value(order_button_select, "date")

    @staticmethod
    def clean_date_text(date_text):
        """Clean up the date text by removing unwanted prefixes."""
        date_text = date_text.replace("Last update ", "").replace("Published On ", "").strip()
        if "\n" in date_text:
            date_text = date_text.split("\n")[0]
        return date_text

    @staticmethod
    def parse_date(date_text):
        """Parse a date string into a datetime object."""
        try:
            return datetime.strptime(date_text, '%d %b %Y')
        except ValueError:
            print(f"Date format for '{date_text}' is not recognized.")
            return None

    def date_condition(self, dates, condition):
        """Filter dates based on a condition in months."""
        current_date = datetime.now()
        filtered_dates = [pub_date for pub_date in dates
                          if (current_date.year - pub_date.year) * 12 + (current_date.month - pub_date.month) <= condition]
        return filtered_dates

    def get_published_dates(self):
        """Get the publication dates for the articles."""
        self.browser.wait_until_element_is_visible('//div[@class="gc__date__date"]', timeout=10)
        date_selector = '//div[@class="gc__date__date"]'
        dates = self.browser.find_elements(date_selector)
        publication_dates = []

        for date in dates:
            date_text = self.clean_date_text(date.text.strip())
            pub_date = self.parse_date(date_text)
            if pub_date:
                publication_dates.append(pub_date)
        return publication_dates

    def titles_remove(self, titles):
        """Remove titles containing today's latest."""
        filter_var = "Today's latest"
        self.positions_to_remove = [i for i, title in enumerate(titles) if filter_var in title]

    def based_from_remove(self, list_items, positions):
        """Remove entries from a list based on specified positions."""
        return [element for i, element in enumerate(list_items) if i not in positions]

    def extract_titles(self):
        """Extract article links and titles from the search results."""
        self.browser.wait_until_element_is_visible('//h3[@class="gc__title"]', timeout=10)
        article_elements = self.browser.find_elements('//h3[@class="gc__title"]/a/span')
        return [elem.text for elem in article_elements]

    def get_descriptions(self):
        """Extract all article descriptions."""
        description_selector = '//div[@class="gc__excerpt"]/p'
        descriptions = self.browser.find_elements(description_selector)
        descriptions = self.based_from_remove(descriptions, self.positions_to_remove)
        description_texts = []

        for excerpt in descriptions:
            full_text = excerpt.text.strip()
            if '...' in full_text:
                parts = full_text.split('...', 1)
                if len(parts) > 1:
                    description_texts.append(parts[1].strip())
        return description_texts

    def download_images(self, count):
        """Download images associated with the articles."""
        images = self.browser.find_elements("//img[contains(@class, 'article-card__image')]")
        images = self.based_from_remove(images, self.positions_to_remove)
        image_paths = []

        for idx, img in enumerate(images[:count]):
            img_filename = f"Image_{idx + 1}.png"
            img_filepath = os.path.join(self.image_dir, img_filename)
            try:
                if idx == 0:
                    self.browser.execute_javascript("window.scrollTo(0, 0);")
                img.screenshot(img_filepath)
                image_paths.append(img_filepath)
            except Exception as e:
                print(f"Failed to capture image {idx + 1}: {e}")

        return image_paths

    def count_search_phrases(self, title, content):
        """Count occurrences of the search phrase in the title and content."""
        search_phrase_lower = self.search_phrase.lower()
        return title.lower().count(search_phrase_lower) + content.lower().count(search_phrase_lower)

    @staticmethod
    def contains_money(text):
        """Check if the text contains any monetary values."""
        money_patterns = [
            r'\$\d+(?:,\d{3})*(?:\.\d{2})?',  # $12.34 or $1,234.56
            r'\b\d+\s*(?:USD|dollars)\b',     # 12 USD or 12 dollars
        ]
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in money_patterns)

    def click_see_more(self):
        """Click the 'See More' button if available."""
        try:
            self.browser.click_element('//button[@data-testid="show-more-button"]')
            time.sleep(2)
            return True
        except Exception as e:
            print("No 'See More' button found or failed to click:", e)
            return False

    def scrape_articles(self):
        """Main method to scrape articles based on search phrase, category, and time frame."""
        all_dates_met_condition = True
        while all_dates_met_condition:
            time.sleep(2)
            publication_dates = self.get_published_dates()
            if any((datetime.now().year - pub_date.year) * 12 + (datetime.now().month - pub_date.month) > self.months
                   for pub_date in publication_dates):
                all_dates_met_condition = False
                break
            if not self.click_see_more():
                break

        publication_dates = self.get_published_dates()
        new_publication_dates = self.date_condition(publication_dates, self.months)
        titles = self.extract_titles()
        self.titles_remove(titles)
        titles = self.based_from_remove(titles, self.positions_to_remove)
        descriptions = self.get_descriptions()
        images = self.download_images(len(new_publication_dates))

        articles_data = []
        for title, description, pub_date, image in zip(titles, descriptions, new_publication_dates, images):
            search_phrase_count = self.count_search_phrases(title, description)
            money_in_article = self.contains_money(title) or self.contains_money(description)

            articles_data.append({
                'title': title,
                'date': pub_date.strftime('%B %d, %Y'),
                'description': description,
                'picture_filename': image,
                'search_phrase_count': search_phrase_count,
                'contains_money': money_in_article
            })

        df = pd.DataFrame(articles_data)
        df.to_excel(self.excel_file, index=False)
        return articles_data

    def run(self):
        """Run the entire scraping process."""
        self.open_site()
        self.search_news()
        self.select_order()
        return self.scrape_articles()


if __name__ == "__main__":
    search_phrase = "Technology"
    category = "Science"
    months = 1

    scraper = NewsScraper(search_phrase, category, months)
    data = scraper.run()
    print("Scraping complete. Data saved to:", scraper.excel_file)
